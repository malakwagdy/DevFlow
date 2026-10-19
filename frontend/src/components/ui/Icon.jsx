import cx from '../../utils/classNames';

/**
 * Material Symbols icon.
 * size: xs (12px) | sm (14px) | base (16px) | default (18px) | xl (20px) | 2xl (24px)
 */
export default function Icon({ name, size, filled = false, spin = false, className, ...rest }) {
  return (
    <span
      className={cx(
        'material-symbols-outlined',
        'icon',
        size && `icon--${size}`,
        filled && 'icon--filled',
        spin && 'icon--spin',
        className,
      )}
      aria-hidden="true"
      {...rest}
    >
      {name}
    </span>
  );
}
