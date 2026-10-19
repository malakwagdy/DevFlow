import Icon from './Icon';

/** Dashed placeholder panel with icon, message and a call to action. */
export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">
        <Icon name={icon} size="2xl" />
      </div>
      <h3 className="empty-state__title">{title}</h3>
      <p className="empty-state__text">{description}</p>
      {action}
    </div>
  );
}
