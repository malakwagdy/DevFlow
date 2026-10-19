import cx from '../../utils/classNames';

/**
 * Top-level page wrapper; offsets the fixed navbar and the mobile bottom nav.
 * variant: sidebar | muted | plain | auth
 */
export default function Page({ variant, className, children }) {
  return <div className={cx('page', variant && `page--${variant}`, className)}>{children}</div>;
}
