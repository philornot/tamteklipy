import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { LogIn, Loader } from "lucide-react";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Walidacja
    if (!username || !password) {
      setError("Wypełnij wszystkie pola");
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
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md border border-gray-700">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">TamteKlipy</h1>
          <p className="text-gray-400">Zaloguj się do platformy</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-gray-300 mb-2">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field w-full"
              placeholder="admin"
              disabled={loading}
              required
            />
          </div>

          <div className="mb-6">
            <label htmlFor="password" className="block text-gray-300 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field w-full"
              placeholder="••••••••"
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
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

        {/* Test credentials hint */}
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
