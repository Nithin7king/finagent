"""
FinAgent — Knowledge Base Loader
Loads text documents from knowledge_base/ into Chroma.
Splits documents into chunks and embeds them.
"""
import os
import uuid
from typing import List, Tuple, Optional
from backend.rag.embedder import get_embedding_engine

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
KB_COLLECTION = "finagent_kb"
CHUNK_SIZE = 400    # characters per chunk
CHUNK_OVERLAP = 80  # overlap between chunks


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.
    Tries to split at paragraph boundaries first.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current = current + "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)
                # Overlap: take last `overlap` chars as start of next chunk
                overlap_text = current[-overlap:] if len(current) > overlap else current
                current = overlap_text + "\n\n" + para
            else:
                # Single paragraph exceeds chunk_size — split by sentence
                sentences = para.split(". ")
                for sent in sentences:
                    if len(current) + len(sent) <= chunk_size:
                        current = current + ". " + sent if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent

    if current:
        chunks.append(current)

    return [c.strip() for c in chunks if c.strip()]


def load_knowledge_base(force_reload: bool = False) -> int:
    """
    Load all .txt files from knowledge_base/ into Chroma.

    Args:
        force_reload: If True, clear existing collection and reload

    Returns:
        Number of chunks loaded
    """
    engine = get_embedding_engine()
    collection = engine.get_or_create_collection(KB_COLLECTION)

    if collection is None:
        print("[KnowledgeLoader] Chroma not available — skipping KB load")
        return 0

    # Check if already loaded
    if not force_reload:
        existing = collection.count()
        if existing > 0:
            print(f"[KnowledgeLoader] Knowledge base already loaded ({existing} chunks). Skipping.")
            return existing

    if force_reload:
        try:
            engine._client.delete_collection(KB_COLLECTION)
            collection = engine.get_or_create_collection(KB_COLLECTION)
        except Exception:
            pass

    if not os.path.exists(KB_DIR):
        print(f"[KnowledgeLoader] Knowledge base directory not found: {KB_DIR}")
        return 0

    total_chunks = 0
    for filename in os.listdir(KB_DIR):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(KB_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        source_name = filename.replace(".txt", "").replace("_", " ").title()
        chunks = _chunk_text(text)

        if not chunks:
            continue

        # Embed chunks
        embeddings = engine.embed(chunks)

        # Add to Chroma
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": source_name, "filename": filename} for _ in chunks]

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )
            total_chunks += len(chunks)
            print(f"[KnowledgeLoader] Loaded '{source_name}': {len(chunks)} chunks")
        except Exception as e:
            print(f"[KnowledgeLoader] Error loading {filename}: {e}")

    print(f"[KnowledgeLoader] Total: {total_chunks} chunks in knowledge base")
    return total_chunks


def retrieve(query: str, n_results: int = 4) -> List[Tuple[str, str, float]]:
    """
    Retrieve relevant chunks for a query.

    Returns:
        List of (chunk_text, source_name, relevance_score) tuples
    """
    engine = get_embedding_engine()
    collection = engine.get_or_create_collection(KB_COLLECTION)

    if collection is None or collection.count() == 0:
        return []

    query_embedding = engine.embed([query])[0]

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        chunks = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        # Convert Chroma distance (L2 cosine) → similarity score
        similarities = [max(0, 1 - d) for d in distances]

        return [(chunk, meta["source"], sim)
                for chunk, meta, sim in zip(chunks, metas, similarities)]
    except Exception as e:
        print(f"[KnowledgeLoader] Retrieval error: {e}")
        return []
