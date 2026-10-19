import cx from '../../utils/classNames';

/** Centered eyebrow + serif headline (+ optional description) used by landing sections. */
export default function SectionHeader({ eyebrow, title, description, compact = false }) {
  return (
    <div className={cx('section-header', compact && 'section-header--compact')}>
      <span className="section-header__eyebrow">{eyebrow}</span>
      <h2 className="section-header__title">{title}</h2>
      {description && <p className="section-header__description">{description}</p>}
    </div>
  );
}
