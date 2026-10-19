import cx from '../../utils/classNames';

/** Numbered card used for each step of the "Provision New Workload" form. */
export default function FormSection({ step, title, description, actions, children }) {
  const heading = (
    <>
      <h2 className={cx('form-section__title', description && 'form-section__title--with-description')}>
        <span className="step-number">{step}</span>
        {title}
      </h2>
      {description && <p className="form-section__description">{description}</p>}
    </>
  );

  return (
    <section className="form-section">
      {actions ? (
        <div className="form-section__header">
          <div>{heading}</div>
          {actions}
        </div>
      ) : (
        heading
      )}
      {children}
    </section>
  );
}
