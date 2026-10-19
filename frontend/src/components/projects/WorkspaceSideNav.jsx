import Button from '../ui/Button';
import SideNav, { SideNavHeader } from '../layout/SideNav';
import { ROUTES, WORKSPACE_NAV } from '../../config/navigation';

export default function WorkspaceSideNav({ workspace }) {
  return (
    <SideNav
      label="DevFlow main side navigation"
      header={
        <SideNavHeader
          initials={workspace?.initials ?? ''}
          title={workspace?.name ?? '…'}
          titleTone="primary"
          subtitle={workspace?.cluster ?? ''}
        />
      }
      cta={
        <Button icon="add" block to={ROUTES.newProject}>
          New Pipeline
        </Button>
      }
      items={WORKSPACE_NAV.main}
      footerItems={WORKSPACE_NAV.footer}
    />
  );
}
