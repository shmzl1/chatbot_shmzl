import type { InputHTMLAttributes, PropsWithChildren } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function TextField({ label, children, className = "", ...props }: PropsWithChildren<TextFieldProps>) {
  return (
    <label className="text-field">
      {label ? <span>{label}</span> : null}
      <input
        className={`text-field-input ${className}`}
        {...props}
      />
      {children}
    </label>
  );
}
