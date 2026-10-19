import Icon from '../ui/Icon';
import SectionHeader from '../ui/SectionHeader';

function StepCard({ number, icon, title, description }) {
  return (
    <div className="step-card">
      <span className="step-card__number">{number}</span>
      <div className="icon-tile">
        <Icon name={icon} />
      </div>
      <h3 className="step-card__title">{title}</h3>
      <p className="step-card__text">{description}</p>
    </div>
  );
}

export default function HowItWorksSection({ id, eyebrow, title, description, steps }) {
  return (
    <section className="section section--lowest" id={id}>
      <div className="container container--6xl">
        <SectionHeader eyebrow={eyebrow} title={title} description={description} />
        <div className="grid grid--4">
          {steps.map((step) => (
            <StepCard key={step.number} {...step} />
          ))}
        </div>
      </div>
    </section>
  );
}
