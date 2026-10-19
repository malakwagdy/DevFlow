import ChoiceCard from '../ui/ChoiceCard';
import Icon from '../ui/Icon';
import FormSection from './FormSection';

export default function FrameworkSection({ frameworks, value, onChange, notice }) {
  return (
    <FormSection
      step={3}
      title="Framework & Compiler Runtime"
      description="DevFlow synthesizes an optimized container layer based on the detected runtime."
    >
      <div className="choice-grid" role="radiogroup" aria-label="Framework">
        {frameworks.map((framework) => (
          <ChoiceCard
            key={framework.id}
            name="framework"
            value={framework.id}
            checked={value === framework.id}
            onChange={onChange}
            title={framework.name}
            description={framework.description}
          />
        ))}
      </div>
      <div className="notice">
        <Icon name="info" size="sm" className="text-primary" />
        <span>{notice}</span>
      </div>
    </FormSection>
  );
}
