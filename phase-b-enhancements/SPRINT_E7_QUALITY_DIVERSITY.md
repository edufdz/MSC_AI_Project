# Sprint E7 — Quality-Diversity Persona/Scenario Selection

## Goal

Replace the 0.85 cosine dedup with a MAP-Elites-style archive over behavioural descriptors (e.g., formality × emotional_volatility × edge_behaviour_count), keeping the most failure-revealing persona per cell. Optionally use a determinantal point process for diverse final selection within budget.

**Literature**: MAP-Elites (Mouret & Clune) explicitly optimises for behavioural coverage rather than mere deduplication. Rainbow Teaming (Samvelyan et al., 2024) uses quality-diversity for diverse adversarial prompts. Determinantal point processes (Kulesza & Taskar) are the principled model for diverse subset selection.

## Tasks

### E7.1 MAP-Elites Archive

**File**: `src/personas/quality_diversity.py` (new file)

- [ ] Define behavioural descriptors (the archive dimensions):
  ```python
  DESCRIPTOR_DIMENSIONS = [
      ("formality_axis", lambda p: {"formal": 0, "casual": 1, "slang": 2}[p.style.formality]),
      ("volatility_axis", lambda p: 0 if p.traits.emotional_volatility <= 3 else (1 if p.traits.emotional_volatility <= 7 else 2)),
      ("edge_count", lambda p: sum([p.edge_behaviors.rage_quits, p.edge_behaviors.changes_mind, p.edge_behaviors.provides_incomplete_info, p.edge_behaviors.asks_off_topic, p.edge_behaviors.tests_boundaries])),
      ("tech_axis", lambda p: 0 if p.traits.tech_savviness <= 3 else (1 if p.traits.tech_savviness <= 7 else 2)),
  ]
  # Archive cells: 3 × 3 × 6 × 3 = 162 cells
  ```

- [ ] Implement `MAPElitesArchive`:
  ```python
  class MAPElitesArchive:
      def __init__(self, dimensions):
          self.grid: dict[tuple, Persona] = {}
          self.dimensions = dimensions
      
      def add(self, persona: Persona, quality: float = 0.0):
          cell = self._cell(persona)
          if cell not in self.grid or quality > self.grid[cell].quality:
              self.grid[cell] = persona
      
      def coverage(self) -> float:
          return len(self.grid) / self._total_cells()
      
      def select_diverse(self, n: int) -> list[Persona]:
          # Return n personas maximising cell coverage
  ```

### E7.2 Replace Cosine Dedup

**File**: `src/personas/builder.py`

- [ ] Replace `_is_duplicate()` cosine check with MAP-Elites archive insertion:
  - When adding a persona, insert into archive
  - If the cell is already occupied by a higher-quality persona, reject
  - Quality metric: sum of edge behaviours + abs(5 - patience) (more extreme = higher quality for testing)

### E7.3 Scenario Diversity Archive

**File**: `src/scenarios/quality_diversity.py` (new file)

- [ ] Apply MAP-Elites to scenarios with descriptors:
  - (type: happy/error/edge) × (difficulty: easy/medium/hard) × (variant_type: 7 types) × (tool_count: 0/1/2/3+)
  - Keep most failure-revealing scenario per cell

### E7.4 DPP Final Selection (Optional)

**File**: `src/generator/diversity_selection.py` (new file)

- [ ] Implement `dpp_select(items: list, kernel_fn, budget: int) -> list`:
  - Greedy determinantal point process selection
  - Kernel: similarity matrix from trait/scenario features
  - Returns maximally diverse subset of size `budget`

## Files Created/Modified

| File | Changes |
|------|---------|
| `src/personas/quality_diversity.py` | **New file**: MAP-Elites archive for personas |
| `src/scenarios/quality_diversity.py` | **New file**: MAP-Elites archive for scenarios |
| `src/generator/diversity_selection.py` | **New file**: DPP diverse selection |
| `src/personas/builder.py` | Replace cosine dedup with archive insertion |

## Done When

- MAP-Elites archive tracks persona coverage across behavioural dimensions
- Archive coverage metric reported alongside existing diversity score
- Scenario archive ensures variant-type × difficulty × tool-count coverage
- Diversity score measurably higher than cosine-dedup baseline
