interface MetricTableProps {
  headers: string[];
  rows: (string | number)[][];
  caption?: string;
}

export default function MetricTable({ headers, rows, caption }: MetricTableProps) {
  function formatCell(value: string | number): string {
    if (typeof value === 'string') return value;
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toString();
  }

  return (
    <table className="metric-table">
      {caption && <caption className="metric-table-caption">{caption}</caption>}
      <thead>
        <tr>
          {headers.map((header) => (
            <th key={header} scope="col">
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => (
              <td key={cellIndex}>{formatCell(cell)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
