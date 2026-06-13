import { Minus, Square, X } from "lucide-react";

export function WindowFrame() {
  function control(action: "minimize" | "maximize" | "close") {
    window.desktopShell?.windowControl?.(action);
  }

  return (
    <header className="window-frame drag">
      <div className="window-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="window-title">虚拟人物陪伴系统</div>
      <div className="window-controls">
        <button type="button" aria-label="最小化" onClick={() => control("minimize")}>
          <Minus size={14} />
        </button>
        <button type="button" aria-label="最大化" onClick={() => control("maximize")}>
          <Square size={12} />
        </button>
        <button type="button" aria-label="关闭" onClick={() => control("close")}>
          <X size={15} />
        </button>
      </div>
    </header>
  );
}
