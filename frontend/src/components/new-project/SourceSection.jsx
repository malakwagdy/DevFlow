import { useId } from 'react';
import FormField from '../ui/FormField';
import SegmentedControl from '../ui/SegmentedControl';
import Select from '../ui/Select';
import FormSection from './FormSection';

const SOURCE_OPTIONS = [
  { value: 'github', label: 'Link GitHub Repo' },
  { value: 'paste', label: 'Paste Code Directly' },
];

export default function SourceSection({ source, onSourceChange, repositories, repository, onRepositoryChange, branches, branch, onBranchChange, code, onCodeChange }) {
  const repoId = useId();
  const branchId = useId();
  const codeId = useId();

  return (
    <FormSection step={2} title="Code Source Ingestion">
      <div className="tab-bar">
        <SegmentedControl
          variant="pills"
          label="Code source"
          options={SOURCE_OPTIONS}
          value={source}
          onChange={onSourceChange}
        />
      </div>

      {source === 'github' ? (
        <div className="form-grid form-grid--3">
          <FormField label="Select Git Repository" htmlFor={repoId} className="form-grid__span-2">
            <Select
              id={repoId}
              mono
              options={repositories}
              value={repository}
              onChange={(event) => onRepositoryChange(event.target.value)}
            />
          </FormField>
          <FormField label="Target Branch" htmlFor={branchId}>
            <Select
              id={branchId}
              mono
              options={branches}
              value={branch}
              onChange={(event) => onBranchChange(event.target.value)}
            />
          </FormField>
        </div>
      ) : (
        <FormField label="Inline Application Entrypoint (e.g., main.go or server.js)" htmlFor={codeId} className="field--mono">
          <textarea
            id={codeId}
            className="code-editor dark-scroll"
            rows={6}
            spellCheck={false}
            value={code}
            onChange={(event) => onCodeChange(event.target.value)}
          />
        </FormField>
      )}
    </FormSection>
  );
}
