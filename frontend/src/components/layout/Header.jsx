import { Link, useNavigate } from "react-router-dom";
import { Award, Home, LogOut, Upload } from "lucide-react";

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
                to="/awards"
                className="flex items-center gap-2 text-gray-300 hover:text-white transition"
              >
                <Award size={20} />
                <span>Nagrody</span>
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

              {/* User info */}
              <div className="flex items-center gap-4 ml-4 pl-4 border-l border-gray-700">
                <span className="text-gray-400">{user.username}</span>

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
