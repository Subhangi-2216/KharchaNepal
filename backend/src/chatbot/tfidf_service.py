# backend/src/chatbot/tfidf_service.py
"""
Enhanced TF-IDF service for more robust FAQ matching.

Features:
- Improved vectorization with better preprocessing
- Support for fuzzy matching to handle typos
- Dynamic threshold based on query length
- Multiple matching strategies (TF-IDF, keyword, fuzzy)
- Detailed match information with confidence scores
"""

import re
import logging
import difflib
from typing import Dict, List, Tuple, Any, Optional, Set

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Define confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4
VERY_LOW_CONFIDENCE = 0.2

class TfidfMatcher:
    """
    Enhanced TF-IDF based FAQ matcher.

    This class uses multiple strategies to match user queries to FAQ entries:
    1. TF-IDF vectorization with cosine similarity
    2. Keyword matching with frequency analysis
    3. Fuzzy matching for handling typos and misspellings
    """

    def __init__(self, faq_data: Dict[str, Dict[str, Any]]):
        """
        Initialize the TF-IDF matcher.

        Args:
            faq_data: Dictionary of FAQ entries with keywords and responses
        """
        self.faq_data = faq_data

        # Create a more sophisticated vectorizer
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 3),  # Use unigrams, bigrams, and trigrams
            min_df=1,            # Include terms that appear in at least 1 document
            max_df=0.9,          # Exclude terms that appear in more than 90% of documents
            sublinear_tf=True    # Apply sublinear tf scaling (1 + log(tf))
        )

        # Prepare corpus for vectorization
        self.faq_ids = []
        self.corpus = []
        self.keyword_sets = {}   # Store sets of keywords for direct matching

        for faq_id, data in faq_data.items():
            # Combine keywords into a single string for TF-IDF
            keywords_text = ' '.join(data['keywords'])
            self.faq_ids.append(faq_id)
            self.corpus.append(keywords_text)

            # Store lowercase keywords as a set for direct matching
            self.keyword_sets[faq_id] = {kw.lower() for kw in data['keywords']}

        # Fit the vectorizer on the corpus
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)
            logging.info(f"Enhanced TF-IDF vectorizer fitted on {len(self.corpus)} FAQ entries")
            self.vocabulary = self.vectorizer.get_feature_names_out()
            logging.info(f"Vocabulary size: {len(self.vocabulary)} terms")
        except Exception as e:
            logging.error(f"Error fitting TF-IDF vectorizer: {e}")
            # Create an empty matrix as fallback
            self.tfidf_matrix = None
            self.vocabulary = []

    def match(self, query: str, base_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Match a user query to the best FAQ entry using multiple strategies.

        Args:
            query: User query
            base_threshold: Base minimum similarity score to consider a match

        Returns:
            Dictionary with match information or None if no match found
        """
        result = {}

        # Clean the query
        clean_query = self._clean_text(query)
        query_words = set(clean_query.split())

        # Adjust threshold based on query length
        # Shorter queries need higher thresholds to avoid false positives
        adjusted_threshold = self._adjust_threshold(base_threshold, len(query_words))

        # Try TF-IDF matching first (if available)
        tfidf_match = None
        if self.tfidf_matrix is not None:
            tfidf_match = self._tfidf_match(clean_query, adjusted_threshold)

        # Try direct keyword matching
        keyword_match = self._keyword_match(query_words)

        # Try fuzzy matching for handling typos
        fuzzy_match = self._fuzzy_match(query_words)

        # Combine and rank all matches
        all_matches = []

        if tfidf_match:
            all_matches.append(("tfidf", tfidf_match))

        if keyword_match:
            all_matches.append(("keyword", keyword_match))

        if fuzzy_match:
            all_matches.append(("fuzzy", fuzzy_match))

        if all_matches:
            # Sort by confidence (highest first)
            all_matches.sort(key=lambda x: x[1]["confidence"], reverse=True)

            # Get the best match
            best_match_type, best_match = all_matches[0]

            # Prepare the result
            result = {
                "response": best_match["response"],
                "confidence": best_match["confidence"],
                "match_type": best_match_type,
                "faq_id": best_match["faq_id"]
            }

            # Include match details
            if "details" in best_match:
                result["details"] = best_match["details"]

            # Include alternatives if available
            if len(all_matches) > 1:
                alternatives = []
                for match_type, match in all_matches[1:]:
                    # Only include if confidence is at least 70% of the best match
                    if match["confidence"] >= best_match["confidence"] * 0.7:
                        alternatives.append({
                            "response": match["response"],
                            "confidence": match["confidence"],
                            "match_type": match_type,
                            "faq_id": match["faq_id"]
                        })
                if alternatives:
                    result["alternatives"] = alternatives[:2]  # Limit to top 2 alternatives

            logging.info(f"Matched query '{query}' using {best_match_type} with confidence {best_match['confidence']:.2f}")
            return result["response"], result["confidence"]

        logging.info(f"No match found for query '{query}'")
        return None

    def _tfidf_match(self, clean_query: str, threshold: float) -> Optional[Dict[str, Any]]:
        """
        Match a query using TF-IDF vectorization and cosine similarity.

        Args:
            clean_query: Cleaned user query
            threshold: Minimum similarity score to consider a match

        Returns:
            Match information or None if no match found
        """
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([clean_query])

            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

            # Find the top 3 matches
            top_indices = similarities.argsort()[-3:][::-1]
            top_scores = similarities[top_indices]

            # Check if the best match exceeds the threshold
            if top_scores[0] >= threshold:
                best_idx = top_indices[0]
                best_score = top_scores[0]
                best_faq_id = self.faq_ids[best_idx]

                # Map similarity score to confidence level
                confidence = self._map_similarity_to_confidence(best_score)

                # Get the most important terms for this match
                important_terms = self._get_important_terms(query_vector, best_idx)

                return {
                    "faq_id": best_faq_id,
                    "response": self.faq_data[best_faq_id]['response'],
                    "confidence": confidence,
                    "similarity": best_score,
                    "details": {
                        "important_terms": important_terms,
                        "matched_keywords": list(self.keyword_sets[best_faq_id])[:5]  # Limit to top 5
                    }
                }
        except Exception as e:
            logging.error(f"Error in TF-IDF matching: {e}")

        return None

    def _keyword_match(self, query_words: Set[str]) -> Optional[Dict[str, Any]]:
        """
        Match a query using direct keyword matching.

        Args:
            query_words: Set of words in the query

        Returns:
            Match information or None if no match found
        """
        best_match = None
        best_score = 0

        for faq_id, keywords in self.keyword_sets.items():
            # Count how many keywords match
            matches = query_words.intersection(keywords)

            if matches:
                # Calculate score based on number and proportion of matches
                num_matches = len(matches)
                proportion = num_matches / len(keywords)

                # Combined score (weighted average)
                score = (0.7 * proportion) + (0.3 * (num_matches / max(len(query_words), 1)))

                if score > best_score:
                    best_score = score
                    best_match = {
                        "faq_id": faq_id,
                        "response": self.faq_data[faq_id]['response'],
                        "confidence": self._map_similarity_to_confidence(score),
                        "similarity": score,
                        "details": {
                            "matched_keywords": list(matches),
                            "match_count": num_matches,
                            "keyword_count": len(keywords)
                        }
                    }

        return best_match

    def _fuzzy_match(self, query_words: Set[str], min_similarity: float = 0.8) -> Optional[Dict[str, Any]]:
        """
        Match a query using fuzzy matching for handling typos.

        Args:
            query_words: Set of words in the query
            min_similarity: Minimum similarity ratio for fuzzy matching

        Returns:
            Match information or None if no match found
        """
        best_match = None
        best_score = 0

        # Skip very short words for fuzzy matching
        filtered_query_words = {w for w in query_words if len(w) >= 3}

        if not filtered_query_words:
            return None

        for faq_id, keywords in self.keyword_sets.items():
            fuzzy_matches = []

            # For each query word, find the best matching keyword
            for query_word in filtered_query_words:
                best_keyword = None
                best_ratio = 0

                for keyword in keywords:
                    # Skip very short keywords
                    if len(keyword) < 3:
                        continue

                    # Calculate similarity ratio
                    ratio = difflib.SequenceMatcher(None, query_word, keyword).ratio()

                    if ratio > best_ratio and ratio >= min_similarity:
                        best_ratio = ratio
                        best_keyword = keyword

                if best_keyword:
                    fuzzy_matches.append((query_word, best_keyword, best_ratio))

            if fuzzy_matches:
                # Calculate score based on number and quality of matches
                num_matches = len(fuzzy_matches)
                avg_ratio = sum(m[2] for m in fuzzy_matches) / num_matches

                # Combined score (weighted average)
                score = (0.6 * avg_ratio) + (0.4 * (num_matches / len(filtered_query_words)))

                if score > best_score:
                    best_score = score
                    best_match = {
                        "faq_id": faq_id,
                        "response": self.faq_data[faq_id]['response'],
                        "confidence": self._map_similarity_to_confidence(score * 0.9),  # Slightly lower confidence for fuzzy matches
                        "similarity": score,
                        "details": {
                            "fuzzy_matches": [{"query": m[0], "keyword": m[1], "similarity": m[2]} for m in fuzzy_matches],
                            "match_count": num_matches,
                            "average_similarity": avg_ratio
                        }
                    }

        return best_match

    def _get_important_terms(self, query_vector, doc_idx, top_n: int = 5) -> List[str]:
        """
        Get the most important terms for a match.

        Args:
            query_vector: Vectorized query
            doc_idx: Index of the matched document
            top_n: Number of top terms to return

        Returns:
            List of important terms
        """
        # Get the feature indices in the query vector
        query_features = query_vector.indices

        # Get the feature indices in the document vector
        doc_vector = self.tfidf_matrix[doc_idx]
        doc_features = doc_vector.indices

        # Find common features
        common_features = set(query_features).intersection(set(doc_features))

        # Get the TF-IDF scores for common features
        feature_scores = []
        for feature_idx in common_features:
            query_score = query_vector[0, feature_idx]
            doc_score = doc_vector[0, feature_idx]
            combined_score = query_score * doc_score
            feature_scores.append((feature_idx, combined_score))

        # Sort by score (highest first)
        feature_scores.sort(key=lambda x: x[1], reverse=True)

        # Get the top N terms
        top_terms = []
        for feature_idx, score in feature_scores[:top_n]:
            term = self.vocabulary[feature_idx]
            top_terms.append(term)

        return top_terms

    def _adjust_threshold(self, base_threshold: float, query_length: int) -> float:
        """
        Adjust the threshold based on query length.

        Args:
            base_threshold: Base threshold
            query_length: Number of words in the query

        Returns:
            Adjusted threshold
        """
        if query_length <= 2:
            # Very short queries need higher threshold
            return base_threshold * 1.5
        elif query_length <= 4:
            # Short queries need slightly higher threshold
            return base_threshold * 1.2
        elif query_length >= 10:
            # Long queries can have lower threshold
            return base_threshold * 0.8
        else:
            # Medium-length queries use the base threshold
            return base_threshold

    def _map_similarity_to_confidence(self, similarity: float) -> float:
        """
        Map a similarity score to a confidence level.

        Args:
            similarity: Similarity score (0.0-1.0)

        Returns:
            Confidence level (0.0-1.0)
        """
        if similarity >= 0.8:
            return HIGH_CONFIDENCE
        elif similarity >= 0.6:
            return MEDIUM_CONFIDENCE
        elif similarity >= 0.4:
            return LOW_CONFIDENCE
        else:
            return VERY_LOW_CONFIDENCE

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

        # Remove punctuation (keep apostrophes for contractions)
        text = re.sub(r'[^\w\s\']', ' ', text)

        # Replace contractions
        text = re.sub(r'\'s\b', ' is', text)
        text = re.sub(r'\'re\b', ' are', text)
        text = re.sub(r'\'ve\b', ' have', text)
        text = re.sub(r'\'m\b', ' am', text)
        text = re.sub(r'\'ll\b', ' will', text)
        text = re.sub(r'\'d\b', ' would', text)
        text = re.sub(r'\'t\b', ' not', text)

        # Remove remaining apostrophes
        text = text.replace('\'', '')

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text