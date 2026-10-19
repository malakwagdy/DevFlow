/**
 * Maps a workload/job status to its display label and color tone.
 * `tone` drives badges, `iconTone` colors the project icon in tables.
 */
export const STATUS_CONFIG = {
  running: { label: 'Running', tone: 'success', iconTone: 'primary' },
  deploying: { label: 'Deploying', tone: 'info', iconTone: 'secondary', pulse: true },
  failed: { label: 'Failed', tone: 'danger', iconTone: 'error' },
  stopped: { label: 'Stopped', tone: 'neutral', iconTone: 'outline' },
  success: { label: 'Success', tone: 'success' },
  passing: { label: 'Passing', tone: 'success' },
};

export function getStatus(status) {
  return STATUS_CONFIG[status] ?? { label: status, tone: 'neutral', iconTone: 'outline' };
}
