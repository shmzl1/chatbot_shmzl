import type { PropsWithChildren } from "react";
import { clsx } from "clsx";

interface PaperPanelProps {
  className?: string;
}

export function PaperPanel({ children, className }: PropsWithChildren<PaperPanelProps>) {
  return <section className={clsx("paper-sheet rounded-[24px] p-5", className)}>{children}</section>;
}
