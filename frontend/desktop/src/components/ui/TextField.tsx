import type { InputHTMLAttributes, PropsWithChildren } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function TextField({ label, children, ...props }: PropsWithChildren<TextFieldProps>) {
  return (
    <label className="grid gap-2 text-sm font-bold text-[var(--muted)]">
      {label ? <span>{label}</span> : null}
      <input
        className="h-11 rounded-xl border border-[var(--line)] bg-[rgba(255,255,255,0.62)] px-3 text-[var(--ink)] outline-none transition focus:border-[var(--green)] focus:bg-white"
        {...props}
      />
      {children}
    </label>
  );
}
