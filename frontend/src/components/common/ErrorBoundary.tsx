/**
 * Catches rendering errors in its child component tree and displays a
 * friendly fallback with a retry option, instead of crashing the entire
 * app. Analogous to a circuit breaker: one broken circuit doesn't cut
 * power to the whole house.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "../ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <h3 className="text-base font-semibold text-foreground">
            Something went wrong
          </h3>
          <p className="max-w-sm text-sm text-muted-foreground">
            An unexpected error occurred while loading this page.
          </p>
          <Button onClick={this.handleRetry} className="mt-2">
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}