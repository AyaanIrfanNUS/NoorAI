/**
 * Registration page.
 *
 * Collects account details, maps first/last name into the backend's
 * single full_name field, and creates the account before redirecting
 * to the dashboard.
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, ChevronDown } from "lucide-react";
import { registerSchema, type RegisterFormInput, type RegisterFormValues } from "@/schemas/register_schema";
import * as authService from "@/services/auth_service";
import { parseApiError } from "@/services/auth_service";
import { useAuthStore } from "@/stores/auth_store";
import { COMMON_COUNTRIES, OTHER_COUNTRIES } from "@/data/countries_mapping";
import AuthLayout from "@/components/layout/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectGroup,
  SelectLabel,
  SelectItem,
} from "@/components/ui/select";
import LoadingSpinner from "@/components/common/LoadingSpinner";

const MADHAB_LABELS: Record<string, string> = {
  hanafi: "Hanafi",
  shafi: "Shafi'i",
  maliki: "Maliki",
  hanbali: "Hanbali",
  jafari: "Ja'fari",
};

const CURRENCY_OPTIONS = ["USD", "SGD", "GBP", "EUR", "PKR", "MYR", "INR", "AED", "SAR"];

function passwordStrength(password: string): { label: string; score: number } {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { label: "Weak", score };
  if (score <= 2) return { label: "Medium", score };
  return { label: "Strong", score };
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((state) => state.setUser);
  const [formError, setFormError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    watch,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormInput, unknown, RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      madhab: "shafi",
      currency: "USD",
    },
  });

  const password = watch("password") ?? "";
  const strength = passwordStrength(password);

  const onSubmit = async (values: RegisterFormValues) => {
    setFormError(null);
    setEmailError(null);

    try {
      const response = await authService.register({
        full_name: `${values.first_name} ${values.last_name}`.trim(),
        email: values.email,
        password: values.password,
        madhab: values.madhab,
        location_country: values.location_country,
        currency: values.currency,
      });

      useAuthStore.getState().setSession(response.user, response.tokens);

      navigate("/", { replace: true });
    } catch (error) {
      const parsed = parseApiError(error);

      if (parsed.status === 400) {
        setEmailError("An account with this email already exists");
        return;
      }

      for (const [field, message] of Object.entries(parsed.fieldErrors)) {
        if (field in values) {
          setError(field as keyof RegisterFormInput, { message });
        }
      }

      if (Object.keys(parsed.fieldErrors).length === 0) {
        setFormError(parsed.message);
      }
    }
  };

  return (
    <AuthLayout
      heroTitle={
        <>
          Begin your journey
          <br />
          with <span className="text-accent">NoorAI</span>
        </>
      }
      heroDescription="Join thousands of Muslims using NoorAI to deepen their practice and stay connected to their faith every day."
      features={["Free to get started", "No credit card required", "Works on all devices"]}
    >
      <h2 className="mb-2 text-[28px] font-bold text-primary">Create your account</h2>
      <p className="mb-7 text-base text-muted-foreground">Join NoorAI and start your journey</p>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">First name</label>
            <Input placeholder="Ahmad" {...register("first_name")} aria-invalid={!!errors.first_name} />
            {errors.first_name && <p className="text-sm text-destructive">{errors.first_name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">Last name</label>
            <Input placeholder="Hassan" {...register("last_name")} aria-invalid={!!errors.last_name} />
            {errors.last_name && <p className="text-sm text-destructive">{errors.last_name.message}</p>}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">Email address</label>
          <Input
            type="email"
            placeholder="you@example.com"
            {...register("email")}
            aria-invalid={!!errors.email || !!emailError}
          />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          {emailError && <p className="text-sm text-destructive">{emailError}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">Password</label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              {...register("password")}
              aria-invalid={!!errors.password}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute top-1/2 right-3 -translate-y-1/2 text-muted-foreground"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {password.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full transition-all ${
                    strength.label === "Weak"
                      ? "w-1/3 bg-destructive"
                      : strength.label === "Medium"
                        ? "w-2/3 bg-accent"
                        : "w-full bg-primary"
                  }`}
                />
              </div>
              <span className="text-xs text-muted-foreground">{strength.label}</span>
            </div>
          )}
          {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">Confirm password</label>
          <div className="relative">
            <Input
              type={showConfirmPassword ? "text" : "password"}
              placeholder="Repeat your password"
              {...register("confirm_password")}
              aria-invalid={!!errors.confirm_password}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword((v) => !v)}
              className="absolute top-1/2 right-3 -translate-y-1/2 text-muted-foreground"
              tabIndex={-1}
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="text-sm text-destructive">{errors.confirm_password.message}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">School of Thought (Madhab)</label>
          <Controller
            name="madhab"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(MADHAB_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          <p className="text-xs text-muted-foreground">Affects your Asr prayer time calculation</p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">Country</label>
          <Controller
            name="location_country"
            control={control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger className="w-full" aria-invalid={!!errors.location_country}>
                  <SelectValue placeholder="Select your country" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectLabel>Common</SelectLabel>
                    {COMMON_COUNTRIES.map((c) => (
                      <SelectItem key={c.code} value={c.code}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                  <SelectGroup>
                    <SelectLabel>All countries</SelectLabel>
                    {OTHER_COUNTRIES.map((c) => (
                      <SelectItem key={c.code} value={c.code}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            )}
          />
          {errors.location_country && (
            <p className="text-sm text-destructive">{errors.location_country.message}</p>
          )}
          <p className="text-xs text-muted-foreground">Sets your local prayer calculation method</p>
        </div>

        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className="flex items-center gap-1.5 text-sm font-medium text-primary"
          >
            <ChevronDown className={`h-4 w-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`} />
            Advanced settings
          </button>
          {showAdvanced && (
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-foreground">Currency</label>
              <Controller
                name="currency"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CURRENCY_OPTIONS.map((code) => (
                        <SelectItem key={code} value={code}>
                          {code}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          )}
        </div>

        {formError && <p className="text-sm text-destructive">{formError}</p>}

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? <LoadingSpinner size={20} /> : "Create Account"}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-primary underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}