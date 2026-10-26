import cx from '../../utils/classNames';

/**
 * Initials badge. Pass `children` (e.g. an <Icon>) to show something other than initials.
 * tone: primary | secondary — shape: round | square
 */
export default function Avatar({ as: Tag = 'div', initials, children, tone = 'primary', shape = 'round', className, ...rest }) {
  return (
    <Tag className={cx('avatar', `avatar--${tone}`, `avatar--${shape}`, className)} {...rest}>
      {children ?? initials}
    </Tag>
  );
}
