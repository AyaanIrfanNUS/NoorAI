/**
 * Reusable loading indicator using the primary brand color.
 */
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: number;
}

export default function LoadingSpinner({ size = 24 }: LoadingSpinnerProps) {
  return (
    <Loader2
      className="animate-spin text-primary"
      style={{ width: size, height: size }}
    />
  );
}