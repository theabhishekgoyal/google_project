"""
Retrieve the most relevant policy clause for a given query using TF-IDF + cosine similarity.
This is the core NLP component of the system.
"""

from typing import List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.schemas import PolicyChunk, Citation


class ClauseRetriever:
    """Builds a TF-IDF index over policy chunks and retrieves the best match for a query."""

    def __init__(self, chunks: List[PolicyChunk]):
        self.chunks = chunks
        self.texts = [chunk.text for chunk in chunks]

        if self.texts:
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2),
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

    def retrieve(self, query: str, top_k: int = 1) -> List[Tuple[PolicyChunk, float]]:
        """
        Return the top_k most relevant chunks for a query, with similarity scores.
        """
        if not self.texts or self.vectorizer is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.0:
                results.append((self.chunks[idx], float(similarities[idx])))

        return results

    def get_best_citation(self, query: str) -> Optional[Citation]:
        """Return a Citation from the best matching chunk, or None if no match."""
        results = self.retrieve(query, top_k=1)
        if not results:
            return None

        chunk, score = results[0]
        if score < 0.01:
            return None

        # Truncate clause text for readability
        clause_text = chunk.text[:300]
        if len(chunk.text) > 300:
            clause_text += "..."

        return Citation(page=chunk.page, clause_text=clause_text)
