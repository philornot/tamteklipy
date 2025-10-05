import { Link, useNavigate } from "react-router-dom";
import { Award, Home, LogOut, Settings, Upload, BarChart3 } from "lucide-react";

function Header({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate("/login");
  };

  return (
    <header className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link
            to="/"
            className="text-2xl font-bold text-white hover:text-gray-300"
          >
            TamteKlipy
          </Link>

          {/* Navigation */}
          {user && (
            <nav className="flex items-center gap-6">
              <Link
                to="/dashboard"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <Home size={20} />
                <span>Dashboard</span>
              </Link>

              <Link
                to="/my-awards"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <Award size={20} />
                <span>Moje Nagrody</span>
              </Link>

              <Link
                to="/upload"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <Upload size={20} />
                <span>Upload</span>
              </Link>

              {/* Nowa zakładka: Statystyki */}
              <Link
                to="/stats"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <BarChart3 size={20} />
                <span>Statystyki</span>
              </Link>

              {/* Panel zakładka dla admina */}
              {user?.is_admin && (
                <Link
                  to="/admin"
                  className="flex items-center gap-2 text-blue-400 hover:text-blue-300 font-semibold transition border border-blue-400 hover:border-blue-300 rounded px-3 py-1"
                >
                  <Settings size={16} />
                  <span>Panel</span>
                </Link>
              )}

              {/* User info */}
              <div className="flex items-center gap-4 ml-4 pl-4 border-l border-gray-700">
                <Link
                  to="/profile"
                  className="text-gray-400 hover:text-white"
                  title="Profil"
                >
                  {user.username}
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 text-gray-400 hover:text-red-400 transition"
                  title="Wyloguj"
                >
                  <LogOut size={20} />
                </button>
              </div>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
