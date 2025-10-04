import { useState, useEffect } from "react";
import { Users, Edit2, Shield } from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";

function UsersManager() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      // Endpoint do implementacji w backendzie: GET /api/admin/users
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch (err) {
      toast.error("Nie udało się załadować użytkowników");
      setUsers([]); // Fallback
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Ładowanie użytkowników...</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">
        Użytkownicy ({users.length})
      </h2>

      <div className="space-y-3">
        {users.length === 0 ? (
          <p className="text-gray-400 text-center py-8">
            Brak użytkowników (endpoint TODO)
          </p>
        ) : (
          users.map((user) => (
            <div
              key={user.id}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700 flex items-center justify-between"
            >
              <div>
                <h3 className="font-semibold flex items-center gap-2">
                  {user.username}
                  {user.award_scopes?.includes("admin") && (
                    <Shield
                      size={16}
                      className="text-yellow-500"
                      title="Admin"
                    />
                  )}
                </h3>
                <p className="text-sm text-gray-400">{user.email}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Scopes: {user.award_scopes?.length || 0}
                </p>
              </div>

              <button className="p-2 hover:bg-gray-700 rounded" title="Edytuj">
                <Edit2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default UsersManager;
