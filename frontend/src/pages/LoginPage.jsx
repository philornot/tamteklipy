import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LogIn, Loader } from "lucide-react";
import usePageTitle from "../hooks/usePageTitle.js";

function LoginPage() {
  usePageTitle("Logowanie");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!username) {
      setError("Wprowadź nazwę użytkownika");
      return;
    }

    setLoading(true);

    const result = await login(username, password);

    setLoading(false);

    if (result.success) {
      navigate("/dashboard");
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="card p-8 w-full max-w-md glow">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text-primary mb-2">TamteKlipy</h1>
          <p className="text-gray-400">Zaloguj się do platformy</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-button mb-4">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-300 mb-2 text-sm font-medium">
              Username
            </label>
            <input
              className="input-field"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Wprowadź nazwę użytkownika"
              disabled={loading}
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-300 mb-2 text-sm font-medium">
              Hasło
            </label>
            <input
              className="input-field"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? (
              <>
                <Loader className="animate-spin" size={20} />
                Logowanie...
              </>
            ) : (
              <>
                <LogIn size={20} />
                Zaloguj się
              </>
            )}
          </button>
        </form>

        {/* Footer hint */}
        <div className="mt-6 pt-6 border-t border-gray-700">
          <p className="text-gray-500 text-sm text-center">
            todo: tutaj napisz później coś mądrego
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
