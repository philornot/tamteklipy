import { useEffect, useState } from "react";
import {
  Edit2,
  Shield,
  Trash2,
  Loader,
  Plus,
  X,
  Save,
  UserX,
  UserCheck,
  CheckSquare,
} from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";
import { useAuth } from "../../hooks/useAuth";
import { useBulkSelection } from "../../hooks/useBulkSelection";

// ============================================
// EDIT USER MODAL
// ============================================
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

// ============================================
// CREATE USER MODAL
// ============================================
function CreateUserModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    full_name: "",
    is_admin: false,
  });
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!formData.username) {
      toast.error("Username jest wymagany");
      return;
    }

    setLoading(true);

    try {
      const response = await api.post("/admin/users", formData);
      toast.success(
        `Użytkownik ${formData.username} utworzony! ${response.data.message}`
      );
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(
        err.response?.data?.message || "Nie udało się utworzyć użytkownika"
      );
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
          <h2 className="text-xl font-bold">Dodaj użytkownika</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-gray-300 mb-2">Username *</label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
              placeholder="jan_kowalski"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-2">
              Email (opcjonalny)
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
              placeholder="jan@example.com"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-2">
              Imię i nazwisko (opcjonalne)
            </label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) =>
                setFormData({ ...formData, full_name: e.target.value })
              }
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
              placeholder="Jan Kowalski"
            />
          </div>

          <div>
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

          <div className="p-3 bg-blue-900/20 border border-blue-700 rounded text-blue-300 text-sm">
            Użytkownik zostanie utworzony bez hasła. Może je ustawić później w
            profilu.
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
            >
              Anuluj
            </button>
            <button
              onClick={handleCreate}
              disabled={loading || !formData.username}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  Tworzenie...
                </>
              ) : (
                <>
                  <Plus size={16} />
                  Utwórz
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// ADMIN USERS TOOLBAR (Bulk Actions)
// ============================================
function AdminUsersToolbar({ selectedCount, selectedUsers, currentUserId, onActionComplete, onCancel }) {
  const [loading, setLoading] = useState(false);

  const handleBulkDeactivate = async () => {
    const usersToDeactivate = selectedUsers.filter(u => u.id !== currentUserId && u.is_active);

    if (usersToDeactivate.length === 0) {
      toast.error('Nie można dezaktywować wybranych użytkowników');
      return;
    }

    if (!confirm(`Czy na pewno chcesz dezaktywować ${usersToDeactivate.length} użytkowników?`)) {
      return;
    }

    setLoading(true);

    let successCount = 0;
    let failCount = 0;

    for (const user of usersToDeactivate) {
      try {
        await api.patch(`/admin/users/${user.id}`, { is_active: false });
        successCount++;
      } catch (err) {
        console.error(`Failed to deactivate user ${user.id}:`, err);
        failCount++;
      }
    }

    setLoading(false);

    if (successCount > 0) {
      toast.success(`Dezaktywowano ${successCount} użytkowników`);
      onActionComplete();
    }

    if (failCount > 0) {
      toast.error(`Nie udało się dezaktywować ${failCount} użytkowników`);
    }
  };

  const handleBulkActivate = async () => {
    const usersToActivate = selectedUsers.filter(u => !u.is_active);

    if (usersToActivate.length === 0) {
      toast.error('Nie można aktywować wybranych użytkowników');
      return;
    }

    if (!confirm(`Czy na pewno chcesz aktywować ${usersToActivate.length} użytkowników?`)) {
      return;
    }

    setLoading(true);

    let successCount = 0;
    let failCount = 0;

    for (const user of usersToActivate) {
      try {
        await api.patch(`/admin/users/${user.id}`, { is_active: true });
        successCount++;
      } catch (err) {
        console.error(`Failed to activate user ${user.id}:`, err);
        failCount++;
      }
    }

    setLoading(false);

    if (successCount > 0) {
      toast.success(`Aktywowano ${successCount} użytkowników`);
      onActionComplete();
    }

    if (failCount > 0) {
      toast.error(`Nie udało się aktywować ${failCount} użytkowników`);
    }
  };

  const handleBulkDelete = async () => {
    const usersToDelete = selectedUsers.filter(u => u.id !== currentUserId);

    if (usersToDelete.length === 0) {
      toast.error('Nie można usunąć wybranych użytkowników');
      return;
    }

    if (!confirm(`Czy na pewno chcesz USUNĄĆ ${usersToDelete.length} użytkowników? Ta operacja jest nieodwracalna!`)) {
      return;
    }

    setLoading(true);

    let successCount = 0;
    let failCount = 0;

    for (const user of usersToDelete) {
      try {
        await api.delete(`/admin/users/${user.id}`);
        successCount++;
      } catch (err) {
        console.error(`Failed to delete user ${user.id}:`, err);
        failCount++;
      }
    }

    setLoading(false);

    if (successCount > 0) {
      toast.success(`Usunięto ${successCount} użytkowników`);
      onActionComplete();
    }

    if (failCount > 0) {
      toast.error(`Nie udało się usunąć ${failCount} użytkowników`);
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 animate-slideUp">
      <div className="bg-gray-900 border border-blue-500/50 rounded-2xl shadow-2xl shadow-blue-500/20 backdrop-blur-xl">
        <div className="px-6 py-4 flex items-center gap-4">
          {/* Selection info */}
          <div className="flex items-center gap-3 pr-4 border-r border-gray-700">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
              <span className="text-blue-400 font-bold text-sm">
                {selectedCount}
              </span>
            </div>
            <span className="text-sm text-gray-300">
              {selectedCount === 1 ? 'użytkownik zaznaczony' : 'użytkowników zaznaczonych'}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleBulkActivate}
              disabled={loading}
              className="px-4 py-2 bg-green-600/90 hover:bg-green-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Aktywuj zaznaczonych"
            >
              <UserCheck size={16} />
              <span className="hidden sm:inline">Aktywuj</span>
            </button>

            <button
              onClick={handleBulkDeactivate}
              disabled={loading}
              className="px-4 py-2 bg-yellow-600/90 hover:bg-yellow-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Dezaktywuj zaznaczonych"
            >
              <UserX size={16} />
              <span className="hidden sm:inline">Dezaktywuj</span>
            </button>

            <div className="w-px h-6 bg-gray-700 mx-1" />

            <button
              onClick={handleBulkDelete}
              disabled={loading}
              className="px-4 py-2 bg-red-600/90 hover:bg-red-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Usuń zaznaczonych"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  <span className="hidden sm:inline">Przetwarzanie...</span>
                </>
              ) : (
                <>
                  <Trash2 size={16} />
                  <span className="hidden sm:inline">Usuń</span>
                </>
              )}
            </button>
          </div>

          {/* Cancel button */}
          <button
            onClick={onCancel}
            disabled={loading}
            className="p-2 hover:bg-gray-800 rounded-lg transition text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            title="Anuluj (ESC)"
          >
            <X size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================
// MAIN USERS MANAGER COMPONENT
// ============================================
function UsersManager() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingUser, setEditingUser] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleting, setDeleting] = useState({});

  // Bulk selection
  const {
    selectedIds,
    selectedCount,
    toggleSelection,
    selectAll,
    clearSelection,
    isSelected,
    hasSelection,
  } = useBulkSelection(users);

  useEffect(() => {
    fetchUsers();
  }, []);

  // ESC key handler
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && hasSelection) {
        clearSelection();
      }
    };

    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [hasSelection, clearSelection]);

  const fetchUsers = async () => {
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch {
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
      toast.error(
        err.response?.data?.message || "Nie udało się usunąć użytkownika"
      );
    } finally {
      setDeleting((prev) => ({ ...prev, [userId]: false }));
    }
  };

  const handleToggleActive = async (userId, isActive) => {
    const action = isActive ? "dezaktywowany" : "aktywowany";

    if (!confirm(`Czy na pewno chcesz ${action} tego użytkownika?`)) {
      return;
    }

    setLoading(true);

    try {
      await api.patch(`/admin/users/${userId}`, {
        is_active: !isActive,
      });
      toast.success(`Użytkownik został ${action}`);
      fetchUsers();
    } catch (err) {
      toast.error(
        err.response?.data?.message ||
          "Nie udało się zmienić statusu użytkownika"
      );
    } finally {
      setLoading(false);
    }
  };

  const selectedUsers = users.filter(u => selectedIds.includes(u.id));

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
            {hasSelection && (
              <span className="text-blue-400 ml-2">
                • {selectedCount} zaznaczonych
              </span>
            )}
          </p>
        </div>

        <div className="flex gap-3">
          {/* Select All Button */}
          {users.length > 0 && (
            <button
              onClick={hasSelection ? clearSelection : selectAll}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-300 ${
                hasSelection
                  ? 'bg-blue-600 border-blue-500 text-white hover:bg-blue-700'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-500 hover:text-blue-400'
              }`}
            >
              <CheckSquare size={18} />
              <span className="font-medium">
                {hasSelection ? 'Odznacz' : 'Zaznacz'}
              </span>
            </button>
          )}

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2"
          >
            <Plus size={20} />
            Dodaj użytkownika
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {users.map((user, index) => (
          <div
            key={user.id}
            className={`bg-gray-800 rounded-lg p-4 border flex items-center justify-between transition ${
              isSelected(user.id)
                ? 'border-blue-500 bg-blue-900/20'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="flex items-center gap-4">
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={isSelected(user.id)}
                onChange={(e) => toggleSelection(user.id, index, e.shiftKey)}
                className="w-5 h-5 rounded border-gray-600"
              />

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
                <p className="text-sm text-gray-400">
                  {user.email || "Brak email"}
                </p>
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

              {/* Toggle active status */}
              <button
                onClick={() => handleToggleActive(user.id, user.is_active)}
                className="p-2 hover:bg-gray-700 rounded text-yellow-400 hover:text-yellow-300"
                title={
                  user.is_active
                    ? "Dezaktywuj użytkownika"
                    : "Aktywuj użytkownika"
                }
              >
                {user.is_active ? <UserX size={16} /> : <UserCheck size={16} />}
              </button>

              <button
                onClick={() => handleDelete(user.id, user.username)}
                disabled={deleting[user.id] || user.id === currentUser?.id}
                className="p-2 hover:bg-gray-700 rounded text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                title={
                  user.id === currentUser?.id
                    ? "Nie możesz usunąć siebie"
                    : "Usuń"
                }
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

      {/* Floating Toolbar */}
      {hasSelection && (
        <AdminUsersToolbar
          selectedCount={selectedCount}
          selectedUsers={selectedUsers}
          currentUserId={currentUser?.id}
          onActionComplete={() => {
            clearSelection();
            fetchUsers();
          }}
          onCancel={clearSelection}
        />
      )}

      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={fetchUsers}
        />
      )}

      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={fetchUsers}
        />
      )}
    </div>
  );
}

export default UsersManager;
