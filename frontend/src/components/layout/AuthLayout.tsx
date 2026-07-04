/**
 * Shared split-screen shell for the login and register pages.
 *
 * Left panel carries branding and marketing copy and stays pinned to
 * the viewport as the user scrolls; right panel renders whatever form
 * content is passed in as children and scrolls independently.
 */
import type { ReactNode } from "react";
import { Moon } from "lucide-react";

interface AuthLayoutProps {
  heroTitle: ReactNode;
  heroDescription: string;
  features: string[];
  children: ReactNode;
}

export default function AuthLayout({
  heroTitle,
  heroDescription,
  features,
  children,
}: AuthLayoutProps) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="relative hidden flex-col overflow-hidden bg-primary px-16 py-14 lg:sticky lg:top-0 lg:flex lg:h-screen lg:self-start">
        <Moon
          aria-hidden="true"
          strokeWidth={1}
          className="pointer-events-none absolute top-[40%] right-[-20px] h-[300px] w-[300px] -translate-y-1/2 text-white opacity-5"
        />

        <div className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/20">
            <Moon className="h-5 w-5 text-accent" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">NoorAI</div>
            <div className="mt-0.5 text-sm text-accent" style={{ fontFamily: "'Noto Sans Arabic', sans-serif" }}>
              نور الذكاء الاصطناعي
            </div>
          </div>
        </div>

        <div className="relative z-10 mt-auto mb-12">
          <h1 className="mb-4 text-5xl leading-tight font-bold text-white">{heroTitle}</h1>
          <p className="max-w-md text-lg leading-relaxed text-white/70">{heroDescription}</p>
        </div>

        <div className="relative z-10 flex flex-col gap-3.5">
          {features.map((feature) => (
            <div key={feature} className="flex items-center gap-3 text-[15px] text-white/85">
              <span className="h-2 w-2 shrink-0 rounded-full bg-accent" />
              {feature}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-center bg-background px-6 py-14 sm:px-20">
        <div className="w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  );
}