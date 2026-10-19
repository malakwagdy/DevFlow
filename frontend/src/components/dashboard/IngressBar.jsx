import Button from '../ui/Button';
import CopyButton from '../ui/CopyButton';
import Icon from '../ui/Icon';
import { confirmAction, notify } from '../../utils/notify';
import { ROUTES } from '../../config/navigation';

/** Canonical URL bar with copy/open tools and the Redeploy / Settings / Stop quick actions. */
export default function IngressBar({ service }) {
  const openLiveUrl = (event) => {
    event.preventDefault();
    notify('Navigating to simulated ingress live URL!');
  };

  return (
    <div className="url-bar">
      <div className="url-bar__main">
        <div className="url-bar__icon">
          <Icon name="public" />
        </div>
        <div className="url-bar__text">
          <div className="url-bar__label">Canonical Ingress URL</div>
          <div className="url-bar__url">{service.url}</div>
        </div>
        <div className="url-bar__tools">
          <CopyButton text={service.url} message="Copied URL to clipboard!" iconSize="sm" />
          <a href={service.url} className="icon-btn" onClick={openLiveUrl} title="Open in new tab" aria-label="Open in new tab">
            <Icon name="open_in_new" size="sm" />
          </a>
        </div>
      </div>

      <div className="button-row">
        <Button size="xs" icon="refresh" to={ROUTES.job}>
          Redeploy
        </Button>
        <Button size="xs" variant="ghost" icon="settings" onClick={() => notify('Opening workload settings modal')}>
          Settings
        </Button>
        <Button
          size="xs"
          variant="danger"
          icon="stop_circle"
          onClick={() => confirmAction(`Stop all running ${service.name} containers?`)}
        >
          Stop
        </Button>
      </div>
    </div>
  );
}
