import { Link, useNavigate } from 'react-router-dom';
import DataTable from '../ui/DataTable';
import StatusBadge from '../ui/StatusBadge';
import cx from '../../utils/classNames';
import { ROUTES } from '../../config/navigation';

const COLUMNS = [
  {
    key: 'run',
    header: 'Run #',
    className: 'cell-strong',
    render: (run) => (
      <span className={cx(run.latest ? 'text-primary' : 'text-on-surface')}>
        #{run.run}
        {run.latest && ' (Latest)'}
      </span>
    ),
  },
  {
    key: 'trigger',
    header: 'Trigger / Commit',
    className: 'cell-body',
    render: (run) => (
      <>
        {run.message} (<code>{run.commit}</code>)
      </>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    render: (run) => <StatusBadge status={run.status} label={run.statusLabel} />,
  },
  { key: 'duration', header: 'Duration', render: (run) => run.duration },
  { key: 'finished', header: 'Finished', className: 'cell-body cell-muted', render: (run) => run.finished },
  {
    key: 'details',
    header: 'Details',
    align: 'right',
    className: 'cell-body cell-medium',
    render: (run) =>
      run.status === 'failed' ? (
        <span className="text-error">Logs →</span>
      ) : (
        <span className="text-primary">Inspect →</span>
      ),
  },
];

export default function ExecutionHistory({ executions }) {
  const navigate = useNavigate();

  return (
    <div className="card card--clip">
      <div className="card__header">
        <h3 className="panel-title panel-title--flush">Execution History</h3>
        <Link to={ROUTES.job} className="link-btn link-btn--primary">
          View All Deployments
        </Link>
      </div>
      <div className="table-scroll">
        <DataTable
          variant="compact"
          columns={COLUMNS}
          rows={executions}
          getRowKey={(run) => run.run}
          onRowClick={() => navigate(ROUTES.job)}
        />
      </div>
    </div>
  );
}
