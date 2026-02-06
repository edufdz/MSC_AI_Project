#!/usr/bin/env python3
"""
Step B: Add Topic Labels
Classify conversations as sales, post_sales, or unknown
"""

import json
import re
from pathlib import Path
from typing import Dict, List

# Post-sales indicators (high confidence)
POST_SALES_SIGNALS = [
    r'servicio de mantenimiento',
    r'cita de servicio',
    r'programar tu cita',
    r'\bmantenimiento\b',
    r'\bkilometraje\b',
    r'cambio de aceite',
    r'folio cita',
    r'confirmamos su cita',
    r'horarios de recepción',
    r'horarios de recepcion',
    r'lavado de carrocería',
    r'revisión de \d+ puntos',
    r'rotación de ruedas',
    r'filtro de aceite',
    r'ya es momento de realizarle',
    r'ha transcurrido un año',
    r'mi auto.*servicio',
    r'mi unidad.*servicio',
    r'mi coche.*servicio',
]

# Sales indicators (high confidence)
SALES_SIGNALS = [
    r'busco auto',
    r'busco vehículo',
    r'busco vehiculo',
    r'seminuevos',
    r'\bcotización\b',
    r'\bprecio\b',
    r'\benganche\b',
    r'\brequisitos\b',
    r'vehículo.*interés',
    r'vehiculo.*interes',
    r'auto.*interés',
    r'auto.*interes',
    r'seminuevos\.chevrolettlahuac\.com',
    r'quiero comprar',
    r'me interesa.*auto',
    r'me interesa.*vehículo',
    r'me interesa.*vehiculo',
]


def classify_topic(conversation: Dict) -> tuple[str, float]:
    """
    Classify conversation topic based on signals.
    Returns: (topic, confidence)
    """
    # Collect all text from conversation
    all_text = ' '.join([
        msg.get('text', '') or msg.get('text_raw', '')
        for msg in conversation.get('messages', [])
    ]).lower()
    
    post_sales_score = 0
    sales_score = 0
    
    # Count post-sales signals
    for pattern in POST_SALES_SIGNALS:
        matches = len(re.findall(pattern, all_text, re.IGNORECASE))
        post_sales_score += matches
    
    # Count sales signals
    for pattern in SALES_SIGNALS:
        matches = len(re.findall(pattern, all_text, re.IGNORECASE))
        sales_score += matches
    
    # Calculate confidence based on score difference
    total_signals = post_sales_score + sales_score
    
    if total_signals == 0:
        return ('unknown', 0.0)
    
    score_diff = abs(post_sales_score - sales_score)
    confidence = min(0.5 + (score_diff / total_signals) * 0.5, 0.95)
    
    if post_sales_score > sales_score:
        return ('post_sales', confidence)
    elif sales_score > post_sales_score:
        return ('sales', confidence)
    else:
        return ('unknown', 0.5)


def main():
    """Main function to label topics."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_sanitized.json"
    output_file = base_dir / "out" / "dataset_sanitized.json"
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        print("Run 09_sanitize.py first!")
        return
    
    print(f"Loading sanitized dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Labeling topics for {len(conversations)} conversations...")
    
    topic_counts = {'post_sales': 0, 'sales': 0, 'unknown': 0}
    
    for conv in conversations:
        topic, confidence = classify_topic(conv)
        
        # Add labels field
        conv['labels'] = {
            'topic': topic,
            'confidence': round(confidence, 2)
        }
        
        topic_counts[topic] += 1
    
    # Save updated dataset
    print(f"Writing labeled dataset to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    # Print summary
    total = len(conversations)
    print(f"\n✅ Topic labeling complete!")
    print(f"\nSummary:")
    print(f"  Total conversations: {total}")
    print(f"  Post-sales: {topic_counts['post_sales']} ({topic_counts['post_sales']/total*100:.1f}%)")
    print(f"  Sales: {topic_counts['sales']} ({topic_counts['sales']/total*100:.1f}%)")
    print(f"  Unknown: {topic_counts['unknown']} ({topic_counts['unknown']/total*100:.1f}%)")


if __name__ == "__main__":
    main()
