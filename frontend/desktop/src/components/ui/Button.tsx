import type { ButtonHTMLAttributes, PropsWithChildren } from "react";
import { clsx } from "clsx";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variants: Record<ButtonVariant, string> = {
  primary: "bg-[var(--green)] text-white shadow-soft hover:bg-[var(--green-2)]",
  secondary: "border border-[var(--line)] bg-[var(--surface)] text-[var(--ink)] hover:bg-[var(--surface-2)]",
  ghost: "bg-transparent text-[var(--muted)] hover:bg-[rgba(98,119,90,0.1)] hover:text-[var(--ink)]",
  danger: "bg-[rgba(168,90,82,0.1)] text-[var(--danger)] hover:bg-[rgba(168,90,82,0.16)]",
};

export function Button({
  className,
  variant = "secondary",
  children,
  ...props
}: PropsWithChildren<ButtonProps>) {
  return (
    <button
      className={clsx(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
