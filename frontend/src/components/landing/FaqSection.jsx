import Icon from '../ui/Icon';
import SectionHeader from '../ui/SectionHeader';

function FaqItem({ question, answer, defaultOpen }) {
  return (
    <details className="faq-item" open={defaultOpen}>
      <summary className="faq-item__summary">
        <span>{question}</span>
        <Icon name="expand_more" className="faq-item__chevron" />
      </summary>
      <p className="faq-item__answer">{answer}</p>
    </details>
  );
}

export default function FaqSection({ id, eyebrow, title, items }) {
  return (
    <section className="section section--lowest" id={id}>
      <div className="container container--3xl">
        <SectionHeader eyebrow={eyebrow} title={title} compact />
        <div className="faq-list">
          {items.map((item) => (
            <FaqItem key={item.id} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
