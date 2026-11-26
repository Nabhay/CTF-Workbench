import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Workbench UI crashed", error, info.componentStack);
  }

  render(): ReactNode {
    const { error } = this.state;
    if (!error) {
      return this.props.children;
    }
    return (
      <main className="min-h-screen bg-chassis px-6 py-16 text-paper">
        <p className="font-mono text-sm text-fault">The workbench UI stopped.</p>
        <h1 className="mt-4 max-w-xl text-3xl font-semibold tracking-tight">
          Reload the page. If this returns, copy the message below when reporting it.
        </h1>
        <pre className="mt-8 max-w-2xl overflow-x-auto border border-edge bg-panel p-4 font-mono text-sm text-mute">
          {error.message}
        </pre>
        <button
          type="button"
          className="mt-8 border border-lamp px-4 py-2 text-sm text-lamp"
          onClick={() => this.setState({ error: null })}
        >
          Try again
        </button>
      </main>
    );
  }
}
