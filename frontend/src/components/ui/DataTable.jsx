import cx from '../../utils/classNames';

/**
 * Generic table.
 * columns: [{ key, header, render(row), align?: 'right', className?, stopPropagation? }]
 * variant: "default" | "compact"
 */
export default function DataTable({
  columns,
  rows,
  getRowKey,
  onRowClick,
  variant = 'default',
  emptyMessage = 'No records found.',
}) {
  const handleKeyDown = (event, row) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onRowClick(row);
    }
  };

  return (
    <table className={cx('data-table', `data-table--${variant}`, onRowClick && 'data-table--clickable')}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} className={cx(column.align === 'right' && 'is-right')}>
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr>
            <td className="data-table__empty" colSpan={columns.length}>
              {emptyMessage}
            </td>
          </tr>
        ) : (
          rows.map((row, index) => (
            <tr
              key={getRowKey(row, index)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              onKeyDown={onRowClick ? (event) => handleKeyDown(event, row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cx(column.align === 'right' && 'is-right', column.className)}
                  onClick={column.stopPropagation ? (event) => event.stopPropagation() : undefined}
                  onKeyDown={column.stopPropagation ? (event) => event.stopPropagation() : undefined}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
