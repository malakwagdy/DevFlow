import Button from '../ui/Button';
import { ROUTES } from '../../config/navigation';

export default function CtaBand({ title, description, button }) {
  return (
    <section className="cta-band">
      <div className="container container--3xl">
        <h2 className="cta-band__title">{title}</h2>
        <p className="cta-band__text">{description}</p>
        <Button size="lg" to={ROUTES.newProject} className="cta-band__button">
          {button}
        </Button>
      </div>
    </section>
  );
}
