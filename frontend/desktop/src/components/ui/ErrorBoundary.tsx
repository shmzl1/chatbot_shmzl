import React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "./Button";

interface ErrorBoundaryState {
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  scope?: string;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(`${this.props.scope || "Page"} crashed:`, error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-card">
          <div className="error-card-icon">
            <AlertTriangle size={22} />
          </div>
          <div className="min-w-0">
            <p className="eyebrow">{this.props.scope || "页面"} 出错</p>
            <h2>这个页面刚刚摔了一下，但应用还在。</h2>
            <p>{this.state.error.message || "未知前端错误"}</p>
            <Button variant="primary" onClick={() => this.setState({ error: null })}>
              <RotateCcw size={16} />
              重新显示
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
