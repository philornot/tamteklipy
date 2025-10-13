/* eslint-disable react-refresh/only-export-components */
import {createContext, useEffect, useState} from "react";
import api from "../services/api";
import { logger } from "../utils/logger";

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

            // DEBUG
            logger.debug("/auth/me response", userData);

            // Zapisz w state i localStorage
            setToken(access_token);
            setUser(userData);
            localStorage.setItem("access_token", access_token);
            localStorage.setItem("user", JSON.stringify(userData));

            return {success: true};
        } catch (error) {
            logger.error("Login failed:", error);
            const status = error.response?.status;
            const backendMessage = error.response?.data?.message;

            // Specjalny komunikat dla konta nieaktywnego
            if (status === 401 && backendMessage === "Konto jest nieaktywne") {
                return {
                    success: false,
                    error: "Twoje konto zostało dezaktywowane przez administratora. Skontaktuj się z administratorem, aby je ponownie aktywować.",
                };
            }

            return {
                success: false,
                error: backendMessage || "Błąd logowania",
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
