import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { signInRedirect } from '../../config/navigation';
import { useSession } from '../../context/SessionContext';

/** Route guard: guests are sent to sign in, then returned to the page they asked for. */
export default function RequireAuth() {
  const { isAuthenticated } = useSession();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={signInRedirect(location.pathname + location.search)} replace />;
  }
  return <Outlet />;
}
