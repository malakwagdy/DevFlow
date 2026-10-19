import CodeBlock from '../ui/CodeBlock';
import SegmentedControl from '../ui/SegmentedControl';
import StageFlow from '../ui/StageFlow';
import StatusDot from '../ui/StatusDot';
import FormSection from './FormSection';

const MODE_OPTIONS = [
  { value: 'standard', label: 'Standard (Auto)' },
  { value: 'advanced', label: 'Advanced', badge: 'Beta' },
];

export default function PipelineModeSection({ mode, onModeChange, stages, script }) {
  return (
    <FormSection
      step={5}
      title="Pipeline Topology Mode"
      description="Choose between fully automated autonomous deployment or manual declarative pipeline."
      actions={
        <SegmentedControl label="Pipeline mode" options={MODE_OPTIONS} value={mode} onChange={onModeChange} />
      }
    >
      {mode === 'standard' ? (
        <div className="stage-strip">
          <div className="stage-strip__label">Synthesized Pipeline Stages</div>
          <div className="stage-strip__list">
            <StageFlow
              items={stages}
              getKey={(stage) => stage}
              renderItem={(stage) => (
                <span className="stage-chip">
                  <StatusDot tone="tertiary" size="md" />
                  {stage}
                </span>
              )}
            />
          </div>
        </div>
      ) : (
        <div className="code-panel">
          <div className="code-panel__header">
            <span className="code-panel__filename">pipeline.yaml / Jenkinsfile definition</span>
            <span className="code-panel__status">Syntax Validated</span>
          </div>
          <CodeBlock code={script} />
        </div>
      )}
    </FormSection>
  );
}
