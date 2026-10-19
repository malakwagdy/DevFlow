import SubHeader from '../layout/SubHeader';
import BackLink from '../ui/BackLink';
import Button from '../ui/Button';
import StatusBadge from '../ui/StatusBadge';
import { notify } from '../../utils/notify';
import { ROUTES } from '../../config/navigation';

export default function JobHeader({ job }) {
  return (
    <SubHeader width="wide">
      <div>
        <div className="breadcrumbs">
          <BackLink to={ROUTES.dashboard} className="back-link--inline">
            {job.service}
          </BackLink>
          <span className="breadcrumbs__separator">/</span>
          <span className="breadcrumbs__current">Job #{job.id}</span>
          <StatusBadge status={job.status} />
        </div>
        <h1 className="job-title">
          Execution #{job.id} — <span className="job-title__sub">{job.title}</span>
        </h1>
        <div className="meta-list">
          {job.meta.map((item) => (
            <span key={item.label}>
              {item.label}: <strong>{item.value}</strong>
            </span>
          ))}
        </div>
      </div>

      <div className="button-row">
        <Button
          size="xs"
          variant="outline"
          icon="replay"
          onClick={() => notify(`Re-running Job #${job.id} with cache purged!`)}
        >
          Re-run Job
        </Button>
        <Button size="xs" icon="visibility" to={ROUTES.dashboard}>
          View Live Service
        </Button>
      </div>
    </SubHeader>
  );
}
