export default function SiteFooter({ brand, copyright, links }) {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__brand">
          <span className="site-footer__name">{brand}</span>
          <span>{copyright}</span>
        </div>
        <div className="site-footer__links">
          {links.map((link) => (
            <a key={link} href="#" className="site-footer__link" onClick={(event) => event.preventDefault()}>
              {link}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
