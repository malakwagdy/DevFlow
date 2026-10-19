import { NavLink } from 'react-router-dom';
import Icon from '../ui/Icon';
import cx from '../../utils/classNames';
import { MOBILE_NAV_ITEMS } from '../../config/navigation';

/** Bottom quick-navigation bar shown below the `lg` breakpoint. */
export default function MobileNav() {
  return (
    <nav className="mobile-nav" aria-label="Mobile quick navigation">
      {MOBILE_NAV_ITEMS.map((item) => (
        <NavLink
          key={item.label}
          to={item.to}
          end
          className={({ isActive }) => cx('mobile-nav__item', isActive && 'is-active')}
        >
          <Icon name={item.icon} size="base" />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
