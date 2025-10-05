import {createContext, useEffect, useState} from "react";
import api from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({children}) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem("access_token");
        const storedUser = localStorage.getItem("user");

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }

        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            // FastAPI OAuth2 wymaga form-data
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const response = await api.post("/auth/login", formData, {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            });

            const {access_token} = response.data;

            // Pobierz dane usera
            const userResponse = await api.get("/auth/me", {
                headers: {
                    Authorization: `Bearer ${access_token}`,
                },
            });

            const userData = userResponse.data;

            // DEBUG - dodaj to
            console.log("=== /auth/me Response ===");
            console.log(userData);
            console.log("is_admin:", userData.is_admin);
            console.log("========================");

            // Zapisz w state i localStorage
            setToken(access_token);
            setUser(userData);
            localStorage.setItem("access_token", access_token);
            localStorage.setItem("user", JSON.stringify(userData));

            return {success: true};
        } catch (error) {
            console.error("Login failed:", error);
            return {
                success: false,
                error: error.response?.data?.message || "Błąd logowania",
            };
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
    };

    const value = {
        user,
        token,
        loading,
        login,
        logout,
        setUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
