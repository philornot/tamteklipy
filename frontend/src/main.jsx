import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import {AuthProvider} from "./contexts/AuthContext";
import {Toaster} from "react-hot-toast";
import ErrorBoundary from "./components/ErrorBoundary";

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <ErrorBoundary showDetails={import.meta.env.DEV}>
            <AuthProvider>
                <App/>
                <Toaster position="top-right"/>
            </AuthProvider>
        </ErrorBoundary>
    </React.StrictMode>
);