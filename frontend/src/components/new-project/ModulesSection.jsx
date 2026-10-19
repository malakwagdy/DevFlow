import CheckboxCard from '../ui/CheckboxCard';
import FormSection from './FormSection';

export default function ModulesSection({ modules, selected, onToggle }) {
  return (
    <FormSection
      step={4}
      title="Managed Infrastructure Modules"
      description="Provision collocated stateful engines with automatic connection strings."
    >
      <div className="check-grid">
        {modules.map((module) => (
          <CheckboxCard
            key={module.id}
            title={module.name}
            description={module.description}
            checked={selected.has(module.id)}
            onChange={(checked) => onToggle(module.id, checked)}
          />
        ))}
      </div>
    </FormSection>
  );
}
