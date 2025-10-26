import { useState } from "react";
import { Lock, LogOut, User } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

function MobileProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleChangePassword = () => {
    // Przekieruj do desktop view lub pokaż modal
    toast("Zmiana hasła dostępna w wersji desktop", { icon: "💻" });
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-900 pb-20">
      {/* Header z avatarem */}
      <div className="bg-gradient-to-br from-purple-900 to-fuchsia-900 p-8 text-center">
        <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center text-4xl font-bold text-white shadow-glow">
          {user.username[0].toUpperCase()}
        </div>
        <h1 className="text-2xl font-bold text-white mb-1">{user.username}</h1>
        <p className="text-purple-200 text-sm">{user.email || "Brak email"}</p>
      </div>

      {/* Stats Cards */}
      <div className="px-4 -mt-8 mb-6 grid grid-cols-2 gap-4">
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
          <p className="text-gray-400 text-xs mb-1">Status</p>
          <p className="text-white font-semibold">
            {user.is_active ? "🟢 Aktywny" : "🔴 Nieaktywny"}
          </p>
        </div>
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 text-center">
          <p className="text-gray-400 text-xs mb-1">Typ konta</p>
          <p className="text-white font-semibold">
            {user.is_admin ? "👑 Admin" : "👤 User"}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 space-y-3">
        {/* Change Password */}
        <button
          onClick={handleChangePassword}
          className="w-full p-4 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl flex items-center gap-3 transition"
        >
          <Lock size={20} className="text-purple-400" />
          <span className="flex-1 text-left">Zmień hasło</span>
          <span className="text-gray-500">→</span>
        </button>

        {/* Desktop Version Link */}
        <a
          href="/profile"
          className="w-full p-4 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl flex items-center gap-3 transition block"
        >
          <User size={20} className="text-blue-400" />
          <span className="flex-1 text-left">Pełna wersja profilu</span>
          <span className="text-gray-500">→</span>
        </a>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full p-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-xl flex items-center justify-center gap-3 transition text-red-400 font-semibold"
        >
          <LogOut size={20} />
          Wyloguj się
        </button>
      </div>

      {/* Info Box */}
      <div className="px-4 mt-6">
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 text-sm text-gray-400">
          <p className="mb-2">
            ℹ️ <strong>Wskazówka:</strong>
          </p>
          <p>Pełna edycja profilu dostępna jest w wersji desktop aplikacji.</p>
        </div>
      </div>
    </div>
  );
}

export default MobileProfilePage;
