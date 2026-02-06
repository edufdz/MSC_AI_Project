#!/usr/bin/env python3
"""
Step 2.3: Build Taxonomy
Classify conversations by scenario (intent) and stage
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

# Scenario definitions with keywords and patterns
SCENARIOS = {
    'booking_service_appointment': {
        'keywords': [
            r'\bcita\b', r'\bagendar\b', r'\bprogramar\b', r'\bdisponibilidad\b',
            r'\bhorario\b', r'\bhorarios\b', r'\brecepción\b', r'\brecepcion\b',
            r'\bprogramar tu cita\b', r'\bagendar cita\b',
        ],
        'patterns': [
            r'quiero agendar', r'necesito cita', r'puedo programar',
            r'quiero programar', r'necesito agendar', r'disponibilidad de',
        ],
        'description': 'Customer requesting service appointment'
    },
    'status_update': {
        'keywords': [
            r'\bya quedó\b', r'\bpara cuándo\b', r'\bcuándo estará\b',
            r'\bestá listo\b', r'\bstatus\b', r'\bestado\b', r'\bavance\b',
        ],
        'patterns': [
            r'ya está listo', r'cuándo puedo pasar', r'sigue en taller',
            r'cuándo estará listo', r'ya terminaron', r'le avisamos',
        ],
        'description': 'Customer asking about service status'
    },
    'complaint_delay': {
        'keywords': [
            r'\btardaron\b', r'\bdemoraron\b', r'\blleva mucho\b',
            r'\bno me han llamado\b', r'\bprometieron\b', r'\bno cumplieron\b',
        ],
        'patterns': [
            r'ya lleva \d+ días', r'prometieron que', r'no cumplieron',
            r'lleva mucho tiempo', r'demoraron mucho',
        ],
        'description': 'Customer expressing frustration about delays'
    },
    'warranty_claim': {
        'keywords': [
            r'\bgarantía\b', r'\bgarantia\b', r'\bfalla\b', r'\bdefecto\b',
            r'\bno funciona\b', r'\bcubre garantía\b', r'\bcubre garantia\b',
        ],
        'patterns': [
            r'está en garantía', r'cubre la garantía', r'defecto de fábrica',
            r'está en garantia', r'cubre garantía',
        ],
        'description': 'Customer mentions warranty coverage'
    },
    'pricing_quote_dispute': {
        'keywords': [
            r'\bprecio\b', r'\bcosto\b', r'\bcotización\b', r'\bcotizacion\b',
            r'\bmuy caro\b', r'\bno coincide\b', r'\bcobraron\b',
        ],
        'patterns': [
            r'el precio no coincide', r'me dijeron que costaba',
            r'cobraron de más', r'precio diferente',
        ],
        'description': 'Customer questioning pricing'
    },
    'parts_availability': {
        'keywords': [
            r'\brefacciones\b', r'\brepuestos\b', r'\btienen\b',
            r'\bdisponible\b', r'\bllegó\b', r'\bllego\b', r'\bllegó la\b',
        ],
        'patterns': [
            r'tienen la refacción', r'cuándo llega', r'está disponible',
            r'tienen refacciones', r'llegó la refacción',
        ],
        'description': 'Customer asking about parts'
    },
    'rescheduling_no_show': {
        'keywords': [
            r'\breagendar\b', r'\bcambiar\b', r'\bno puedo\b',
            r'\botro día\b', r'\botro dia\b', r'\bfalté\b', r'\bfalte\b',
        ],
        'patterns': [
            r'quiero cambiar la cita', r'no puedo ir', r'me faltó',
            r'reagendar la cita', r'cambiar de día',
        ],
        'description': 'Customer needs to reschedule or missed appointment'
    },
    'pickup_delivery_logistics': {
        'keywords': [
            r'\brecoger\b', r'\bpasar por\b', r'\bentrega\b',
            r'\bpuedo pasar\b', r'\bestá listo\b', r'\bpaso por\b',
        ],
        'patterns': [
            r'puedo pasar por', r'cuándo puedo recoger', r'ya puedo pasar',
            r'puedo recoger', r'está listo para recoger',
        ],
        'description': 'Customer arranging pickup'
    },
    'invoice_payment_questions': {
        'keywords': [
            r'\bfactura\b', r'\bpago\b', r'\bcobro\b', r'\brecibo\b',
            r'\bcuánto\b', r'\bcuanto\b', r'\bdebo\b',
        ],
        'patterns': [
            r'necesito factura', r'cómo pago', r'cuánto debo',
            r'necesito recibo', r'cómo cobro',
        ],
        'description': 'Customer asking about payment/invoice'
    },
    'escalation_complaint': {
        'keywords': [
            r'\bgerente\b', r'\bsupervisor\b', r'\bqueja\b',
            r'\bmal servicio\b', r'\binsatisfecho\b', r'\binsatisfecha\b',
        ],
        'patterns': [
            r'quiero hablar con gerente', r'quiero hacer una queja',
            r'mal servicio', r'no estoy satisfecho',
        ],
        'description': 'Customer escalating or complaining'
    },
}

# Stage definitions
STAGES = {
    'opening': {
        'indicators': ['greetings', 'initial contact'],
        'patterns': [
            r'\bhola\b', r'\bbuenos días\b', r'\bbuenas tardes\b',
            r'\bbuenas noches\b', r'\bgracias por comunicarte\b',
        ],
        'description': 'Initial greeting and contact'
    },
    'info_gathering': {
        'indicators': ['dealership asking questions', 'customer providing details'],
        'patterns': [
            r'\bkilometraje\b', r'\bmodelo\b', r'\baño\b', r'\bano\b',
            r'\bqué servicio\b', r'\bque servicio\b', r'\bcuál es el problema\b',
            r'\bcual es el problema\b', r'\bunidad\b',
        ],
        'description': 'Gathering information about vehicle/service'
    },
    'scheduling': {
        'indicators': ['discussing dates', 'times', 'availability'],
        'patterns': [
            r'\bqué día\b', r'\bque dia\b', r'\bhorarios disponibles\b',
            r'\bconfirmamos\b', r'\bfolio\b', r'\bdisponibilidad\b',
        ],
        'description': 'Scheduling appointment'
    },
    'waiting_status_loop': {
        'indicators': ['customer checking status', 'dealership providing updates'],
        'patterns': [
            r'\bya está listo\b', r'\bsigue en taller\b', r'\bcuándo estará\b',
            r'\bcuando estara\b', r'\ble avisamos\b', r'\bestado\b',
        ],
        'description': 'Waiting for service completion, status updates'
    },
    'resolution': {
        'indicators': ['service completed', 'customer satisfied', 'closing'],
        'patterns': [
            r'\bya quedó\b', r'\bya quedo\b', r'\blisto para recoger\b',
            r'\bgracias\b', r'\btodo bien\b', r'\bterminado\b',
        ],
        'description': 'Service completed, resolution reached'
    },
    'escalation_complaint': {
        'indicators': ['customer unhappy', 'requesting manager', 'complaints'],
        'patterns': [
            r'\bquiero hablar con gerente\b', r'\bmal servicio\b',
            r'\bno estoy satisfecho\b', r'\bqueja\b',
        ],
        'description': 'Escalation or complaint'
    },
    'closing': {
        'indicators': ['final messages', 'thank you', 'goodbye'],
        'patterns': [
            r'\bgracias\b', r'\bhasta luego\b', r'\bcualquier duda\b',
            r'\bquedamos pendientes\b', r'\bexcelente\b',
        ],
        'description': 'Final closing messages'
    },
}


def classify_scenario(turns: List[Dict]) -> Tuple[str, float]:
    """
    Classify conversation scenario based on turns.
    Returns: (scenario_name, confidence)
    """
    scenario_scores = {}
    total_matches = 0
    
    # Collect all text from all turns
    all_text = ' '.join([turn.get('text', '') for turn in turns]).lower()
    
    # Score each scenario
    for scenario_name, scenario_def in SCENARIOS.items():
        score = 0
        
        # Check keywords
        for keyword in scenario_def['keywords']:
            matches = len(re.findall(keyword, all_text, re.IGNORECASE))
            score += matches
        
        # Check patterns
        for pattern in scenario_def['patterns']:
            if re.search(pattern, all_text, re.IGNORECASE):
                score += 2  # Patterns are weighted higher
        
        if score > 0:
            scenario_scores[scenario_name] = score
            total_matches += score
    
    if not scenario_scores:
        return ('unknown', 0.0)
    
    # Get scenario with highest score
    best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
    confidence = min(best_scenario[1] / max(total_matches, 1), 1.0)
    
    return (best_scenario[0], confidence)


def classify_stage(turn: Dict, turn_idx: int, total_turns: int) -> str:
    """
    Classify stage for a single turn.
    Returns: stage_name
    """
    text = turn.get('text', '').lower()
    role = turn.get('role', 'unknown')
    
    # Position-based heuristics
    if turn_idx == 0:
        return 'opening'
    if turn_idx >= total_turns - 2:
        # Check if it's closing or resolution
        if any(re.search(pattern, text) for pattern in STAGES['closing']['patterns']):
            return 'closing'
        if any(re.search(pattern, text) for pattern in STAGES['resolution']['patterns']):
            return 'resolution'
        return 'closing'
    
    # Keyword-based detection for middle stages
    stage_scores = {}
    
    for stage_name, stage_def in STAGES.items():
        if stage_name in ['opening', 'closing']:  # Skip, handled by position
            continue
        
        score = 0
        for pattern in stage_def['patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        
        if score > 0:
            stage_scores[stage_name] = score
    
    if stage_scores:
        return max(stage_scores.items(), key=lambda x: x[1])[0]
    
    # Default based on position
    if turn_idx < total_turns * 0.2:
        return 'info_gathering'
    elif turn_idx < total_turns * 0.6:
        return 'scheduling'
    else:
        return 'waiting_status_loop'


def main():
    """Main function to build taxonomy and label conversations."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_post_sales_turns.json"
    output_taxonomy = base_dir / "out" / "taxonomy.json"
    output_labels = base_dir / "out" / "labels.jsonl"
    
    # Load dataset
    print(f"Loading dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Processing {len(conversations)} conversations...")
    
    # Classify each conversation
    labels = []
    stage_distributions = {}
    
    for conv in conversations:
        conv_id = conv['conversation_id']
        turns = conv.get('turns', [])
        
        if not turns:
            continue
        
        # Classify scenario
        scenario, scenario_confidence = classify_scenario(turns)
        
        # Classify stages for each turn
        turn_stages = []
        for turn_idx, turn in enumerate(turns):
            stage = classify_stage(turn, turn_idx, len(turns))
            turn_stages.append(stage)
        
        # Calculate stage distribution
        stage_dist = Counter(turn_stages)
        
        label_entry = {
            'conversation_id': conv_id,
            'scenario': scenario,
            'scenario_confidence': round(scenario_confidence, 3),
            'stages': turn_stages,
            'stage_distribution': dict(stage_dist)
        }
        
        labels.append(label_entry)
        
        # Update stage distributions
        for stage, count in stage_dist.items():
            stage_distributions[stage] = stage_distributions.get(stage, 0) + count
    
    # Save taxonomy
    taxonomy = {
        'scenarios': SCENARIOS,
        'stages': STAGES,
        'metadata': {
            'total_conversations': len(labels),
            'scenario_distribution': dict(Counter([l['scenario'] for l in labels])),
            'stage_distribution': stage_distributions
        }
    }
    
    with open(output_taxonomy, 'w', encoding='utf-8') as f:
        json.dump(taxonomy, f, ensure_ascii=False, indent=2)
    
    # Save labels (JSONL format)
    with open(output_labels, 'w', encoding='utf-8') as f:
        for label in labels:
            f.write(json.dumps(label, ensure_ascii=False) + '\n')
    
    # Print summary
    scenario_counts = Counter([l['scenario'] for l in labels])
    unknown_count = scenario_counts.get('unknown', 0)
    unknown_rate = unknown_count / len(labels) if labels else 0
    
    print(f"\n✅ Taxonomy built!")
    print(f"\nSummary:")
    print(f"  Total conversations labeled: {len(labels)}")
    print(f"  Scenario distribution:")
    for scenario, count in sorted(scenario_counts.items(), key=lambda x: -x[1]):
        pct = count / len(labels) * 100 if labels else 0
        print(f"    {scenario}: {count} ({pct:.1f}%)")
    print(f"  Unknown scenarios: {unknown_count} ({unknown_rate*100:.1f}%)")
    print(f"  Stage distribution:")
    for stage, count in sorted(stage_distributions.items(), key=lambda x: -x[1]):
        print(f"    {stage}: {count}")
    
    print(f"\nOutput files:")
    print(f"  {output_taxonomy}")
    print(f"  {output_labels}")


if __name__ == "__main__":
    main()
