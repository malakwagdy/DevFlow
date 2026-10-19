import { useId } from 'react';
import FormField from '../ui/FormField';
import Select from '../ui/Select';
import FormSection from './FormSection';

export default function ProjectSpecSection({ name, onNameChange, domain, environment, environments, onEnvironmentChange }) {
  const nameId = useId();
  const environmentId = useId();

  return (
    <FormSection step={1} title="Project Specification">
      <div className="form-grid form-grid--2">
        <FormField label="Workload Identifier" htmlFor={nameId} hint={`Live domain: ${domain}`}>
          <input
            id={nameId}
            type="text"
            className="input input--mono"
            value={name}
            onChange={(event) => onNameChange(event.target.value)}
          />
        </FormField>
        <FormField label="Target Environment" htmlFor={environmentId}>
          <Select
            id={environmentId}
            options={environments}
            value={environment}
            onChange={(event) => onEnvironmentChange(event.target.value)}
          />
        </FormField>
      </div>
    </FormSection>
  );
}
