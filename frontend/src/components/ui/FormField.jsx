import cx from '../../utils/classNames';

/** Label + control + optional hint. `action` renders on the right of the label (e.g. "Forgot password?"). */
export default function FormField({ label, htmlFor, hint, action, className, children }) {
  const labelElement = (
    <label className="field__label" htmlFor={htmlFor}>
      {label}
    </label>
  );

  return (
    <div className={cx('field', className)}>
      {action ? (
        <div className="field__label-row">
          {labelElement}
          {action}
        </div>
      ) : (
        labelElement
      )}
      {children}
      {hint && <span className="field__hint">{hint}</span>}
    </div>
  );
}
