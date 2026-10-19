import { Link } from 'react-router-dom';
import Avatar from '../ui/Avatar';
import Icon from '../ui/Icon';
import cx from '../../utils/classNames';

function SideNavItem({ item, compact = false }) {
  const className = cx('sidenav__link', compact && 'sidenav__link--compact', item.active && 'is-active');
  const content = (
    <>
      <Icon name={item.icon} size="base" />
      {item.label}
    </>
  );

  if (item.to) {
    return (
      <Link to={item.to} className={className} aria-current={item.active ? 'page' : undefined}>
        {content}
      </Link>
    );
  }
  // Placeholder destinations that don't exist in the prototype yet.
  return (
    <button type="button" className={className}>
      {content}
    </button>
  );
}

/** Avatar + title + subtitle block at the top of a side nav. */
export function SideNavHeader({ initials, avatarTone = 'primary', title, titleTone, subtitle, subtitleTone }) {
  return (
    <div className="sidenav__header">
      <Avatar initials={initials} tone={avatarTone} shape="square" />
      <div>
        <div className={cx('sidenav__title', titleTone && `text-${titleTone}`)}>{title}</div>
        <div className={cx('sidenav__subtitle', subtitleTone && `text-${subtitleTone}`)}>{subtitle}</div>
      </div>
    </div>
  );
}

/**
 * Left sidebar used by the workspace and service screens.
 * items / footerItems: [{ label, icon, to?, active? }]
 */
export default function SideNav({ label, header, cta, items, footerItems, footer }) {
  const hasFooter = Boolean(footerItems?.length || footer);

  return (
    <aside className="sidenav" aria-label={label}>
      <div>
        {header}
        {cta && <div className="sidenav__cta">{cta}</div>}
        <nav className="sidenav__nav">
          {items.map((item) => (
            <SideNavItem key={item.label} item={item} />
          ))}
        </nav>
      </div>
      {hasFooter && (
        <div className="sidenav__footer">
          {footerItems?.map((item) => (
            <SideNavItem key={item.label} item={item} compact />
          ))}
          {footer}
        </div>
      )}
    </aside>
  );
}
