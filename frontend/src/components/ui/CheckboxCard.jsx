/** Checkbox option rendered as a card with title + description. */
export default function CheckboxCard({ checked, onChange, title, description }) {
  return (
    <label className="check-card">
      <input
        type="checkbox"
        className="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <div>
        <div className="check-card__title">{title}</div>
        <div className="check-card__description">{description}</div>
      </div>
    </label>
  );
}
