import Card from '../ui/Card';
import Icon from '../ui/Icon';
import StageFlow from '../ui/StageFlow';

function StageCard({ name, meta, icon }) {
  return (
    <div className="stage-card">
      <div>
        <div className="stage-card__name">{name}</div>
        <div className="stage-card__meta">{meta}</div>
      </div>
      <Icon name={icon} size="sm" />
    </div>
  );
}

export default function StageProgress({ stages, summary }) {
  return (
    <Card shadow>
      <div className="stage-progress__head">
        <span className="eyebrow text-muted">Pipeline Stage Progression</span>
        <span className="stage-progress__summary">{summary}</span>
      </div>
      <div className="stage-cards">
        <StageFlow items={stages} getKey={(stage) => stage.name} renderItem={(stage) => <StageCard {...stage} />} />
      </div>
    </Card>
  );
}
