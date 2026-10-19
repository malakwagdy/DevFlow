import Button from '../ui/Button';
import Icon from '../ui/Icon';
import SectionHeader from '../ui/SectionHeader';
import cx from '../../utils/classNames';
import { ROUTES } from '../../config/navigation';

function TierCard({ eyebrow, title, price, priceNote, features, cta, featured, badge }) {
  return (
    <div className={cx('tier-card', featured && 'tier-card--featured')}>
      {badge && <span className="tier-card__badge">{badge}</span>}

      <div className="tier-card__head">
        <div>
          <span className="tier-card__eyebrow">{eyebrow}</span>
          <h3 className="tier-card__title">{title}</h3>
        </div>
        <span className="tier-card__price">
          {price} <span className="tier-card__price-note">{priceNote}</span>
        </span>
      </div>

      <ul className={cx('feature-list', featured && 'feature-list--emphasis')}>
        {features.map((feature) => (
          <li key={feature}>
            <Icon name="check" size="base" className="text-tertiary" />
            {feature}
          </li>
        ))}
      </ul>

      <Button variant={featured ? 'primary' : 'ghost'} block to={ROUTES.signUp} className="tier-card__cta">
        {cta}
      </Button>
    </div>
  );
}

export default function PricingSection({ id, eyebrow, title, items }) {
  return (
    <section className="section section--low" id={id}>
      <div className="container container--5xl">
        <SectionHeader eyebrow={eyebrow} title={title} compact />
        <div className="grid grid--2 grid--gap-lg">
          {items.map((tier) => (
            <TierCard key={tier.id} {...tier} />
          ))}
        </div>
      </div>
    </section>
  );
}
