import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

export default function ResourceUsage({ resources }) {
  return (
    <Card padding="md" className="span-lg-2">
      <h3 className="panel-title">Replica Resource Utilization</h3>
      <div className="stack stack--md">
        {resources.map((resource) => (
          <ProgressBar key={resource.label} {...resource} />
        ))}
      </div>
    </Card>
  );
}
