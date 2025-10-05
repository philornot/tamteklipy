import { useEffect, useState } from "react";
import { Award, Loader, Plus, Trash2, Edit2 } from "lucide-react";
import * as LucideIcons from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";
import CreateAwardModal from "../components/awards/CreateAwardModal";
import EditMyAwardModal from "../components/awards/EditMyAwardModal";

function MyAwardsPage() {
  const [customAwards, setCustomAwards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAward, setEditingAward] = useState(null);

  useEffect(() => {
    fetchCustomAwards();
  }, []);

  const fetchCustomAwards = async () => {
    try {
      const response = await api.get("/my-awards/my-award-types");
      setCustomAwards(response.data);
    } catch (err) {
      console.error("Failed to fetch custom awards:", err);
      toast.error("Nie udało się załadować nagród");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (awardId, awardName) => {
    if (!confirm(`Czy na pewno chcesz usunąć nagrodę "${awardName}"?`)) return;

    try {
      await api.delete(`/my-awards/my-award-types/${awardId}`);
      toast.success("Nagroda usunięta");
      fetchCustomAwards();
    } catch (err) {
      toast.error(
        err.response?.data?.message || "Nie udało się usunąć nagrody"
      );
    }
  };

  const renderIcon = (award) => {
    if (award.icon_url) {
      return (
        <img
          src={`${import.meta.env.VITE_API_URL}${award.icon_url}`}
          alt={award.display_name}
          className="w-16 h-16 rounded"
        />
      );
    } else if (award.lucide_icon) {
      const componentName = award.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];
      return IconComponent ? (
        <IconComponent size={64} />
      ) : (
        <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center text-3xl">
          {award.icon}
        </div>
      );
    } else {
      return (
        <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center text-3xl">
          {award.icon}
        </div>
      );
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center">
        <Loader className="animate-spin text-blue-500" size={48} />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Moje Nagrody</h1>
          <p className="text-gray-400">
            Własne nagrody ({customAwards.length}/5)
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          disabled={customAwards.length >= 5}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          title={
            customAwards.length >= 5 ? "Maksymalnie 5 nagród" : "Utwórz nagrodę"
          }
        >
          <Plus size={20} />
          Nowa nagroda
        </button>
      </div>

      {customAwards.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
          <Award size={48} className="mx-auto mb-4 text-gray-600" />
          <p className="text-gray-400 mb-4">Nie masz jeszcze własnych nagród</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            Utwórz pierwszą nagrodę
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {customAwards.map((award) => (
            <div
              key={award.id}
              className="bg-gray-800 rounded-lg p-4 border border-gray-700"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">{renderIcon(award)}</div>

                <div className="flex-1 min-w-0">
                  {/* Dodanie odznaki "Imienna" przy tytule */}
                  <h3 className="font-semibold text-lg mb-1 flex items-center gap-2">
                    {award.display_name}
                    {award.is_personal && (
                      <span className="text-xs bg-blue-600 px-2 py-1 rounded">
                        Imienna
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-gray-400 mb-2">
                    {award.description}
                  </p>
                  <div className="flex items-center gap-2">
                    <div
                      className="w-6 h-6 rounded"
                      style={{ backgroundColor: award.color }}
                    />
                    <span className="text-xs text-gray-500">{award.color}</span>
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => setEditingAward(award)}
                    className="p-2 text-blue-400 hover:text-blue-300 hover:bg-gray-700 rounded transition"
                    title="Edytuj nagrodę"
                  >
                    <Edit2 size={20} />
                  </button>

                  {/* Pokaż przycisk Delete, tylko jeśli nie jest personal */}
                  {!award.is_personal && (
                    <button
                      onClick={() => handleDelete(award.id, award.display_name)}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-700 rounded transition"
                      title="Usuń nagrodę"
                    >
                      <Trash2 size={20} />
                    </button>
                  )}

                  {/* Usunięto boczną etykietę "Imienna", ponieważ dodano badge przy tytule */}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateAwardModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={fetchCustomAwards}
        />
      )}

      {editingAward && (
        <EditMyAwardModal
          award={editingAward}
          onClose={() => setEditingAward(null)}
          onSuccess={() => {
            fetchCustomAwards();
            setEditingAward(null);
          }}
        />
      )}
    </div>
  );
}

export default MyAwardsPage;
