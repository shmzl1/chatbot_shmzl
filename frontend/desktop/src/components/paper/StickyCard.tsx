import type { PropsWithChildren } from "react";
import { clsx } from "clsx";

interface StickyCardProps {
  className?: string;
}

export function StickyCard({ children, className }: PropsWithChildren<StickyCardProps>) {
  return <article className={clsx("note-card rounded-2xl p-4", className)}>{children}</article>;
}
