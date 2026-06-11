import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="grid min-h-40 place-items-center rounded-2xl border border-dashed border-[var(--line)] bg-[rgba(255,250,241,0.54)] p-8 text-center">
      <div className="max-w-sm">
        {icon ? <div className="mx-auto mb-3 grid size-11 place-items-center rounded-full bg-[var(--surface-2)] text-[var(--green)]">{icon}</div> : null}
        <h3 className="text-base font-black text-[var(--ink)]">{title}</h3>
        {description ? <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{description}</p> : null}
      </div>
    </div>
  );
}
