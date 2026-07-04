/**
 * Placeholder for password reset. No backend endpoint exists yet;
 * this page reserves the route and UI slot so reset support can be
 * wired in later without changing how it's linked to from Login.
 */
import { Link } from "react-router-dom";
import AuthLayout from "@/components/layout/AuthLayout";

export default function ForgotPasswordPage() {
  return (
    <AuthLayout
      heroTitle={
        <>
          Your daily companion
          <br />
          for <span className="text-accent">Islamic living</span>
        </>
      }
      heroDescription="Track your prayers, discover duas, calculate zakat, and get answers from an AI trained on Islamic knowledge."
      features={[]}
    >
      <h2 className="mb-2 text-3xl font-bold text-primary">Password reset</h2>
      <p className="mb-9 text-base text-muted-foreground">
        Password reset isn't available yet. Please contact support or try signing in again.
      </p>
      <Link to="/login" className="text-sm font-semibold text-primary">
        Back to Sign In
      </Link>
    </AuthLayout>
  );
}