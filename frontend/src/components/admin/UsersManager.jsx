import { useEffect, useState } from "react";
import { Edit2, Shield, Trash2, Loader, Plus, X, Save, UserX } from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";
import { useAuth } from "../../hooks/useAuth";

function EditUserModal({ user, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    username: user.username,
    email: user.email || "",
    full_name: user.full_name || "",
    is_active: user.is_active,
    is_admin: user.is_admin,
  });
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    setLoading(true);

    try {
      await api.patch(`/admin/users/${user.id}`, formData);
      toast.success("Użytkownik zaktualizowany");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się zaktualizować");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-lg max-w-md w-full p-6 border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Edytuj użytkownika</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-gray-300 mb-2">Username</label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-2">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-2">Imię i nazwisko</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) =>
                setFormData({ ...formData, full_name: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-4 h-4"
              />
              <span className="text-gray-300">Aktywny</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_admin}
                onChange={(e) =>
                  setFormData({ ...formData, is_admin: e.target.checked })
                }
                className="w-4 h-4"
              />
              <span className="text-gray-300">Administrator</span>
            </label>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
            >
              Anuluj
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  Zapisywanie...
                </>
              ) : (
                <>
                  <Save size={16} />
                  Zapisz
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function UsersManager() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState(null);
  const [deleting, setDeleting] = useState({});

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch (err) {
      toast.error("Nie udało się załadować użytkowników");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (userId, username) => {
    if (userId === currentUser?.id) {
      toast.error("Nie możesz usunąć własnego konta");
      return;
    }

    if (!confirm(`Czy na pewno chcesz usunąć użytkownika "${username}"?`)) {
      return;
    }

    setDeleting((prev) => ({ ...prev, [userId]: true }));

    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success("Użytkownik usunięty");
      await fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się usunąć użytkownika");
    } finally {
      setDeleting((prev) => ({ ...prev, [userId]: false }));
    }
  };

  const handleToggleActive = async (userId, currentStatus) => {
    try {
      await api.patch(`/admin/users/${userId}/${currentStatus ? 'deactivate' : 'activate'}`);
      toast.success(currentStatus ? "Użytkownik dezaktywowany" : "Użytkownik aktywowany");
      await fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się zmienić statusu");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">
            Użytkownicy ({users.length})
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Zarządzaj kontami użytkowników
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {users.map((user) => (
          <div
            key={user.id}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700 flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold">{user.username}</h3>
                  {user.is_admin && (
                    <Shield
                      size={16}
                      className="text-yellow-500"
                      title="Administrator"
                    />
                  )}
                  {!user.is_active && (
                    <span className="text-xs bg-red-600 px-2 py-1 rounded">
                      Nieaktywny
                    </span>
                  )}
                  {user.id === currentUser?.id && (
                    <span className="text-xs bg-blue-600 px-2 py-1 rounded">
                      To ty
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400">{user.email || "Brak email"}</p>
                {user.full_name && (
                  <p className="text-xs text-gray-500 mt-1">{user.full_name}</p>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setEditingUser(user)}
                className="p-2 hover:bg-gray-700 rounded text-blue-400 hover:text-blue-300"
                title="Edytuj"
              >
                <Edit2 size={16} />
              </button>

              <button
                onClick={() => handleDelete(user.id, user.username)}
                disabled={deleting[user.id] || user.id === currentUser?.id}
                className="p-2 hover:bg-gray-700 rounded text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                title={user.id === currentUser?.id ? "Nie możesz usunąć siebie" : "Usuń"}
              >
                {deleting[user.id] ? (
                  <Loader className="animate-spin" size={16} />
                ) : (
                  <Trash2 size={16} />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={fetchUsers}
        />
      )}
    </div>
  );
}

export default UsersManager;
