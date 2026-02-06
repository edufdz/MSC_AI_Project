# Customer Policy Documentation

## Overview

The customer policy determines what action a simulated customer will take next based on the current conversation state. This creates realistic behavior patterns that match how real customers interact with dealerships.

## Customer Actions

### 1. answer_question
**Description**: Provide requested information to the dealership.

**When used**:
- Dealership asks a question (70% probability)
- During info_gathering stage
- Calm/cooperative personas

**Examples**:
- "50,000 km"
- "El modelo es Spark 2021"
- "Sí, tengo cuponera"
- "Se lo comparto en un momento"

### 2. ask_clarification
**Description**: Ask for clarification or more details about something.

**When used**:
- Dealership message is unclear (20% probability when question asked)
- During opening or info_gathering stages
- Confused/low-context personas

**Examples**:
- "¿Qué incluye el servicio?"
- "¿Cuánto tiempo tarda?"
- "¿Qué necesito llevar?"
- "No entiendo, ¿cómo funciona?"

### 3. ask_status
**Description**: Check on service status or timeline.

**When used**:
- During waiting_status_loop stage (60% probability)
- Impatient/urgent personas
- Late in conversation (>15 turns)

**Examples**:
- "¿Ya está listo?"
- "¿Para cuándo estará?"
- "¿Sigue en taller?"
- "¿Cuándo puedo pasar?"

### 4. reject_proposal
**Description**: Reject a proposed time slot or option.

**When used**:
- During scheduling stage (30% probability)
- Need-it-today personas
- Mid-conversation turns (5-15)

**Examples**:
- "No puedo a las 3pm"
- "Ese día no me funciona"
- "Prefiero otro horario"
- "Ese horario no me conviene"

### 5. provide_constraint
**Description**: Share budget, time, or location constraints.

**When used**:
- During info_gathering or scheduling stages
- Price-sensitive personas
- Need-it-today personas

**Examples**:
- "Mi presupuesto es $2000"
- "Solo puedo en las mañanas"
- "Vivo lejos"
- "Necesito que sea antes del viernes"

### 6. complain_escalate
**Description**: Express frustration or request escalation.

**When used**:
- During waiting_status_loop (30% probability)
- Angry/escalating personas
- Late in conversation
- After delays or issues

**Examples**:
- "Ya lleva mucho tiempo"
- "Quiero hablar con el gerente"
- "No estoy satisfecho"
- "Prometieron que estaría listo"

### 7. short_ack
**Description**: Brief acknowledgment.

**When used**:
- Ultra-short personas (high probability)
- During closing stage (80% probability)
- During resolution stage (70% probability)
- When dealership provides information

**Examples**:
- "Ok"
- "Va"
- "👍"
- "Gracias"
- "Perfecto"
- "Sí"

### 8. switch_topic
**Description**: Slight topic shift (common in real conversations).

**When used**:
- During closing stage (20% probability)
- Friendly/chatty personas
- After main topic resolved

**Examples**:
- "Otra cosa, ¿tienen refacciones?"
- "También necesito..."
- "Por cierto, ¿cuánto cuesta...?"

## Decision Logic

### Rule 1: Dealership Asked Question
If the dealership's last message was a question:
- 70% → answer_question (if info available)
- 20% → ask_clarification (if unclear)
- 10% → short_ack (if persona is ultra-short)

### Rule 2: By Stage
- **opening**: answer_question (40%), ask_clarification (40%), short_ack (20%)
- **info_gathering**: answer_question (60%), provide_constraint (30%), ask_clarification (10%)
- **scheduling**: answer_question (50%), reject_proposal (30%), provide_constraint (20%)
- **waiting_status_loop**: ask_status (60%), complain_escalate (30%), short_ack (10%)
- **resolution**: short_ack (70%), ask_status (20%), complain_escalate (10%)
- **closing**: short_ack (80%), switch_topic (20%)

### Rule 3: By Persona
Personas adjust base probabilities:
- **impatient_urgent**: +20% ask_status, +10% complain_escalate
- **angry_escalating**: +30% complain_escalate, -20% answer_question
- **ultra_short**: +30% short_ack, -20% answer_question
- **calm_cooperative**: +10% answer_question, -10% complain_escalate
- **price_sensitive**: +20% provide_constraint, +10% ask_clarification
- **need_it_today**: +20% reject_proposal, +10% provide_constraint, +10% complain_escalate
- **confused_low_context**: +30% ask_clarification, -10% answer_question
- **friendly_chatty**: +10% switch_topic, -10% short_ack

### Rule 4: By Turn Count
- **Early turns (<5)**: More answer_question, ask_clarification; less complain_escalate
- **Mid turns (5-15)**: Balanced
- **Late turns (>15)**: More ask_status, short_ack, complain_escalate; less answer_question

## Implementation

The policy is implemented in `scripts/18_customer_policy.py` with the `decide_action()` function. It uses weighted random selection based on the calculated probabilities.

## Quality Criteria

A good policy should:
- Sometimes generate short responses (short_ack)
- Sometimes push back (reject_proposal, complain_escalate)
- Sometimes repeat status follow-ups (ask_status in waiting_status_loop)
- Match actions to conversation context
- Feel realistic and varied
