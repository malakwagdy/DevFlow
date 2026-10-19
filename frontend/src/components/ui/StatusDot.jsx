import cx from '../../utils/classNames';

/**
 * Small colored indicator dot.
 * tone: current (inherits text color) | success | info | danger | neutral | primary | tertiary | tertiary-container
 */
export default function StatusDot({ tone = 'current', size = 'sm', pulse = false, className }) {
  return (
    <span
      className={cx('dot', `dot--${tone}`, size === 'md' && 'dot--md', pulse && 'dot--pulse', className)}
      aria-hidden="true"
    />
  );
}
