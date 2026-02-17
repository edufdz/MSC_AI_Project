import { Slider, Toggle, NumberInput, Select, Section } from '../shared/ControlPanel'

interface GenerationControlsProps {
  count: number
  personaCount: number
  scenarioCount: number
  variants: number
  skipAi: boolean
  seed: number | null
  language: string
  useTlahuac: boolean
  tlahuacDir: string
  onCountChange: (v: number) => void
  onPersonaCountChange: (v: number) => void
  onScenarioCountChange: (v: number) => void
  onVariantsChange: (v: number) => void
  onSkipAiChange: (v: boolean) => void
  onSeedChange: (v: number | null) => void
  onLanguageChange: (v: string) => void
  onUseTlahuacChange: (v: boolean) => void
  onTlahuacDirChange: (v: string) => void
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
          label="Skip AI Generation"
          checked={props.skipAi}
          onChange={props.onSkipAiChange}
          description="Offline mode — no API key needed"
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

      <Section title="Tlahuac Data">
        <Toggle
          label="Use Tlahuac Data"
          checked={props.useTlahuac}
          onChange={props.onUseTlahuacChange}
          description="Load personas and scenarios from tlahuac pack"
        />
        {props.useTlahuac && (
          <div className="space-y-1">
            <label className="text-sm text-smoke">Tlahuac Directory</label>
            <input
              type="text"
              value={props.tlahuacDir}
              onChange={(e) => props.onTlahuacDirChange(e.target.value)}
              placeholder="Auto-detect or specify path"
              className="w-full px-3 py-2 text-sm bg-bg-card border border-border rounded-lg text-pearl font-mono focus:outline-none focus:border-platinum transition-colors"
            />
          </div>
        )}
      </Section>
    </div>
  )
}
