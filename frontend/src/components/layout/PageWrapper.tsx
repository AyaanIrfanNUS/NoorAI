/**
 * Layout shell for all protected pages. Renders the Navbar and applies
 * consistent padding and max-width to the page content below it.
 */
import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar";

const HIDDEN_NAVBAR_PATHS = ["/login", "/register"];

export default function PageWrapper() {
  const location = useLocation();
  const showNavbar = !HIDDEN_NAVBAR_PATHS.includes(location.pathname);

  return (
    <div className="min-h-screen bg-background">
      {showNavbar && <Navbar />}
      <main className="mx-auto max-w-[1440px] p-8">
        <Outlet />
      </main>
    </div>
  );
}