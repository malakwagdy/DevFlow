import Icon from './Icon';

/** Inline notification banner with optional action. tone: warning */
export default function Alert({ tone = 'warning', icon = 'warning', title, children, action }) {
  return (
    <div className={`alert alert--${tone}`} role="status">
      <Icon name={icon} className="alert__icon" />
      <div className="alert__body">
        <div className="alert__title">{title}</div>
        <div className="alert__message">{children}</div>
      </div>
      {action}
    </div>
  );
}
