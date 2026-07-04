/**
 * Login page.
 *
 * Authenticates against the backend and redirects to the dashboard on
 * success. Redirects away immediately if the user is already signed in.
 */
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginFormInput, type LoginFormValues } from "@/schemas/login_schema";
import { parseApiError } from "@/services/auth_service";
import { useAuthStore } from "@/stores/auth_store";
import AuthLayout from "@/components/layout/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import LoadingSpinner from "@/components/common/LoadingSpinner";

const FEATURES = [
  "Daily prayer tracker with streaks",
  "AI chatbot powered by Islamic knowledge",
  "Location-based prayer times",
  "Personalised dua & Surah finder",
];

export default function LoginPage() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const login = useAuthStore((state) => state.login);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormInput, unknown, LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { remember_me: false },
  });

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const onSubmit = async (values: LoginFormValues) => {
    setFormError(null);
    try {
      await login(values.email, values.password, values.remember_me);
      navigate("/", { replace: true });
    } catch (error) {
      const parsed = parseApiError(error);
      setFormError(parsed.message);
    }
  };

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
      features={FEATURES}
    >
      <h2 className="mb-2 text-3xl font-bold text-primary">Assalam Walaikum</h2>
      <p className="mb-9 text-base text-muted-foreground">Sign in to your NoorAI account</p>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="email" className="text-sm font-semibold text-foreground">
            Email address
          </label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-sm font-semibold text-foreground">
              Password
            </label>
            <Link to="/forgot-password" className="text-[13px] font-medium text-primary underline">
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="Enter your password"
            aria-invalid={!!errors.password}
            {...register("password")}
          />
          {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
        </div>

        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            {...register("remember_me")}
            className="h-4 w-4 rounded border-border accent-primary"
          />
          Remember me
        </label>

        {formError && <p className="text-sm text-destructive">{formError}</p>}

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? <LoadingSpinner size={20} /> : "Sign In"}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Don't have an account?{" "}
          <Link to="/register" className="font-semibold text-primary underline">
            Create one
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}