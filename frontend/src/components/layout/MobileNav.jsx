import { NavLink, useNavigate } from 'react-router-dom';
import Icon from '../ui/Icon';
import cx from '../../utils/classNames';
import { MOBILE_NAV_ITEMS, ROUTES } from '../../config/navigation';
import { useSession } from '../../context/SessionContext';

/** Bottom quick-navigation bar shown below the `lg` breakpoint. */
export default function MobileNav() {
  const { isAuthenticated, signOut } = useSession();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate(ROUTES.landing);
  };

  return (
    <nav className="mobile-nav" aria-label="Mobile quick navigation">
      {MOBILE_NAV_ITEMS.filter((item) => !(item.guestOnly && isAuthenticated)).map((item) => (
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
      {isAuthenticated && (
        <button type="button" className="mobile-nav__item" onClick={handleSignOut}>
          <Icon name="logout" size="base" />
          <span>Sign out</span>
        </button>
      )}
    </nav>
  );
}
