"""
FinAgent — RAG Embedder
Sentence-transformer embeddings for Chroma vector store.
Falls back to TF-IDF if sentence-transformers is unavailable.
"""
import os
import numpy as np
from typing import List, Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 80MB, fast, good quality


class EmbeddingEngine:
    """
    Provides text embedding + Chroma collection management.
    Uses sentence-transformers for high-quality embeddings.
    """

    def __init__(self, collection_name: str = "finagent_kb"):
        self.collection_name = collection_name
        self._model: Optional[SentenceTransformer] = None
        self._client = None
        self._collection = None
        self._init()

    def _init(self):
        """Initialize Chroma client and embedding model."""
        if HAS_CHROMA:
            self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(EMBEDDING_MODEL)
            except Exception as e:
                print(f"[Embedder] Warning: Could not load SentenceTransformer: {e}")
                self._model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts. Returns list of embedding vectors."""
        if self._model is not None:
            return self._model.encode(texts, normalize_embeddings=True).tolist()
        else:
            # TF-IDF fallback: sklearn-based sparse embedding → dense
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            import scipy.sparse as sp

            if not hasattr(self, "_tfidf"):
                self._tfidf = TfidfVectorizer(max_features=512)
                self._svd = TruncatedSVD(n_components=64, random_state=42)
                combined = self._tfidf.fit_transform(texts)
                self._svd.fit(combined)

            X = self._tfidf.transform(texts)
            return self._svd.transform(X).tolist()

    def get_or_create_collection(self, name: Optional[str] = None):
        """Get or create a Chroma collection."""
        col_name = name or self.collection_name
        if self._client is None:
            return None
        try:
            return self._client.get_or_create_collection(
                name=col_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"[Embedder] Chroma error: {e}")
            return None

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        va = np.array(a)
        vb = np.array(b)
        norm_a = np.linalg.norm(va)
        norm_b = np.linalg.norm(vb)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(va, vb) / (norm_a * norm_b))


# Singleton
_engine: Optional[EmbeddingEngine] = None


def get_embedding_engine() -> EmbeddingEngine:
    global _engine
    if _engine is None:
        _engine = EmbeddingEngine()
    return _engine
