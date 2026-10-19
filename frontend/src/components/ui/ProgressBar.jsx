/**
 * Labelled horizontal usage bar.
 * tone: secondary | warning | success | primary
 */
export default function ProgressBar({ label, value, percent, tone = 'secondary' }) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className="progress">
      <div className="progress__head">
        <span>{label}</span>
        <span className="progress__value">{value}</span>
      </div>
      <div
        className="progress__track"
        role="progressbar"
        aria-label={label}
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        {/* The fill width is the only runtime-computed style, passed as a CSS variable. */}
        <div className={`progress__fill progress__fill--${tone}`} style={{ '--progress': `${clamped}%` }} />
      </div>
    </div>
  );
}
