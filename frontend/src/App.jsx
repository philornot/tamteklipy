import {BrowserRouter, Navigate, Route, Routes} from "react-router-dom";
import {useAuth} from "./hooks/useAuth";
import Layout from "./components/layout/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProtectedRoute from "./components/ProtectedRoute";
import UploadPage from "./pages/UploadPage";

function App() {
    const {user, logout} = useAuth();

    return (
        <BrowserRouter>
            <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage/>}/>

                {/* Protected routes with Layout */}
                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Layout user={user} onLogout={logout}>
                                <DashboardPage/>
                            </Layout>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/upload"
                    element={
                        <ProtectedRoute>
                            <Layout user={user} onLogout={logout}>
                                <UploadPage/>
                            </Layout>
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/my-awards"
                    element={
                        <ProtectedRoute>
                            <Layout user={user} onLogout={logout}>
                                <MyAwardsPage/>
                            </Layout>
                        </ProtectedRoute>
                    }
                />

                <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
                <Route path="*" element={<NotFoundPage/>}/>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
