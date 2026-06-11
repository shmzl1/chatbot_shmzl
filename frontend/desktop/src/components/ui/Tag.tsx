import type { PropsWithChildren } from "react";

export function Tag({ children }: PropsWithChildren) {
  return (
    <span className="inline-flex items-center rounded-full border border-[var(--line)] bg-[rgba(126,141,104,0.12)] px-2.5 py-1 text-xs font-bold text-[var(--green)]">
      {children}
    </span>
  );
}
