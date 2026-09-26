import json
import os
import re
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi
import numpy as np

from engine.vectorizer import DenseVectorizer
from engine.schema import ActionableDeepLink, StepGroup, ValidationDeepLink
from engine.safe_planner import SafePlanOrderer
from engine.sanitizer import PipelineSanitizer


class HybridRetriever:
    """
    Hybrid Retrieval Engine combining:
    - BM25Okapi keyword search over metadata & keyword indices
    - Dense Vector Embeddings with subword n-gram cosine matching
    - Reciprocal / Normalized linear score fusion
    - Confidence thresholding for clean fallback ("contexts": [], "fallback": "no match")
    """

    FALLBACK_STOPWORDS = {
        "cake", "bake", "recipe", "cook", "pizza", "weather", "forecast", "stock",
        "crypto", "bitcoin", "president", "capital", "movie", "song", "lyrics",
        "flight", "hotel", "restaurant", "football", "cricket"
    }

    def __init__(self, deeplinks_path: str = "data/deeplinks.json", vector_dim: int = 256):
        self.deeplinks_path = deeplinks_path
        self.vector_dim = vector_dim
        self.documents: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.vectorizer = DenseVectorizer(vector_dim=vector_dim)
        self.doc_matrix: Optional[np.ndarray] = None
        self.confidence_threshold = 0.22
        self.is_warmed = False

        self._load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-z0-9]+\b", text.lower())

    def _load_and_index(self):
        if not os.path.exists(self.deeplinks_path):
            raise FileNotFoundError(f"DeepLinks database not found at {self.deeplinks_path}")

        with open(self.deeplinks_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        # Build corpus texts for indexing
        corpus_texts = []
        tokenized_corpus = []

        for doc in self.documents:
            kw_str = " ".join(doc.get("keywords", []))
            meta_str = f"{doc.get('category', '')} {doc.get('title', '')} {doc.get('description', '')} {kw_str}"
            corpus_texts.append(meta_str)
            tokenized_corpus.append(self._tokenize(meta_str))

        # 1. Initialize BM25
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 2. Fit and compute Dense Vectors
        self.vectorizer.fit(corpus_texts)
        self.doc_matrix = self.vectorizer.transform_batch(corpus_texts)

        self.is_warmed = True

    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "at", "to",
        "for", "with", "by", "from", "who", "what", "where", "when", "why", "how",
        "and", "or", "so", "this", "that", "these", "those", "my", "your", "can",
        "you", "please", "me", "tell", "give", "show"
    }

    def retrieve(self, query: str, top_k: int = 4) -> Tuple[bool, List[Dict[str, Any]], float]:
        """
        Performs hybrid retrieval over indexed deeplinks.
        Returns: (is_fallback, scored_documents, max_score)
        """
        clean_query = query.strip().lower()
        all_tokens = self._tokenize(clean_query)

        # Immediate out-of-domain stopword check
        if any(w in all_tokens for w in self.FALLBACK_STOPWORDS):
            return True, [], 0.0

        content_tokens = [t for t in all_tokens if t not in self.STOPWORDS]
        if not content_tokens or len(clean_query) < 3:
            return True, [], 0.0

        # BM25 scoring over content tokens
        bm25_scores = np.array(self.bm25.get_scores(content_tokens), dtype=np.float32)
        bm25_max = np.max(bm25_scores) if len(bm25_scores) > 0 else 0.0

        # If absolutely NO content token matches any Samsung settings or keywords,
        # it is cleanly out-of-domain (Zero Hallucination Fallback)
        if bm25_max <= 1e-6:
            return True, [], 0.0

        bm25_norm = bm25_scores / bm25_max

        # Dense Cosine scoring
        query_vec = self.vectorizer.transform(clean_query)
        dense_scores = self.vectorizer.batch_cosine_similarity(query_vec, self.doc_matrix)
        dense_scores = np.clip(dense_scores, 0.0, 1.0)

        # Hybrid fusion: 50% BM25 + 50% Dense
        hybrid_scores = 0.5 * bm25_norm + 0.5 * dense_scores

        max_score = float(np.max(hybrid_scores))

        # Confidence check for Fallback handling
        if max_score < self.confidence_threshold:
            return True, [], max_score

        # Get top-k indices
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(hybrid_scores[idx])
            if score >= self.confidence_threshold:
                doc = dict(self.documents[idx])
                doc["retrieval_score"] = round(score, 4)
                results.append(doc)

        if not results:
            return True, [], max_score

        return False, results, max_score
