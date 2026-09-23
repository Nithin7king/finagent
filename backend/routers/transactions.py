"""
FinAgent — Transactions Router
CRUD operations, CSV upload with auto-categorization, and ML pipeline.
"""
import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user
from backend import models, schemas
from backend.encryption import encrypt, decrypt
from backend.ml.categorizer import get_categorizer
from backend.ml.anomaly_detector import get_detector

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _transaction_to_schema(t: models.Transaction) -> schemas.TransactionOut:
    return schemas.TransactionOut(
        id=t.id,
        date=t.date,
        description=t.description,
        amount=t.amount,
        category=t.category or t.ml_category or "Other",
        ml_category=t.ml_category,
        ml_confidence=t.ml_confidence,
        anomaly_score=t.anomaly_score,
        anomaly_label=t.anomaly_label,
        anomaly_explanation=t.anomaly_explanation,
        is_subscription=t.is_subscription,
        subscription_interval_days=t.subscription_interval_days,
        source=t.source,
        created_at=t.created_at,
    )


@router.get("", response_model=schemas.TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    days: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    anomaly_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List transactions with pagination and filtering."""
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    if days:
        cutoff = datetime.now() - timedelta(days=days)
        query = query.filter(models.Transaction.date >= cutoff)

    if category:
        query = query.filter(models.Transaction.category == category)

    if anomaly_only:
        query = query.filter(models.Transaction.anomaly_label == True)

    total = query.count()
    transactions = (
        query.order_by(models.Transaction.date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return schemas.TransactionListResponse(
        total=total,
        transactions=[_transaction_to_schema(t) for t in transactions],
    )


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(
    data: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a single transaction with automatic categorization."""
    categorizer = get_categorizer()
    ml_cat, ml_conf = categorizer.predict(data.description, data.amount)

    transaction = models.Transaction(
        user_id=current_user.id,
        date=data.date,
        description=data.description,
        amount=data.amount,
        category=data.category or ml_cat,
        ml_category=ml_cat,
        ml_confidence=ml_conf,
        encrypted_notes=encrypt(data.notes) if data.notes else None,
        source="manual",
    )

    # Run anomaly detection if we have history
    detector = get_detector()
    if detector.model is not None:
        score, severity, explanation = detector.score_transaction(
            amount=data.amount,
            date=data.date,
            category=transaction.category,
            description=data.description,
        )
        transaction.anomaly_score = score
        transaction.anomaly_label = severity in ("medium", "high")
        transaction.anomaly_explanation = explanation if transaction.anomaly_label else None

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return _transaction_to_schema(transaction)


@router.put("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int,
    data: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a transaction (e.g., correct category)."""
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()

    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if data.category is not None:
        t.category = data.category
    if data.description is not None:
        t.description = data.description
    if data.notes is not None:
        t.encrypted_notes = encrypt(data.notes)

    db.commit()
    db.refresh(t)
    return _transaction_to_schema(t)


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a transaction."""
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == current_user.id,
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(t)
    db.commit()


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a CSV file with transactions. Auto-categorizes all entries.
    Expected CSV columns: date, description, amount (and optional: category)
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # Normalize column names
    headers = [h.lower().strip() for h in reader.fieldnames or []]
    if "date" not in headers or "amount" not in headers:
        raise HTTPException(
            status_code=400,
            detail="CSV must have 'date' and 'amount' columns",
        )

    categorizer = get_categorizer()
    detector = get_detector()
    created = []
    errors = []

    for i, row in enumerate(rows):
        try:
            # Parse date
            date_str = row.get("date", "").strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y"):
                try:
                    date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                errors.append(f"Row {i+2}: Cannot parse date '{date_str}'")
                continue

            # Parse amount
            amount_str = row.get("amount", "0").strip().replace(",", "").replace("₹", "")
            amount = float(amount_str)

            description = row.get("description", row.get("narration", row.get("merchant", "Unknown"))).strip()

            # ML categorization
            ml_cat, ml_conf = categorizer.predict(description, amount)
            user_cat = row.get("category", "").strip() or ml_cat

            t = models.Transaction(
                user_id=current_user.id,
                date=date,
                description=description,
                amount=amount,
                category=user_cat,
                ml_category=ml_cat,
                ml_confidence=ml_conf,
                source="csv",
            )

            # Anomaly detection
            if detector.model is not None and amount < 0:
                score, severity, explanation = detector.score_transaction(
                    amount=amount, date=date, category=user_cat, description=description,
                )
                t.anomaly_score = score
                t.anomaly_label = severity in ("medium", "high")
                t.anomaly_explanation = explanation if t.anomaly_label else None

            db.add(t)
            created.append(description)

        except Exception as e:
            errors.append(f"Row {i+2}: {str(e)}")

    db.commit()

    return {
        "created": len(created),
        "errors": len(errors),
        "error_details": errors[:10],  # Show first 10 errors
        "message": f"Successfully imported {len(created)} transactions.",
    }


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload an Indian bank statement PDF (SBI, HDFC, ICICI, Axis, Kotak, etc.).
    Extracts transactions across 3 tiers (direct table -> LLM -> OCR),
    with transparent password decryption for protected statements.
    """
    if not (file.filename.lower().endswith(".pdf") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF bank statement")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty")

    from backend.pdf_statement_parser import parse_statement_pdf
    from backend.rag.engine import _call_llm

    result = parse_statement_pdf(
        content,
        password=password,
        llm_generate_fn=lambda prompt, **kw: _call_llm(prompt)
    )

    if result.get("requires_password"):
        return {
            "requires_password": True,
            "tier_used": None,
            "message": "This bank statement is password-protected. Please enter your PDF password.",
            "transactions": [],
            "warnings": result.get("warnings", []),
        }

    raw_txns = result.get("transactions", [])
    if not raw_txns:
        warnings_msg = " ".join(result.get("warnings", []))
        raise HTTPException(
            status_code=422,
            detail=f"No transactions could be extracted from this PDF. {warnings_msg}"
        )

    categorizer = get_categorizer()
    detector = get_detector()
    preview_txns = []

    for idx, tx in enumerate(raw_txns):
        debit = tx.get("debit")
        credit = tx.get("credit")
        if debit is not None and debit > 0:
            amount = -abs(float(debit))
        elif credit is not None and credit > 0:
            amount = abs(float(credit))
        else:
            amount = 0.0

        desc = str(tx.get("description") or "Bank Transaction").strip()
        date_raw = str(tx.get("date") or "").strip()

        # Normalize date to YYYY-MM-DD
        formatted_date = datetime.now().strftime("%Y-%m-%d")
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y", "%d-%b-%Y"):
            try:
                formatted_date = datetime.strptime(date_raw, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue

        # ML categorization
        ml_cat, ml_conf = categorizer.predict(desc, amount)

        # Anomaly scoring
        is_anomaly = False
        anomaly_score = 0.0
        if detector.model is not None and amount < 0:
            try:
                parsed_dt = datetime.strptime(formatted_date, "%Y-%m-%d")
                score, severity, explanation = detector.score_transaction(
                    amount=amount, date=parsed_dt, category=ml_cat, description=desc
                )
                is_anomaly = severity in ("medium", "high")
                anomaly_score = score
            except Exception:
                pass

        preview_txns.append({
            "id": f"pdf-{idx}-{int(datetime.now().timestamp())}",
            "date": formatted_date,
            "description": desc,
            "amount": amount,
            "category": ml_cat or "Other",
            "status": "AI-assigned",
            "isAnomaly": is_anomaly,
            "anomalyScore": anomaly_score,
            "balanceAfter": tx.get("balance") or 0.0,
            "source": "pdf",
        })

    return {
        "requires_password": False,
        "tier_used": result.get("tier_used"),
        "tier_name": result.get("tier_name"),
        "warnings": result.get("warnings", []),
        "transactions": preview_txns,
        "count": len(preview_txns),
    }


@router.get("/export")
def export_transactions_csv(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Export all transactions as a CSV file download."""
    from fastapi.responses import StreamingResponse

    cutoff = datetime.now() - timedelta(days=days)
    txns = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.date >= cutoff,
        )
        .order_by(models.Transaction.date.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Amount", "Category", "ML Category", "Anomaly", "Anomaly Score", "Is Subscription", "Source"])
    for t in txns:
        writer.writerow([
            t.date.strftime("%Y-%m-%d"),
            t.description,
            t.amount,
            t.category or "Other",
            t.ml_category or "",
            "Yes" if t.anomaly_label else "No",
            round(t.anomaly_score or 0, 3),
            "Yes" if t.is_subscription else "No",
            t.source or "manual",
        ])

    output.seek(0)
    filename = f"finagent_transactions_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

