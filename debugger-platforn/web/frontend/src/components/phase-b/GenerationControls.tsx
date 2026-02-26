import { Slider, Toggle, NumberInput, Select, Section } from '../shared/ControlPanel'

interface GenerationControlsProps {
  count: number
  personaCount: number
  scenarioCount: number
  variants: number
  includeTemplates: boolean
  seed: number | null
  language: string
  onCountChange: (v: number) => void
  onPersonaCountChange: (v: number) => void
  onScenarioCountChange: (v: number) => void
  onVariantsChange: (v: number) => void
  onIncludeTemplatesChange: (v: boolean) => void
  onSeedChange: (v: number | null) => void
  onLanguageChange: (v: string) => void
}

export default function GenerationControls(props: GenerationControlsProps) {
  return (
    <div className="space-y-6">
      <Section title="Test Generation">
        <Slider label="Test Count" value={props.count} min={10} max={1000} step={10} onChange={props.onCountChange} />
        <Slider label="Persona Count" value={props.personaCount} min={0} max={20} onChange={props.onPersonaCountChange} />
        <Slider label="Scenario Count" value={props.scenarioCount} min={0} max={50} onChange={props.onScenarioCountChange} />
        <Slider label="Variants per Scenario" value={props.variants} min={0} max={10} onChange={props.onVariantsChange} />
      </Section>

      <Section title="Options">
        <Toggle
          label="Include Template Personas"
          checked={props.includeTemplates}
          onChange={props.onIncludeTemplatesChange}
          description="Also create pre-built template personas (default: AI-only)"
        />
        <NumberInput label="Random Seed" value={props.seed} onChange={props.onSeedChange} placeholder="Optional" />
        <Select
          label="Language"
          value={props.language}
          options={[
            { value: '', label: 'Auto (from Agent Map)' },
            { value: 'English', label: 'English' },
            { value: 'Spanish', label: 'Spanish' },
          ]}
          onChange={props.onLanguageChange}
        />
      </Section>
    </div>
  )
}
