export function Table({ children, className = "" }) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-collapse text-left text-[13px] tabular-nums">
        {children}
      </table>
    </div>
  );
}

export function THead({ columns }) {
  return (
    <thead>
      <tr className="border-b border-slate-200">
        {columns.map((col, i) => (
          <th key={i} className="micro-label px-3 py-2.5">
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export function TRow({ children, onClick, className = "" }) {
  return (
    <tr
      onClick={onClick}
      className={`border-b border-slate-100 last:border-0 ${
        onClick ? "cursor-pointer hover:bg-slate-50" : ""
      } ${className}`}
    >
      {children}
    </tr>
  );
}

export function TCell({ children, className = "" }) {
  return <td className={`px-3 py-2.5 align-middle ${className}`}>{children}</td>;
}
