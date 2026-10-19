import cx from '../../utils/classNames';

/**
 * Bordered surface used for panels throughout the app.
 * padding: none | sm (1rem) | md (1.25rem) | lg (1.5rem) | xl (2rem)
 */
export default function Card({ as: Tag = 'div', padding = 'sm', shadow = false, className, children, ...rest }) {
  return (
    <Tag
      className={cx('card', padding !== 'none' && `card--pad-${padding}`, shadow && 'card--shadow', className)}
      {...rest}
    >
      {children}
    </Tag>
  );
}
