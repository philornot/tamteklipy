import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import Layout from "./components/layout/Layout";
import MobileNavBar from "./components/layout/MobileNavBar";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProtectedRoute from "./components/ProtectedRoute";
import UploadPage from "./pages/UploadPage";
import AdminPage from "./pages/AdminPage.jsx";
import MyAwardsPage from "./pages/MyAwardsPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import StatsPage from './pages/StatsPage';
import VerticalFeed from './components/mobile/VerticalFeed';
import useIsMobile from './hooks/useIsMobile';

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
          
          {/* Redirect upload/stats to main feed */}
          <Route path="/upload" element={<Navigate to="/" replace />} />
          <Route path="/stats" element={<Navigate to="/" replace />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        
        <MobileNavBar 
          currentPath={location.pathname}
          onNavigate={navigate}
          user={user}
        />
      </>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes with Layout */}
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
