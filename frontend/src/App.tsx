/**
 * Root application component. Restores any remembered session before
 * rendering, then defines all routes and applies the protected route
 * guard to authenticated-only pages.
 */
import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/common/ProtectedRoute";
import PageWrapper from "./components/layout/PageWrapper";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import DashboardPage from "./pages/DashboardPage";
import PrayerTrackerPage from "./pages/PrayerTrackerPage";
import ChatPage from "./pages/ChatPage";
import DuaFinderPage from "./pages/DuaFinderPage";
import SurahFinderPage from "./pages/SurahFinderPage";
import SurahBrowserPage from "./pages/SurahBrowserPage";
import PrayerTimesPage from "./pages/PrayerTimesPage";
import ZakatPage from "./pages/ZakatPage";
import ProfilePage from "./pages/ProfilePage";
import { useAuthStore } from "./stores/auth_store";
import LoadingSpinner from "./components/common/LoadingSpinner";

export default function App() {
  const restoreSession = useAuthStore((state) => state.restoreSession);
  const isInitializing = useAuthStore((state) => state.isInitializing);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <LoadingSpinner size={32} />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<PageWrapper />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/prayers" element={<PrayerTrackerPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/dua" element={<DuaFinderPage />} />
            <Route path="/surah" element={<SurahFinderPage />} />
            <Route path="/quran" element={<SurahBrowserPage />} />
            <Route path="/times" element={<PrayerTimesPage />} />
            <Route path="/zakat" element={<ZakatPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}