import { Link, useNavigate } from 'react-router-dom';
import UserMenu from './UserMenu';
import Button from '../ui/Button';
import Icon from '../ui/Icon';
import StatusDot from '../ui/StatusDot';
import ThemeToggle from '../ui/ThemeToggle';
import { LANDING_SECTIONS, ROUTES } from '../../config/navigation';
import { useSession } from '../../context/SessionContext';

export default function TopNavBar() {
  const { isAuthenticated, workspace, signOut } = useSession();
  const navigate = useNavigate();

  const handleSignOut = () => {
    signOut();
    navigate(ROUTES.landing);
  };

  return (
    <header className="topnav">
      <div className="topnav__inner">
        <div className="topnav__left">
          <Link to={ROUTES.landing} className="brand">
            <Icon name="rocket_launch" size="xl" />
            <span>DevFlow</span>
          </Link>
          <nav className="topnav__links" aria-label="Landing sections">
            {LANDING_SECTIONS.map((section) => (
              <Link key={section.id} to={`${ROUTES.landing}#${section.id}`} className="topnav__link">
                {section.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="topnav__right">
          {isAuthenticated && (
            <div className="workspace-pill">
              <StatusDot tone="tertiary" size="md" />
              <span className="workspace-pill__name">{workspace?.slug ?? '…'}</span>
            </div>
          )}
          <ThemeToggle />
          <Button variant="secondary" size="sm" icon="dns" to={ROUTES.projects} className="hide-below-lg">
            My Projects
          </Button>
          <Button size="sm" icon="add" to={ROUTES.newProject} className="hide-below-lg">
            Create New Project
          </Button>
          {isAuthenticated ? (
            <button type="button" className="topnav__signin" onClick={handleSignOut}>
              Sign Out
            </button>
          ) : (
            <Link to={ROUTES.signIn} className="topnav__signin">
              Sign In
            </Link>
          )}
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
