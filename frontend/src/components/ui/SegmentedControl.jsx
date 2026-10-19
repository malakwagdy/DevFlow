import cx from '../../utils/classNames';

/**
 * Single-choice toggle group.
 * variant: "segmented" (raised active pill inside a track) | "pills" (flat tab buttons)
 * options: [{ value, label, badge? }]
 */
export default function SegmentedControl({ options, value, onChange, variant = 'segmented', block = false, label }) {
  const isPills = variant === 'pills';
  return (
    <div
      className={cx(isPills ? 'pill-tabs' : 'segmented', block && 'segmented--block')}
      role="tablist"
      aria-label={label}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            className={cx(isPills ? 'pill-tabs__option' : 'segmented__option', active && 'is-active')}
            onClick={() => onChange(option.value)}
          >
            {option.label}
            {option.badge && <span className="beta-badge">{option.badge}</span>}
          </button>
        );
      })}
    </div>
  );
}
