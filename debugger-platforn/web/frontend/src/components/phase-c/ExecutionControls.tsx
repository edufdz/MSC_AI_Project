import { Slider, Toggle, NumberInput, Select, Section } from '../shared/ControlPanel'

interface ExecutionControlsProps {
  mock: boolean
  workers: number
  count: number
  aiPersonas: boolean
  traces: boolean
  failRate: number
  seed: number | null
  language: string
  onMockChange: (v: boolean) => void
  onWorkersChange: (v: number) => void
  onCountChange: (v: number) => void
  onAiPersonasChange: (v: boolean) => void
  onTracesChange: (v: boolean) => void
  onFailRateChange: (v: number) => void
  onSeedChange: (v: number | null) => void
  onLanguageChange: (v: string) => void
}

export default function ExecutionControls(props: ExecutionControlsProps) {
  return (
    <div className="space-y-6">
      <Section title="Connector">
        <div className="flex gap-2">
          <button
            onClick={() => props.onMockChange(true)}
            className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-all duration-200 ${
              props.mock
                ? 'bg-graphite/80 border-platinum/30 text-pearl'
                : 'border-border text-text-muted hover:bg-bg-card'
            }`}
          >
            Mock
          </button>
          <button
            onClick={() => props.onMockChange(false)}
            className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-all duration-200 ${
              !props.mock
                ? 'bg-graphite/80 border-platinum/30 text-pearl'
                : 'border-border text-text-muted hover:bg-bg-card'
            }`}
          >
            Real API
          </button>
        </div>
      </Section>

      <Section title="Execution">
        <Slider label="Workers" value={props.workers} min={1} max={50} onChange={props.onWorkersChange} />
        <Slider label="Test Count Limit" value={props.count} min={0} max={500} step={10} onChange={props.onCountChange} />
        <Toggle label="AI Personas" checked={props.aiPersonas} onChange={props.onAiPersonasChange} description="Use AI for persona messages (costs $)" />
        <Toggle label="Enable Traces" checked={props.traces} onChange={props.onTracesChange} description="Save per-test trace files" />
      </Section>

      {props.mock && (
        <Section title="Mock Settings">
          <Slider label="Fail Rate" value={props.failRate} min={0} max={1} step={0.01} onChange={props.onFailRateChange} />
        </Section>
      )}

      <Section title="Options">
        <NumberInput label="Random Seed" value={props.seed} onChange={props.onSeedChange} />
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
