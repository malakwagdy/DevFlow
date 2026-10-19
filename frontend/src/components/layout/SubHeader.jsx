import cx from '../../utils/classNames';

/**
 * Full-width header band under the navbar.
 * width: "narrow" (64rem, form screens) | "wide" (80rem, stacks on mobile)
 */
export default function SubHeader({ width = 'narrow', children }) {
  return (
    <header className="subheader">
      <div className={cx('subheader__inner', `subheader__inner--${width}`)}>{children}</div>
    </header>
  );
}
