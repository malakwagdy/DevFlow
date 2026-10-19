import Page from '../components/layout/Page';
import SubHeader from '../components/layout/SubHeader';
import NewProjectForm from '../components/new-project/NewProjectForm';
import AsyncContent from '../components/ui/AsyncContent';
import BackLink from '../components/ui/BackLink';
import { ROUTES } from '../config/navigation';
import { useSession } from '../context/SessionContext';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

export default function NewProjectPage() {
  const { workspace } = useSession();
  const state = useApi(api.getNewProjectOptions);

  return (
    <Page variant="muted">
      <SubHeader>
        <div>
          <BackLink to={ROUTES.projects}>Back to Projects</BackLink>
          <h1 className="subheader__title">Provision New Workload</h1>
        </div>
        <span className="subheader__meta">
          Cluster: <strong>{workspace?.cluster ?? '…'}</strong>
        </span>
      </SubHeader>

      <AsyncContent state={state}>{(options) => <NewProjectForm options={options} />}</AsyncContent>
    </Page>
  );
}
