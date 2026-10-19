import cx from '../../utils/classNames';

/** Styled <select>. options: string[] or [{ value, label }]. size: md | sm */
export default function Select({ options, size = 'md', mono = false, className, ...rest }) {
  return (
    <select
      className={cx('input', 'select', size === 'sm' && 'input--sm', mono && 'input--mono', className)}
      {...rest}
    >
      {options.map((option) => {
        const { value, label } = typeof option === 'string' ? { value: option, label: option } : option;
        return (
          <option key={value} value={value}>
            {label}
          </option>
        );
      })}
    </select>
  );
}
