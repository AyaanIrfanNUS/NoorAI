/**
 * Route guard that redirects unauthenticated users to the login page.
 * Wraps any route that requires a logged-in user.
 */
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../stores/auth_store";

export default function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}