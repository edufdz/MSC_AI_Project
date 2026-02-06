#!/usr/bin/env python3
"""
Customer Retriever Module
Retrieve similar customer snippets based on conversation context
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use environment variables directly

try:
    import faiss
except ImportError:
    raise ImportError("faiss not installed. Install with: pip install faiss-cpu")

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai not installed. Install with: pip install openai")


class CustomerRetriever:
    """Retriever for finding similar customer messages."""
    
    def __init__(self, index_dir: str = "vector_index"):
        """
        Initialize retriever.
        
        Args:
            index_dir: Path to directory containing FAISS index and metadata
        """
        index_path = Path(index_dir)
        
        # Load index configuration
        config_file = index_path / "index_config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Index config not found: {config_file}")
        
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.model = self.config['model']
        self.dimensions = self.config['dimensions']
        
        # Load FAISS index
        index_file = index_path / "snippets.index"
        if not index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        self.index = faiss.read_index(str(index_file))
        print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
        # Load metadata
        meta_file = index_path / "snippets_meta.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_file}")
        
        with open(meta_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        print(f"Loaded metadata for {len(self.metadata)} snippets")
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
    
    def _build_query_text(self, context: Dict) -> str:
        """Build query text from context."""
        dealership_turns = context.get('last_dealership_turns', [])
        customer_turns = context.get('last_customer_turns', [])
        
        # Limit to last 2 turns each
        dealership_turns = dealership_turns[-2:] if len(dealership_turns) > 2 else dealership_turns
        customer_turns = customer_turns[-2:] if len(customer_turns) > 2 else customer_turns
        
        parts = []
        if dealership_turns:
            parts.extend(dealership_turns)
        if customer_turns:
            parts.extend(customer_turns)
        
        if not parts:
            return ""
        
        return " | ".join(parts)
    
    def _embed_query(self, query_text: str) -> np.ndarray:
        """Generate embedding for query text."""
        if not query_text:
            # Return zero vector if empty query
            return np.zeros((1, self.dimensions), dtype=np.float32)
        
        response = self.client.embeddings.create(
            model=self.model,
            input=[query_text]
        )
        embedding = np.array([response.data[0].embedding], dtype=np.float32)
        return embedding
    
    def _filter_results(self, results: List[Dict], scenario: Optional[str] = None, 
                       stage: Optional[str] = None) -> List[Dict]:
        """Filter results by scenario and/or stage."""
        filtered = results
        
        if scenario:
            filtered = [r for r in filtered if r.get('scenario') == scenario]
        
        if stage:
            filtered = [r for r in filtered if r.get('stage') == stage]
        
        return filtered
    
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        if not texts:
            return np.zeros((0, self.dimensions), dtype=np.float32)
        
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        embeddings = np.array([item.embedding for item in response.data], dtype=np.float32)
        return embeddings
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
    
    def _mmr_selection(self, candidates: List[Dict], query_embedding: np.ndarray, 
                      k: int, lambda_param: float = 0.5) -> List[Dict]:
        """
        Select diverse results using Maximal Marginal Relevance (MMR).
        
        Args:
            candidates: List of candidate results with similarity_score
            query_embedding: Query embedding vector (1D numpy array)
            k: Number of results to return
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
                          Default 0.5 balances both
        
        Returns:
            List of k diverse results
        """
        if not candidates:
            return []
        
        if len(candidates) <= k:
            return candidates
        
        # Get embeddings for all candidates (for diversity calculation)
        candidate_texts = []
        for cand in candidates:
            # Build text for embedding (same as get_embedding_text logic)
            snippet_type = cand.get('snippet_type', 'customer_turn')
            customer_text = cand.get('customer_text', '').strip()
            prev_dealership = cand.get('prev_dealership_text')
            
            if snippet_type == 'dealer_customer_pair':
                pair_text = cand.get('pair_text')
                if pair_text:
                    candidate_texts.append(pair_text)
                elif prev_dealership:
                    candidate_texts.append(f"{prev_dealership} | {customer_text}")
                else:
                    candidate_texts.append(customer_text)
            elif snippet_type == 'three_turn_window':
                window_text = cand.get('window_text')
                if window_text:
                    candidate_texts.append(window_text)
                elif prev_dealership:
                    candidate_texts.append(f"{prev_dealership} | {customer_text}")
                else:
                    candidate_texts.append(customer_text)
            elif snippet_type == 'sentence_chunk':
                candidate_texts.append(customer_text)
            else:
                # customer_turn
                if prev_dealership:
                    candidate_texts.append(f"{prev_dealership} | {customer_text}")
                else:
                    candidate_texts.append(customer_text)
        
        # Generate embeddings for candidates
        candidate_embeddings = self._embed_texts(candidate_texts)
        
        # Normalize query embedding for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Normalize candidate embeddings
        candidate_norms = candidate_embeddings / np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
        
        # Calculate relevance scores (cosine similarity to query)
        relevance_scores = np.dot(candidate_norms, query_norm.T).flatten()
        
        # Initialize selected set with top result
        selected_indices = [0]  # Start with highest relevance
        selected_embeddings = [candidate_norms[0]]
        
        # Select remaining k-1 results using MMR
        for _ in range(k - 1):
            best_mmr_score = -float('inf')
            best_idx = None
            
            for idx, cand_emb in enumerate(candidate_norms):
                if idx in selected_indices:
                    continue
                
                # Relevance: similarity to query
                relevance = float(relevance_scores[idx])
                
                # Diversity: max similarity to already-selected results
                max_sim_to_selected = 0.0
                for sel_emb in selected_embeddings:
                    sim = float(np.dot(cand_emb, sel_emb))
                    max_sim_to_selected = max(max_sim_to_selected, sim)
                
                # MMR score: lambda * relevance - (1 - lambda) * diversity
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
                
                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                selected_embeddings.append(candidate_norms[best_idx])
            else:
                break  # No more candidates
        
        # Return selected candidates in order of selection
        selected = [candidates[i] for i in selected_indices]
        return selected
    
    def get_anchors(self, context: Dict, k: int = 8, 
                   scenario: Optional[str] = None, 
                   stage: Optional[str] = None,
                   use_mmr: bool = True,
                   mmr_lambda: float = 0.5) -> List[Dict]:
        """
        Retrieve similar customer snippets based on context with MMR diversity.
        
        Args:
            context: Dict with keys:
                - last_dealership_turns: List[str] (last 1-2 dealership messages)
                - last_customer_turns: List[str] (last 1-2 customer messages)
            k: Number of results to return (default 8, range 5-12)
            scenario: Optional scenario filter
            stage: Optional stage filter
            use_mmr: Whether to use MMR for diversity (default True)
            mmr_lambda: MMR lambda parameter (0.0 = max diversity, 1.0 = max relevance)
        
        Returns:
            List of snippet dicts with:
                - customer_text
                - prev_dealership_text
                - scenario
                - stage
                - similarity_score
                - snippet_type (if available)
        """
        # Validate k
        k = max(5, min(12, k))
        
        # Build query
        query_text = self._build_query_text(context)
        
        if not query_text:
            # Return random samples if no context
            import random
            samples = random.sample(self.metadata, min(k, len(self.metadata)))
            return [{
                'customer_text': s['customer_text'],
                'prev_dealership_text': s.get('prev_dealership_text'),
                'scenario': s.get('scenario'),
                'stage': s.get('stage'),
                'similarity_score': 0.5,  # Random, no similarity
                'snippet_type': s.get('snippet_type', 'customer_turn')
            } for s in samples]
        
        # Generate query embedding
        query_embedding = self._embed_query(query_text)
        
        # Retrieve top 50 candidates for MMR (or more if filtering needed)
        search_k = 50 if use_mmr else (k * 2 if (scenario or stage) else k)
        search_k = min(search_k, self.index.ntotal)
        
        distances, indices = self.index.search(query_embedding, search_k)
        
        # Get results with metadata
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            meta = self.metadata[idx]
            similarity = 1 / (1 + dist)  # Convert L2 distance to similarity
            
            result = {
                'customer_text': meta['customer_text'],
                'prev_dealership_text': meta.get('prev_dealership_text'),
                'scenario': meta.get('scenario'),
                'stage': meta.get('stage'),
                'similarity_score': float(similarity),
                'snippet_type': meta.get('snippet_type', 'customer_turn'),
            }
            
            # Add type-specific fields if present
            if 'pair_text' in meta:
                result['pair_text'] = meta['pair_text']
            if 'window_text' in meta:
                result['window_text'] = meta['window_text']
            
            results.append(result)
        
        # Apply filters if provided
        if scenario or stage:
            filtered = self._filter_results(results, scenario, stage)
            
            # If filtering reduced results too much, use unfiltered
            if len(filtered) < k:
                filtered = results[:k]
        else:
            filtered = results
        
        # Apply MMR for diversity if enabled
        if use_mmr and len(filtered) > k:
            # Use MMR to select diverse top k
            # query_embedding is (1, dim), extract the vector
            query_vec = query_embedding[0] if query_embedding.ndim > 1 else query_embedding
            selected = self._mmr_selection(filtered, query_vec, k, mmr_lambda)
            return selected
        else:
            # Return top k without MMR
            return filtered[:k]


def main():
    """Example usage."""
    import sys
    
    # Example context
    context = {
        'last_dealership_turns': [
            '¿Desea agendar una cita para el día de mañana?',
            'Claro, el día lunes tenemos disponibilidad de recepción desde las 7 am a las 12 pm'
        ],
        'last_customer_turns': [
            'Para el Lunes podrá?'
        ]
    }
    
    try:
        retriever = CustomerRetriever()
        
        print("Retrieving anchors...")
        anchors = retriever.get_anchors(context, k=8, scenario='booking_service_appointment')
        
        print(f"\nFound {len(anchors)} anchors:")
        for i, anchor in enumerate(anchors, 1):
            print(f"\n{i}. Similarity: {anchor['similarity_score']:.3f}")
            print(f"   Customer: {anchor['customer_text'][:80]}...")
            if anchor.get('prev_dealership_text'):
                print(f"   Context: {anchor['prev_dealership_text'][:60]}...")
            print(f"   Scenario: {anchor.get('scenario')}, Stage: {anchor.get('stage')}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
