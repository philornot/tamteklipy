import { lazy, Suspense } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import Layout from "./components/layout/Layout";
import MobileNavBar from "./components/layout/MobileNavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import useIsMobile from "./hooks/useIsMobile";
import { Spinner } from "./components/ui/StyledComponents";

/**
 * Lazy loaded pages for code splitting.
 * Each page becomes a separate chunk loaded on demand.
 */
const LoginPage = lazy(() => import("./pages/LoginPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const UploadPage = lazy(() => import("./pages/UploadPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const MyAwardsPage = lazy(() => import("./pages/MyAwardsPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const StatsPage = lazy(() => import("./pages/StatsPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));
const VerticalFeed = lazy(() => import("./components/mobile/VerticalFeed"));

/**
 * Loading fallback component.
 * Shown while lazy loaded components are being fetched.
 */
function PageLoader() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <Spinner size="xl" color="primary" />
        <p className="text-gray-400 mt-4">Ładowanie...</p>
      </div>
    </div>
  );
}

function AppContent() {
  const { user, logout } = useAuth();
  const isMobile = useIsMobile();
  const location = useLocation();

  const navigate = (path) => {
    window.location.href = path;
  };

  // Mobile routing
  if (isMobile && user) {
    return (
      <>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <VerticalFeed />
                </ProtectedRoute>
              }
            />

            <Route
              path="/awards"
              element={
                <ProtectedRoute>
                  <Layout user={user} onLogout={logout}>
                    <MyAwardsPage />
                  </Layout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Layout user={user} onLogout={logout}>
                    <ProfilePage />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {user?.is_admin && (
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <Layout user={user} onLogout={logout}>
                      <AdminPage />
                    </Layout>
                  </ProtectedRoute>
                }
              />
            )}

            <Route path="/upload" element={<Navigate to="/" replace />} />
            <Route path="/stats" element={<Navigate to="/" replace />} />
            <Route path="/dashboard" element={<Navigate to="/" replace />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>

        <MobileNavBar
          currentPath={location.pathname}
          onNavigate={navigate}
          user={user}
        />
      </>
    );
  }

  // Desktop routing
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <UploadPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/my-awards"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <MyAwardsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <AdminPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/stats"
          element={
            <ProtectedRoute>
              <Layout user={user} onLogout={logout}>
                <StatsPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
