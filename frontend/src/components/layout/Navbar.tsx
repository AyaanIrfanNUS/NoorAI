/**
 * Top navigation bar shown on all protected pages. Displays the NoorAI
 * brand, primary navigation links, a dark mode toggle, and the current
 * user's avatar with a logout menu. Hidden on /login and /register.
 */
import { NavLink } from "react-router-dom";
import { Moon, Sun, MoonStar } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { useAuthStore } from "../../stores/auth_store";
import { useThemeStore } from "../../stores/theme_store";

const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/prayers", label: "Prayers" },
  { to: "/chat", label: "AI Chat" },
  { to: "/dua", label: "Dua Finder" },
  { to: "/surah", label: "Surah Finder" },
  { to: "/quran", label: "Quran" },
  { to: "/zakat", label: "Zakat" },
];

function getInitials(fullName: string | undefined): string {
  if (!fullName) return "";
  const parts = fullName.trim().split(/\s+/);
  const initials = parts.slice(0, 2).map((part) => part[0]?.toUpperCase());
  return initials.join("");
}

export default function Navbar() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);

  return (
    <nav className="flex h-16 items-center gap-3 bg-primary px-8">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/20 text-accent">
        <Moon className="h-[18px] w-[18px]" />
      </div>
      <span className="text-lg font-bold tracking-tight text-primary-foreground">
        NoorAI
      </span>
      <span className="ml-1 text-[13px] text-accent">نور</span>

      <div className="ml-8 flex gap-1">
        {NAV_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              `rounded-sm px-4 py-1.5 text-sm transition-colors ${
                isActive
                  ? "bg-primary-foreground/15 font-semibold text-primary-foreground"
                  : "text-primary-foreground/75 hover:bg-primary-foreground/10"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>

      <div className="ml-auto flex items-center gap-3">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-foreground/10 text-primary-foreground"
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <MoonStar className="h-4 w-4" />
          )}
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-[13px] font-bold text-accent-foreground"
            >
              {getInitials(user?.full_name)}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => logout()}>
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </nav>
  );
}