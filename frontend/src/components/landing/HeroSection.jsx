import Button from '../ui/Button';
import DashboardPreview from './DashboardPreview';
import { ROUTES } from '../../config/navigation';

export default function HeroSection({ hero, preview }) {
  return (
    <section className="hero">
      <div className="hero__inner">
        <div className="hero__badge">
          <span className="hero__badge-dot" aria-hidden="true" />
          {hero.badge}
        </div>
        <h1 className="hero__title">{hero.title}</h1>
        <p className="hero__subtitle">{hero.subtitle}</p>

        <div className="hero__actions">
          <Button size="lg" icon="rocket_launch" to={ROUTES.newProject}>
            {hero.primaryCta}
          </Button>
          <Button size="lg" variant="outline" icon="desktop_windows" to={ROUTES.projects}>
            {hero.secondaryCta}
          </Button>
        </div>

        <DashboardPreview {...preview} />
      </div>
    </section>
  );
}
