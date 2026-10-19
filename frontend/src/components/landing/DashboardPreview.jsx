import { Link } from 'react-router-dom';
import Icon from '../ui/Icon';
import MetricCard from '../ui/MetricCard';
import StageFlow from '../ui/StageFlow';
import StatusDot from '../ui/StatusDot';
import cx from '../../utils/classNames';
import { ROUTES } from '../../config/navigation';

function PreviewStage({ stage }) {
  const running = stage.status === 'running';
  return (
    <div className={cx('preview-stage', running && 'preview-stage--running')}>
      <Icon
        name={running ? 'refresh' : 'check_circle'}
        spin={running}
        className={running ? 'text-primary' : 'text-tertiary'}
      />
      <span className="preview-stage__name">{stage.name}</span>
      <span className="preview-stage__time">{stage.duration}</span>
    </div>
  );
}

/** Mock "live dashboard" window shown in the landing hero. */
export default function DashboardPreview({ path, liveLabel, stats, stages, logsLinkLabel }) {
  return (
    <div className="preview-window">
      <div className="preview-window__bar">
        <div className="preview-window__title">
          <span className="window-dot" />
          <span className="window-dot" />
          <span className="window-dot" />
          <span className="preview-window__path">{path}</span>
        </div>
        <div className="preview-window__live">
          <StatusDot tone="tertiary-container" size="md" pulse />
          {liveLabel}
        </div>
      </div>

      <div className="preview-window__grid">
        {stats.map((stat) => (
          <MetricCard key={stat.label} variant="preview" {...stat} />
        ))}

        <div className="preview-stages">
          <StageFlow
            items={stages}
            getKey={(stage) => stage.name}
            renderItem={(stage) => <PreviewStage stage={stage} />}
          />
          <Link to={ROUTES.job} className="preview-stages__link">
            {logsLinkLabel}
          </Link>
        </div>
      </div>
    </div>
  );
}
