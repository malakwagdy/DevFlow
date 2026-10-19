import cx from '../../utils/classNames';

/**
 * Initials badge.
 * tone: primary | secondary — shape: round | square
 */
export default function Avatar({ as: Tag = 'div', initials, tone = 'primary', shape = 'round', className, ...rest }) {
  return (
    <Tag className={cx('avatar', `avatar--${tone}`, `avatar--${shape}`, className)} {...rest}>
      {initials}
    </Tag>
  );
}
