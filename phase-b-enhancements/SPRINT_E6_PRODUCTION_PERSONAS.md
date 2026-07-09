# Sprint E6 — Production-Grounded Personas

## Goal

Fit the 10-trait and style distributions to Langfuse production traces (formality, typo rate, emoji, verbosity, code-switching, language proficiency), and add trace-derived personas as a sixth persona source so that the persona population matches the real user population. This replaces hand-authored trait vectors with empirically grounded distributions.

**Literature**: Simulators overfitted to hand-written rules fail to transfer to real humans (Gao et al., Neural Approaches to Conversational AI). LLM-based simulators improve realism but suffer persona drift unless grounded. SimGym (2026) grounds synthetic buyers in production clickstreams and reports directional correlation with observed human outcomes.

## Tasks

### E6.1 Trace-to-Trait Analyser

**File**: `src/personas/trace_grounding.py` (new file)

- [ ] Implement `analyse_user_traits(conversations: list) -> dict`:
  - For each conversation's user messages:
    - **Formality**: count usted/tú indicators → formal/casual/slang
    - **Verbosity**: average word count per message → scale 1-10
    - **Typo rate**: character-level error ratio (repeated chars, missing accents) → 0.0-1.0
    - **Emoji use**: emoji count / message count → none/rare/moderate/frequent
    - **Patience**: number of turns before escalation or abandonment → scale 1-10
    - **Language proficiency**: grammar error ratio, code-switching frequency → scale 1-10
    - **Emotional volatility**: sentiment variance across messages → scale 1-10
    - **Tech savviness**: use of technical terms, order number formats → scale 1-10
  - Return distribution statistics: mean, std, percentiles per trait

- [ ] Implement `fit_trait_distributions(conversations) -> dict[str, tuple[float, float]]`:
  - Returns mean and std for each of the 10 PersonaTraits dimensions
  - Plus style distribution (formality %, typo_rate mean, emoji_use %)

### E6.2 Production-Distribution Persona Generator

**File**: `src/personas/trace_grounding.py`

- [ ] Implement `sample_production_personas(distributions: dict, count: int, seed: int = 42) -> list[Persona]`:
  - Sample from the fitted distributions (truncated normal, clipped to 1-10)
  - Each persona's traits match the real population statistics
  - Set `source = "production_grounded"`
  - Assign realistic names from the cultural distribution (Mexican-Spanish for Samsung)

### E6.3 Integrate into B2

**File**: `src/personas/builder.py`

- [ ] Add method `generate_production_grounded_personas(trace_result, count: int = 5) -> list[Persona]`:
  - Calls `analyse_user_traits(trace_result.conversations)`
  - Calls `fit_trait_distributions()`
  - Calls `sample_production_personas()`
  - Appends to self.personas

- [ ] Wire into `generate_tests.py`:
  ```python
  if trace_result and trace_result.conversations:
      production_personas = persona_builder.generate_production_grounded_personas(trace_result, count=5)
  ```

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/personas/trace_grounding.py` | **New file**: trait analyser, distribution fitting, persona sampling |
| `src/personas/builder.py` | New `generate_production_grounded_personas()` |
| `generate_tests.py` | Wire production persona generation when traces available |

## Done When

- Trace analysis extracts formality, verbosity, patience, etc. from real conversations
- Distribution fitting produces mean/std for each trait dimension
- Sampled personas match the real user population statistics
- Production-grounded personas appear in persona library with source="production_grounded"
- Measurement harness (E12) shows diversity improvement vs hand-authored personas only
