#!/usr/bin/env python3
"""
Step 3.2: Embed and Index Snippets
Build FAISS vector index from customer snippets using OpenAI embeddings
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict
import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use environment variables directly

try:
    import faiss
except ImportError:
    print("Error: faiss not installed. Install with: pip install faiss-cpu")
    exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai not installed. Install with: pip install openai")
    exit(1)

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536  # text-embedding-3-small dimension
BATCH_SIZE = 100  # OpenAI batch limit


def get_embedding_text(snippet: Dict) -> str:
    """
    Create embedding text from snippet based on snippet type.
    
    Handles different snippet types:
    - customer_turn: customer_text only (or with prev_dealership_text)
    - dealer_customer_pair: uses pair_text if available
    - three_turn_window: uses window_text if available
    - sentence_chunk: sentence only (customer_text contains the sentence)
    """
    snippet_type = snippet.get('snippet_type', 'customer_turn')
    
    if snippet_type == 'dealer_customer_pair':
        # Use pair_text if available, otherwise construct it
        pair_text = snippet.get('pair_text')
        if pair_text:
            return pair_text
        # Fallback to constructing from components
        customer_text = snippet.get('customer_text', '').strip()
        prev_dealership = snippet.get('prev_dealership_text')
        if prev_dealership:
            return f"{prev_dealership} | {customer_text}"
        return customer_text
    
    elif snippet_type == 'three_turn_window':
        # Use window_text if available
        window_text = snippet.get('window_text')
        if window_text:
            return window_text
        # Fallback: construct from available turns
        customer_text = snippet.get('customer_text', '').strip()
        prev_dealership = snippet.get('prev_dealership_text')
        if prev_dealership:
            return f"{prev_dealership} | {customer_text}"
        return customer_text
    
    elif snippet_type == 'sentence_chunk':
        # For sentence chunks, use just the sentence (customer_text contains the sentence)
        customer_text = snippet.get('customer_text', '').strip()
        return customer_text
    
    else:
        # Default: customer_turn (backward compatible)
        customer_text = snippet.get('customer_text', '').strip()
        prev_dealership = snippet.get('prev_dealership_text')
        
        if prev_dealership:
            return f"{prev_dealership} | {customer_text}"
        return customer_text


def generate_embeddings_batch(client: OpenAI, texts: List[str], model: str) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    try:
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise


def build_index(snippets: List[Dict], index_dir: Path):
    """Build FAISS index from snippets."""
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Create index directory
    index_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating embeddings for {len(snippets)} snippets...")
    print(f"Using model: {EMBEDDING_MODEL}")
    
    # Prepare texts for embedding
    embedding_texts = [get_embedding_text(snippet) for snippet in snippets]
    
    # Generate embeddings in batches
    all_embeddings = []
    for i in range(0, len(embedding_texts), BATCH_SIZE):
        batch = embedding_texts[i:i+BATCH_SIZE]
        print(f"  Processing batch {i//BATCH_SIZE + 1}/{(len(embedding_texts)-1)//BATCH_SIZE + 1}...")
        
        embeddings = generate_embeddings_batch(client, batch, EMBEDDING_MODEL)
        all_embeddings.extend(embeddings)
        
        # Rate limiting: small delay between batches
        if i + BATCH_SIZE < len(embedding_texts):
            time.sleep(0.1)
    
    # Convert to numpy array
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    print(f"Generated {len(embeddings_array)} embeddings of dimension {embeddings_array.shape[1]}")
    
    # Build FAISS index
    print("Building FAISS index...")
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(embeddings_array)
    print(f"Index built with {index.ntotal} vectors")
    
    # Save index
    index_file = index_dir / "snippets.index"
    faiss.write_index(index, str(index_file))
    print(f"Index saved to {index_file}")
    
    # Save metadata
    metadata = []
    for i, snippet in enumerate(snippets):
        meta_entry = {
            'index_id': i,
            'conversation_id': snippet.get('conversation_id'),
            'turn_index': snippet.get('turn_index'),
            'scenario': snippet.get('scenario'),
            'stage': snippet.get('stage'),
            'customer_text': snippet.get('customer_text'),
            'prev_dealership_text': snippet.get('prev_dealership_text'),
            'snippet_type': snippet.get('snippet_type', 'customer_turn'),  # Add snippet type
        }
        
        # Add type-specific fields if present
        if 'pair_text' in snippet:
            meta_entry['pair_text'] = snippet['pair_text']
        if 'window_text' in snippet:
            meta_entry['window_text'] = snippet['window_text']
        if 'sentence_index' in snippet:
            meta_entry['sentence_index'] = snippet['sentence_index']
        if 'original_customer_text' in snippet:
            meta_entry['original_customer_text'] = snippet['original_customer_text']
        
        metadata.append(meta_entry)
    
    meta_file = index_dir / "snippets_meta.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Metadata saved to {meta_file}")
    
    # Save index configuration
    config = {
        'model': EMBEDDING_MODEL,
        'dimensions': EMBEDDING_DIM,
        'index_type': 'IndexFlatL2',
        'total_vectors': index.ntotal,
        'batch_size': BATCH_SIZE,
    }
    
    config_file = index_dir / "index_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_file}")
    
    return index, metadata


def test_index(index, metadata: List[Dict], index_dir: Path):
    """Test the index with a sample query."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return
    
    client = OpenAI(api_key=api_key)
    
    # Test query
    test_query = "quiero cita para servicio, tengo prisa"
    print(f"\nTesting index with query: '{test_query}'")
    
    # Generate query embedding
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[test_query]
    )
    query_embedding = np.array([response.data[0].embedding], dtype=np.float32)
    
    # Search
    k = 5
    distances, indices = index.search(query_embedding, k)
    
    print(f"\nTop {k} results:")
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        meta = metadata[idx]
        similarity = 1 / (1 + dist)  # Convert distance to similarity
        print(f"\n  {i+1}. Similarity: {similarity:.3f}")
        print(f"     Customer: {meta['customer_text'][:80]}...")
        if meta.get('prev_dealership_text'):
            print(f"     Context: {meta['prev_dealership_text'][:60]}...")
        print(f"     Scenario: {meta.get('scenario')}, Stage: {meta.get('stage')}")


def main():
    """Main function to build index."""
    base_dir = Path(__file__).parent.parent
    
    # Try expanded snippets first, fallback to original
    snippets_file = base_dir / "out" / "snippets_expanded.jsonl"
    if not snippets_file.exists():
        snippets_file = base_dir / "out" / "customer_snippets.jsonl"
    
    index_dir = base_dir / "vector_index"
    
    if not snippets_file.exists():
        print(f"Error: No snippets file found")
        print("Run 15_create_snippets.py or 27_expand_snippets.py first!")
        exit(1)
    
    print(f"Using snippets file: {snippets_file.name}")
    
    # Load snippets
    print(f"Loading snippets from {snippets_file}...")
    snippets = []
    with open(snippets_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            snippet = json.loads(line)
            snippets.append(snippet)
    
    print(f"Loaded {len(snippets)} snippets")
    
    if not snippets:
        print("Error: No snippets found")
        exit(1)
    
    # Build index
    index, metadata = build_index(snippets, index_dir)
    
    # Test index
    test_index(index, metadata, index_dir)
    
    print(f"\n✅ Index build complete!")
    print(f"Index directory: {index_dir}")


if __name__ == "__main__":
    main()
