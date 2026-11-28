export interface ChartDataTableColumn {
  key: string;
  label: string;
}

export interface ChartDataTableProps {
  caption: string;
  columns: ChartDataTableColumn[];
  rows: ReadonlyArray<object>;
}

/** Visually hidden semantic HTML table exposing chart data to screen readers and assistive tech. */
export function ChartDataTable({ caption, columns, rows }: ChartDataTableProps) {
  if (rows.length === 0 || columns.length === 0) {
    return null;
  }

  return (
    <table className="sr-only">
      <caption>{caption}</caption>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} scope="col">
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIdx) => {
          const record = row as Record<string, unknown>;
          return (
            <tr key={rowIdx}>
              {columns.map((col) => (
                <td key={col.key}>
                  {record[col.key] !== undefined && record[col.key] !== null
                    ? String(record[col.key])
                    : '—'}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

