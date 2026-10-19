import Icon from './Icon';
import cx from '../../utils/classNames';

/**
 * Label / big value / hint tile.
 * variant: "default" (dashboard KPI) | "preview" (compact tile in the landing mock window)
 */
export default function MetricCard({
  label,
  value,
  hint,
  hintIcon,
  valueTone,
  hintTone,
  valueFormat,
  variant = 'default',
}) {
  return (
    <div className={cx('metric-card', `metric-card--${variant}`)}>
      <div className="metric-card__label">{label}</div>
      <div
        className={cx(
          'metric-card__value',
          valueFormat === 'code' && 'metric-card__value--code',
          valueTone && `text-${valueTone}`,
        )}
      >
        {value}
      </div>
      {hint && (
        <div className={cx('metric-card__hint', hintTone && `text-${hintTone}`)}>
          {hintIcon && <Icon name={hintIcon} size="xs" />}
          {hint}
        </div>
      )}
    </div>
  );
}
