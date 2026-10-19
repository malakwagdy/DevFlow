/** Joins truthy class names: cx('btn', isActive && 'is-active') → "btn is-active". */
export default function cx(...classes) {
  return classes.filter(Boolean).join(' ');
}
