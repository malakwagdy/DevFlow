import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import FrameworkSection from './FrameworkSection';
import ModulesSection from './ModulesSection';
import PipelineModeSection from './PipelineModeSection';
import ProjectSpecSection from './ProjectSpecSection';
import SourceSection from './SourceSection';
import { ROUTES } from '../../config/navigation';

export default function NewProjectForm({ options }) {
  const navigate = useNavigate();
  const { defaults } = options;

  const [name, setName] = useState(defaults.name);
  const [environment, setEnvironment] = useState(options.environments[0].value);
  const [source, setSource] = useState('github');
  const [repository, setRepository] = useState(options.repositories[0].value);
  const [branch, setBranch] = useState(options.branches[0]);
  const [code, setCode] = useState(defaults.entrypoint);
  const [framework, setFramework] = useState(defaults.framework);
  const [modules, setModules] = useState(
    () => new Set(options.modules.filter((module) => module.enabled).map((module) => module.id)),
  );
  const [pipelineMode, setPipelineMode] = useState('standard');

  const toggleModule = (id, checked) => {
    setModules((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    navigate(ROUTES.dashboard);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-stack">
        <ProjectSpecSection
          name={name}
          onNameChange={setName}
          domain={`${name}${defaults.domainSuffix}`}
          environment={environment}
          environments={options.environments}
          onEnvironmentChange={setEnvironment}
        />
        <SourceSection
          source={source}
          onSourceChange={setSource}
          repositories={options.repositories}
          repository={repository}
          onRepositoryChange={setRepository}
          branches={options.branches}
          branch={branch}
          onBranchChange={setBranch}
          code={code}
          onCodeChange={setCode}
        />
        <FrameworkSection
          frameworks={options.frameworks}
          value={framework}
          onChange={setFramework}
          notice={options.frameworkNotice}
        />
        <ModulesSection modules={options.modules} selected={modules} onToggle={toggleModule} />
        <PipelineModeSection
          mode={pipelineMode}
          onModeChange={setPipelineMode}
          stages={options.stages}
          script={options.pipelineScript}
        />
      </div>

      {/* Sticky bottom action bar */}
      <div className="action-bar">
        <div className="action-bar__inner">
          <div className="action-bar__note">
            Estimated first build duration: <strong>{options.estimatedFirstBuild}</strong>
          </div>
          <div className="action-bar__actions">
            <Button variant="ghost" to={ROUTES.projects}>
              Cancel
            </Button>
            <Button type="submit" icon="rocket_launch" className="btn--wide">
              Create &amp; Trigger First Deploy
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}
