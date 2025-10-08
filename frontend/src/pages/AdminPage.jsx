import { useState } from "react";
import { Award, BarChart3, Film, Users } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { Navigate } from "react-router-dom";
import StatsPanel from "../components/admin/StatsPanel.jsx";
import UsersManager from "../components/admin/UsersManager.jsx";
import AwardTypesManager from "../components/admin/AwardTypesManager.jsx";
import ClipsManager from "../components/admin/ClipsManager.jsx";
import usePageTitle from "../hooks/usePageTitle.js";

function AdminPage() {
  usePageTitle("Admin Panel");
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("clips");

  // Check admin permission
  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Panel Administracyjny</h1>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-700 overflow-x-auto">
        <button
          onClick={() => setActiveTab("clips")}
          className={`px-4 py-2 flex items-center gap-2 whitespace-nowrap ${
            activeTab === "clips"
              ? "border-b-2 border-blue-500 text-white"
              : "text-gray-400"
          }`}
        >
          <Film size={20} />
          Klipy
        </button>
        <button
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2 flex items-center gap-2 whitespace-nowrap ${
            activeTab === "users"
              ? "border-b-2 border-blue-500 text-white"
              : "text-gray-400"
          }`}
        >
          <Users size={20} />
          Użytkownicy
        </button>
        <button
          onClick={() => setActiveTab("award-types")}
          className={`px-4 py-2 flex items-center gap-2 whitespace-nowrap ${
            activeTab === "award-types"
              ? "border-b-2 border-blue-500 text-white"
              : "text-gray-400"
          }`}
        >
          <Award size={20} />
          Nagrody
        </button>
        <button
          onClick={() => setActiveTab("stats")}
          className={`px-4 py-2 flex items-center gap-2 whitespace-nowrap ${
            activeTab === "stats"
              ? "border-b-2 border-blue-500 text-white"
              : "text-gray-400"
          }`}
        >
          <BarChart3 size={20} />
          Statystyki
        </button>
      </div>

      {/* Content */}
      <div>
        {activeTab === "clips" && <ClipsManager />}
        {activeTab === "users" && <UsersManager />}
        {activeTab === "award-types" && <AwardTypesManager />}
        {activeTab === "stats" && <StatsPanel />}
      </div>
    </div>
  );
}

export default AdminPage;
