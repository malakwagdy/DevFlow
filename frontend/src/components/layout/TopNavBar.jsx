import { Link } from 'react-router-dom';
import Avatar from '../ui/Avatar';
import Button from '../ui/Button';
import Icon from '../ui/Icon';
import StatusDot from '../ui/StatusDot';
import ThemeToggle from '../ui/ThemeToggle';
import { LANDING_SECTIONS, ROUTES } from '../../config/navigation';
import { useSession } from '../../context/SessionContext';

export default function TopNavBar() {
  const { user, workspace } = useSession();

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
          <div className="workspace-pill">
            <StatusDot tone="tertiary" size="md" />
            <span className="workspace-pill__name">{workspace?.slug ?? '…'}</span>
          </div>
          <ThemeToggle />
          <Button variant="secondary" size="sm" icon="dns" to={ROUTES.projects} className="hide-below-lg">
            My Projects
          </Button>
          <Button size="sm" icon="add" to={ROUTES.newProject} className="hide-below-lg">
            Create New Project
          </Button>
          <Link to={ROUTES.signIn} className="topnav__signin">
            Sign In
          </Link>
          <Avatar as={Link} to={ROUTES.signUp} initials={user?.initials ?? ''} title="User profile / team" />
        </div>
      </div>
    </header>
  );
}
