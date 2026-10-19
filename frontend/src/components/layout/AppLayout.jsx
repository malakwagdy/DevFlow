import { Outlet } from 'react-router-dom';
import MobileNav from './MobileNav';
import ScrollManager from './ScrollManager';
import TopNavBar from './TopNavBar';

/** Shell shared by every route: fixed top navbar, page outlet, mobile bottom nav. */
export default function AppLayout() {
  return (
    <>
      <ScrollManager />
      <TopNavBar />
      <MobileNav />
      <Outlet />
    </>
  );
}
