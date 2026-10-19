import { useState } from 'react';
import Page from '../components/layout/Page';
import PageHeader from '../components/layout/PageHeader';
import ProjectFilters, { filterProjects } from '../components/projects/ProjectFilters';
import ProjectsTable from '../components/projects/ProjectsTable';
import WorkspaceSideNav from '../components/projects/WorkspaceSideNav';
import AsyncContent from '../components/ui/AsyncContent';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { ROUTES } from '../config/navigation';
import { useSession } from '../context/SessionContext';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

const INITIAL_FILTERS = { query: '', status: 'all', framework: 'all' };

export default function ProjectsPage() {
  const { workspace } = useSession();
  const state = useApi(api.getProjects);
  const [showEmptyState, setShowEmptyState] = useState(false);
  const [filters, setFilters] = useState(INITIAL_FILTERS);

  return (
    <Page variant="sidebar">
      <WorkspaceSideNav workspace={workspace} />

      <main className="page-main">
        <div className="container container--6xl stack">
          <PageHeader
            title="Production Workloads"
            description="Active web services, workers, and continuous deployment triggers."
            actions={
              <>
                <Button variant="outline" size="xs" className="btn--muted" onClick={() => setShowEmptyState((v) => !v)}>
                  {showEmptyState ? 'Restore Projects Table' : 'Toggle Empty State'}
                </Button>
                <Button icon="add" iconSize="base" to={ROUTES.newProject}>
                  New project
                </Button>
              </>
            }
          />

          <AsyncContent state={state}>
            {(data) => (
              <>
                <ProjectFilters filters={filters} options={data.filters} onChange={setFilters} />
                {showEmptyState ? (
                  <EmptyState
                    icon="rocket"
                    title="No services found"
                    description={`You haven't provisioned any pipelines in the ${workspace?.name ?? ''} workspace yet.`}
                    action={
                      <Button icon="add" to={ROUTES.newProject}>
                        Create your first project
                      </Button>
                    }
                  />
                ) : (
                  <ProjectsTable projects={filterProjects(data.projects, filters)} />
                )}
              </>
            )}
          </AsyncContent>
        </div>
      </main>
    </Page>
  );
}
