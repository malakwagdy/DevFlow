import cx from '../../utils/classNames';

/** Radio option rendered as a selectable card. */
export default function ChoiceCard({ name, value, checked, onChange, title, description }) {
  return (
    <label className={cx('choice-card', checked && 'is-selected')}>
      <input
        type="radio"
        className="visually-hidden"
        name={name}
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
      />
      <span className="choice-card__title">{title}</span>
      <span className="choice-card__description">{description}</span>
    </label>
  );
}
