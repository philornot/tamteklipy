import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  // TODO: Pobierz auth state z AuthContext
  const isAuthenticated = false; // Placeholder

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
