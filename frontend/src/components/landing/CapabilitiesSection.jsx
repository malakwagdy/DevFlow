import Icon from '../ui/Icon';
import SectionHeader from '../ui/SectionHeader';

/** Bottom strip of a capability card; its shape depends on `footer.type`. */
function CapabilityFooter({ footer }) {
  switch (footer.type) {
    case 'code':
      return (
        <div className="capability-card__code">
          <code>{footer.text}</code>
        </div>
      );
    case 'chips':
      return (
        <div className="chip-list">
          {footer.items.map((item) => (
            <span key={item} className="chip">
              {item}
            </span>
          ))}
        </div>
      );
    case 'note':
      return (
        <div className="capability-card__note">
          <Icon name={footer.icon} size="xs" className="text-tertiary" />
          {footer.text}
        </div>
      );
    case 'stats':
      return (
        <div className="capability-card__stats">
          <span>{footer.left}</span>
          <span className="text-tertiary text-semibold">{footer.right}</span>
        </div>
      );
    default:
      return null;
  }
}

function CapabilityCard({ icon, iconTone, tag, title, description, footer }) {
  return (
    <div className="capability-card">
      <div>
        <div className="capability-card__head">
          <Icon name={icon} className={`capability-card__icon text-${iconTone}`} />
          <span className="tag">{tag}</span>
        </div>
        <h3 className="capability-card__title">{title}</h3>
        <p className="capability-card__text">{description}</p>
      </div>
      <CapabilityFooter footer={footer} />
    </div>
  );
}

export default function CapabilitiesSection({ id, eyebrow, title, items }) {
  return (
    <section className="section section--background" id={id}>
      <div className="container container--6xl">
        <SectionHeader eyebrow={eyebrow} title={title} />
        <div className="grid grid--2">
          {items.map((item) => (
            <CapabilityCard key={item.id} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
