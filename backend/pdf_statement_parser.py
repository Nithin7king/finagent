"""
pdf_statement_parser.py

Tiered, fully open-source parser for Indian bank statement PDFs, to sit
alongside (not replace) the existing CSV upload path in MYFI.AI.

Why this exists:
Most Indian banks either don't offer CSV at all via net banking (SBI),
or only offer it through one specific channel (HDFC: app only, not net
banking; ICICI: net banking only, not the app). PDF is the one format
every bank, every channel, reliably supports. This module extracts
transactions from that PDF instead of requiring the user to already
have a CSV.

Three tiers, each only invoked if the previous one fails:
  1. Direct table extraction via pdfplumber (handles the common case:
     digitally-generated statements with real embedded text)
  2. LLM-assisted structured extraction via the existing Ollama/LLM
     integration (handles irregular layouts that don't extract as a
     clean table)
  3. OCR via pytesseract (handles scanned/image-based PDFs where tier 1
     extracts near-zero real text)

Dependencies (all open source):
  pip install pdfplumber pikepdf pytesseract pdf2image
  Tesseract OCR binary must also be installed separately for tier 3
  (apt install tesseract-ocr on Debian/Ubuntu or Windows Tesseract-OCR installer)
"""

import io
import json
import re
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pikepdf
except ImportError:
    pikepdf = None


@dataclass
class ParsedTransaction:
    date: str
    description: str
    debit: Optional[float]
    credit: Optional[float]
    balance: Optional[float]


# Column-name variants seen across major Indian banks, mapped to a
# canonical field. Extend this as new bank formats are encountered.
COLUMN_ALIASES = {
    "date": ["date", "value date", "txn date", "transaction date", "posting date"],
    "description": ["narration", "description", "particulars", "transaction remarks", "details", "remarks"],
    "debit": ["debit", "withdrawal", "withdrawal amt", "debit amount", "dr", "dr amount"],
    "credit": ["credit", "deposit", "deposit amt", "credit amount", "cr", "cr amount"],
    "balance": ["balance", "closing balance", "available balance", "running balance"],
}


def _decrypt_if_needed(file_bytes: bytes, password: Optional[str]) -> bytes:
    """Tier 0: transparently decrypt a password-protected statement PDF
    before any extraction is attempted. Most Indian banks email
    statements with a password (commonly PAN + DOB or account-number
    based), so this has to run first, not as an afterthought."""
    if pikepdf is None:
        return file_bytes
    try:
        with pikepdf.open(io.BytesIO(file_bytes), password=password or "") as pdf:
            out = io.BytesIO()
            pdf.save(out)
            return out.getvalue()
    except pikepdf.PasswordError:
        raise ValueError("PDF is password-protected; correct statement password required.")
    except Exception:
        # Not actually encrypted / not a pikepdf-recognized issue - fall
        # through and let pdfplumber try the original bytes as-is.
        return file_bytes


def _normalize_header(cell: str) -> Optional[str]:
    if not cell:
        return None
    cell_l = str(cell).strip().lower()
    for canonical, aliases in COLUMN_ALIASES.items():
        if any(alias in cell_l for alias in aliases):
            return canonical
    return None


def _parse_amount(cell: Any) -> Optional[float]:
    if cell is None:
        return None
    cell_str = str(cell).strip()
    if not cell_str:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", cell_str.replace(",", ""))
    if cleaned in ("", "-", ".", "--", "nil"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _tier1_table_extraction(file_bytes: bytes) -> List[ParsedTransaction]:
    """Direct table extraction. Returns [] if nothing usable is found,
    signalling the caller to fall through to tier 2."""
    if pdfplumber is None:
        return []

    results: List[ParsedTransaction] = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    header_row = table[0]
                    col_map = {}
                    for idx, cell in enumerate(header_row):
                        canonical = _normalize_header(cell or "")
                        if canonical:
                            col_map[canonical] = idx

                    # Need at minimum a date and a description-equivalent
                    # column to trust this table as a transaction table
                    # (this also correctly skips unrelated tables, e.g. a
                    # summary box, that happen to appear on the same page).
                    if "date" not in col_map or "description" not in col_map:
                        continue

                    for row in table[1:]:
                        if row is None or len(row) <= max(col_map.values()):
                            continue
                        date_val = str(row[col_map["date"]] or "").strip()
                        if not re.search(r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", date_val) and not re.search(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}", date_val):
                            continue  # skip footer/subtotal rows without a real date

                        results.append(ParsedTransaction(
                            date=date_val,
                            description=str(row[col_map["description"]] or "").strip().replace("\n", " "),
                            debit=_parse_amount(row[col_map["debit"]]) if "debit" in col_map else None,
                            credit=_parse_amount(row[col_map["credit"]]) if "credit" in col_map else None,
                            balance=_parse_amount(row[col_map["balance"]]) if "balance" in col_map else None,
                        ))
    except Exception as e:
        print(f"[PDFParser] Tier 1 extraction notice: {e}")

    return results


def _tier2_llm_extraction(file_bytes: bytes, llm_generate_fn) -> List[ParsedTransaction]:
    """LLM-assisted fallback for irregular layouts. llm_generate_fn is
    injected (rather than imported directly) so this module has no
    hard dependency on backend.agent.llm_provider - pass it in from
    the caller."""
    if pdfplumber is None or llm_generate_fn is None:
        return []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages[:5])
    except Exception:
        return []

    if len(raw_text.strip()) < 50:
        return []  # essentially no real text - this is likely a scanned PDF, go to tier 3

    prompt = f"""Extract every transaction from this bank statement text as a
JSON array. Each element must have exactly these fields: date, description,
debit (number or null), credit (number or null), balance (number or null).
Return ONLY the JSON array, no other text or markdown codeblocks.

STATEMENT TEXT:
{raw_text[:7500]}
"""
    try:
        response = llm_generate_fn(prompt, temperature=0.0)
        cleaned = re.sub(r"^```(?:json)?|```$", "", response.strip(), flags=re.MULTILINE).strip()
        rows = json.loads(cleaned)
        return [
            ParsedTransaction(
                date=str(row.get("date", "")).strip(),
                description=str(row.get("description", "")).strip(),
                debit=_parse_amount(row.get("debit")),
                credit=_parse_amount(row.get("credit")),
                balance=_parse_amount(row.get("balance")),
            ) for row in rows if row.get("date")
        ]
    except Exception as e:
        print(f"[PDFParser] Tier 2 LLM extraction notice: {e}")
        return []


def _tier3_ocr_extraction(file_bytes: bytes, llm_generate_fn) -> List[ParsedTransaction]:
    """OCR fallback for scanned/image-based statement PDFs."""
    if llm_generate_fn is None:
        return []

    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(file_bytes, first_page=1, last_page=3)
        ocr_text = "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception as ocr_err:
        print(f"[PDFParser] Tier 3 OCR dependency notice: {ocr_err}")
        return []

    if len(ocr_text.strip()) < 50:
        return []  # even OCR found nothing usable

    prompt = f"""This text was OCR-extracted from a scanned bank statement and
may contain errors. Extract every transaction you can confidently identify as
a JSON array with fields: date, description, debit (number or null), credit
(number or null), balance (number or null). Return ONLY the JSON array.

OCR TEXT:
{ocr_text[:7500]}
"""
    try:
        response = llm_generate_fn(prompt, temperature=0.0)
        cleaned = re.sub(r"^```(?:json)?|```$", "", response.strip(), flags=re.MULTILINE).strip()
        rows = json.loads(cleaned)
        return [
            ParsedTransaction(
                date=str(row.get("date", "")).strip(),
                description=str(row.get("description", "")).strip(),
                debit=_parse_amount(row.get("debit")),
                credit=_parse_amount(row.get("credit")),
                balance=_parse_amount(row.get("balance")),
            ) for row in rows if row.get("date")
        ]
    except Exception as e:
        print(f"[PDFParser] Tier 3 extraction error: {e}")
        return []


def parse_statement_pdf(
    file_bytes: bytes,
    password: Optional[str] = None,
    llm_generate_fn=None
) -> Dict[str, Any]:
    """Main entry point. Returns a dict with 'transactions', 'tier_used',
    and 'warnings' so the caller/UI can tell the user how the data was
    extracted and how much to trust it.
    """
    warnings = []

    # Check for library readiness
    if pdfplumber is None:
        return {
            "transactions": [],
            "tier_used": None,
            "warnings": ["pdfplumber library not installed. Please run: pip install pdfplumber pikepdf"],
        }

    try:
        decrypted_bytes = _decrypt_if_needed(file_bytes, password)
    except ValueError as ve:
        return {
            "transactions": [],
            "tier_used": None,
            "requires_password": True,
            "warnings": [str(ve)],
        }

    # Tier 1: Direct table extraction
    txns = _tier1_table_extraction(decrypted_bytes)
    if txns:
        return {
            "transactions": [asdict(t) for t in txns],
            "tier_used": 1,
            "tier_name": "Direct Table Extraction",
            "warnings": warnings,
        }

    warnings.append("Table extraction did not find structured tabular data; falling back to LLM-assisted extraction.")
    if llm_generate_fn is not None:
        txns = _tier2_llm_extraction(decrypted_bytes, llm_generate_fn)
        if txns:
            return {
                "transactions": [asdict(t) for t in txns],
                "tier_used": 2,
                "tier_name": "LLM-Assisted Extraction",
                "warnings": warnings,
            }

    warnings.append("Text extraction failed; falling back to OCR (for scanned/image-based statements).")
    if llm_generate_fn is not None:
        txns = _tier3_ocr_extraction(decrypted_bytes, llm_generate_fn)
        if txns:
            return {
                "transactions": [asdict(t) for t in txns],
                "tier_used": 3,
                "tier_name": "OCR Scanned Extraction",
                "warnings": warnings,
            }

    return {
        "transactions": [],
        "tier_used": None,
        "warnings": warnings + ["All extraction tiers failed. Please ensure the PDF contains transaction entries or try uploading CSV."],
    }
