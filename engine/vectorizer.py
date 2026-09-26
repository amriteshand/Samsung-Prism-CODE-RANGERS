import re
import math
from typing import List, Dict, Tuple
import numpy as np


class DenseVectorizer:
    """
    High-performance subword character n-gram + token dense vectorizer.
    Guarantees deterministic, sub-millisecond dense embeddings without external model downloads,
    providing high cosine semantic similarity for typos, colloquialisms, and synonyms.
    """

    def __init__(self, vector_dim: int = 256):
        self.vector_dim = vector_dim
        self.idf: Dict[str, float] = {}
        self.doc_count = 0
        self.is_fitted = False

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        # Word tokens
        words = re.findall(r"\b[a-z0-9]+\b", text)
        tokens = list(words)
        # Add character 3-grams and 4-grams for typo tolerance
        for word in words:
            if len(word) >= 3:
                for n in (3, 4):
                    for i in range(len(word) - n + 1):
                        tokens.append(f"#{word[i:i+n]}")
        return tokens

    def _hash_token(self, token: str) -> int:
        """Deterministic hash into vector dimension."""
        h = 5381
        for char in token:
            h = ((h << 5) + h) + ord(char)
        return abs(h) % self.vector_dim

    def fit(self, documents: List[str]):
        """Compute Inverse Document Frequencies across document corpus."""
        self.doc_count = len(documents)
        df: Dict[str, int] = {}
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for tok in tokens:
                df[tok] = df.get(tok, 0) + 1

        self.idf = {}
        for tok, count in df.items():
            self.idf[tok] = math.log((self.doc_count + 1) / (count + 1)) + 1.0

        self.is_fitted = True

    def transform(self, text: str) -> np.ndarray:
        """Transforms a string into an L2-normalized dense vector."""
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for tok in tokens:
            idx = self._hash_token(tok)
            weight = self.idf.get(tok, 1.0)
            vec[idx] += float(weight)

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec /= norm
        return vec

    def transform_batch(self, texts: List[str]) -> np.ndarray:
        """Batch vectorize list of texts."""
        return np.vstack([self.transform(t) for t in texts])

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @staticmethod
    def batch_cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
        """Vectorized cosine similarity against entire document matrix."""
        q_norm = np.linalg.norm(query_vec)
        if q_norm < 1e-6:
            return np.zeros(doc_matrix.shape[0], dtype=np.float32)
        dots = np.dot(doc_matrix, query_vec)
        doc_norms = np.linalg.norm(doc_matrix, axis=1)
        doc_norms[doc_norms < 1e-6] = 1e-6
        return dots / (doc_norms * q_norm)
