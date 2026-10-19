import Button from './Button';
import Icon from './Icon';

/**
 * Renders a loading / error state for a `useApi` result, or calls
 * `children(data)` once the data has arrived.
 */
export default function AsyncContent({ state, children, loadingLabel = 'Loading…' }) {
  if (state.loading) {
    return (
      <div className="async-state" role="status">
        <span className="spinner" aria-hidden="true" />
        {loadingLabel}
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="async-state async-state--error" role="alert">
        <Icon name="error" />
        <span>{state.error.message || 'Something went wrong.'}</span>
        <Button variant="ghost" size="xs" onClick={state.reload}>
          Retry
        </Button>
      </div>
    );
  }

  return children(state.data);
}
