import { Link } from 'react-router-dom';
import Icon from './Icon';
import cx from '../../utils/classNames';

/** Small "← label" navigation link used in page headers. */
export default function BackLink({ to, children, className }) {
  return (
    <Link to={to} className={cx('back-link', className)}>
      <Icon name="arrow_back" size="xs" />
      {children}
    </Link>
  );
}
