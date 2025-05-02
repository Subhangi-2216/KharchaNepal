# backend/src/chatbot/tfidf_service.py
"""
TF-IDF service for more robust FAQ matching.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TfidfMatcher:
    """
    TF-IDF based FAQ matcher.
    
    This class uses TF-IDF vectorization and cosine similarity to match user queries
    to FAQ entries.
    """
    
    def __init__(self, faq_data: Dict[str, Dict[str, Any]]):
        """
        Initialize the TF-IDF matcher.
        
        Args:
            faq_data: Dictionary of FAQ entries with keywords and responses
        """
        self.faq_data = faq_data
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)  # Use unigrams and bigrams
        )
        
        # Prepare corpus for vectorization
        self.faq_ids = []
        self.corpus = []
        
        for faq_id, data in faq_data.items():
            # Combine keywords into a single string
            keywords_text = ' '.join(data['keywords'])
            self.faq_ids.append(faq_id)
            self.corpus.append(keywords_text)
        
        # Fit the vectorizer on the corpus
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
            logging.info(f"TF-IDF vectorizer fitted on {len(self.corpus)} FAQ entries")
        except Exception as e:
            logging.error(f"Error fitting TF-IDF vectorizer: {e}")
            # Create an empty matrix as fallback
            self.tfidf_matrix = None
    
    def match(self, query: str, threshold: float = 0.3) -> Optional[Tuple[str, float]]:
        """
        Match a user query to the best FAQ entry.
        
        Args:
            query: User query
            threshold: Minimum similarity score to consider a match
            
        Returns:
            Tuple of (response, similarity_score) or None if no match found
        """
        if self.tfidf_matrix is None:
            logging.warning("TF-IDF matcher not properly initialized, falling back to keyword matching")
            return None
        
        # Clean and vectorize the query
        clean_query = self._clean_text(query)
        query_vector = self.vectorizer.transform([clean_query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Find the best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            best_faq_id = self.faq_ids[best_idx]
            response = self.faq_data[best_faq_id]['response']
            logging.info(f"TF-IDF matched query '{query}' to FAQ '{best_faq_id}' with score {best_score:.2f}")
            return response, best_score
        
        logging.info(f"No good TF-IDF match found for query '{query}' (best score: {best_score:.2f})")
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better matching.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text