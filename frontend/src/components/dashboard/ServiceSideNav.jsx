import SideNav, { SideNavHeader } from '../layout/SideNav';
import StatusDot from '../ui/StatusDot';
import { SERVICE_NAV } from '../../config/navigation';

export default function ServiceSideNav({ service }) {
  return (
    <SideNav
      label="DevFlow dashboard side navigation"
      header={
        <SideNavHeader
          initials={service.initials}
          avatarTone="secondary"
          title={service.name}
          subtitleTone="success"
          subtitle={
            <>
              <StatusDot tone="success" /> {service.health}
            </>
          }
        />
      }
      items={SERVICE_NAV}
      footer={
        <div className="sidenav__meta">
          Release: <strong>{service.release}</strong>
        </div>
      }
    />
  );
}
