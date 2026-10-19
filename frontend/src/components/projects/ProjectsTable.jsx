import { Link, useNavigate } from 'react-router-dom';
import CopyButton from '../ui/CopyButton';
import DataTable from '../ui/DataTable';
import Icon from '../ui/Icon';
import StatusBadge from '../ui/StatusBadge';
import { getStatus } from '../../utils/status';
import { routeFor } from '../../config/navigation';

const COLUMNS = [
  {
    key: 'project',
    header: 'Project',
    render: (project) => (
      <>
        <div className="project-name">
          <Icon name="view_in_ar" size="base" className={`text-${getStatus(project.status).iconTone}`} />
          {project.name}
        </div>
        <div className="project-meta">
          {project.branch} (commit #{project.commit})
        </div>
      </>
    ),
  },
  {
    key: 'framework',
    header: 'Framework',
    render: (project) => <span className="tag tag--strong">{project.framework}</span>,
  },
  {
    key: 'status',
    header: 'Status',
    render: (project) => <StatusBadge status={project.status} />,
  },
  {
    key: 'url',
    header: 'Monospace URL',
    render: (project) =>
      project.url ? (
        <div className="url-cell">
          <span className="url-cell__text">{project.url}</span>
          <CopyButton text={project.url} message="Monospace URL Copied!" bare stopPropagation />
        </div>
      ) : (
        <span className="text-placeholder">{project.urlPlaceholder}</span>
      ),
  },
  {
    key: 'lastDeployed',
    header: 'Last Deployed',
    className: 'cell-muted',
    render: (project) => project.lastDeployed,
  },
  {
    key: 'actions',
    header: 'Actions',
    align: 'right',
    stopPropagation: true,
    render: (project) => (
      <Link to={routeFor(project.action.target)} className={`link-btn link-btn--${project.action.tone}`}>
        {project.action.label}
      </Link>
    ),
  },
];

export default function ProjectsTable({ projects }) {
  const navigate = useNavigate();

  return (
    <div className="table-card">
      <div className="table-scroll">
        <DataTable
          columns={COLUMNS}
          rows={projects}
          getRowKey={(project) => project.id}
          onRowClick={(project) => navigate(routeFor(project.target))}
          emptyMessage="No projects match the current filters."
        />
      </div>
    </div>
  );
}
