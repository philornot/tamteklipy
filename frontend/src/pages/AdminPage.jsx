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

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  const tabs = [
    { id: "clips", label: "Klipy", icon: Film },
    { id: "users", label: "Użytkownicy", icon: Users },
    { id: "award-types", label: "Nagrody", icon: Award },
    { id: "stats", label: "Statystyki", icon: BarChart3 },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Panel Administracyjny</h1>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-dark-700 overflow-x-auto">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`px-4 py-2 flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeTab === id
                ? "border-b-2 border-primary-500 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <Icon size={20} />
            {label}
          </button>
        ))}
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
