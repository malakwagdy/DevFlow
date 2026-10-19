import StatusDot from './StatusDot';
import { getStatus } from '../../utils/status';

/** Pill showing a workload / job status, e.g. "● Running". `label` overrides the default text. */
export default function StatusBadge({ status, label }) {
  const config = getStatus(status);
  return (
    <span className={`badge badge--${config.tone}`}>
      <StatusDot pulse={config.pulse} />
      {label ?? config.label}
    </span>
  );
}
