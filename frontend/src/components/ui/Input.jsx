import { forwardRef } from "react";

const Input = forwardRef(function Input(
  { label, error, hint, className = "", ...props },
  ref
) {
  return (
    <label className="block">
      {label && (
        <span className="micro-label mb-1 block">
          {label}
          {hint && (
            <span className="ml-1 font-normal normal-case tracking-normal text-slate-400">
              ({hint})
            </span>
          )}
        </span>
      )}
      <input
        ref={ref}
        className={`w-full rounded-md border-0 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm ring-1 ring-inset placeholder:text-slate-400 focus:ring-2 focus:ring-inset ${
          error
            ? "ring-red-300 focus:ring-red-500"
            : "ring-slate-300 focus:ring-amber-500"
        } ${className}`}
        {...props}
      />
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
});

export default Input;
