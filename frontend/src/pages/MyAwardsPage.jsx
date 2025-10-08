import { useEffect, useState } from "react";
import { Award, Loader, Plus, Trash2, Edit2, Sparkles } from "lucide-react";
import * as LucideIcons from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";
import CreateAwardModal from "../components/awards/CreateAwardModal";
import EditMyAwardModal from "../components/awards/EditMyAwardModal";
import { getBaseUrl } from "../utils/urlHelper";
import usePageTitle from "../hooks/usePageTitle.js";

function MyAwardsPage() {
  usePageTitle("Moje nagrody");
  const [customAwards, setCustomAwards] = useState([]);
  const [awardTypesMap, setAwardTypesMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAward, setEditingAward] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const awardsResponse = await api.get("/my-awards/my-award-types");
      setCustomAwards(awardsResponse.data);

      const typesResponse = await api.get("/admin/award-types/detailed");
      const typesMap = {};
      typesResponse.data.forEach(type => {
        typesMap[type.id] = type;
      });
      setAwardTypesMap(typesMap);
    } catch (err) {
      console.error("Failed to fetch data:", err);
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
      fetchData();
    } catch (err) {
      toast.error(
        err.response?.data?.message || "Nie udało się usunąć nagrody"
      );
    }
  };

  const renderIcon = (award) => {
    const awardType = awardTypesMap[award.id];

    if (!awardType) {
      return (
        <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center text-3xl">
          {award.icon || "🏆"}
        </div>
      );
    }

    if (awardType.icon_type === "custom" && awardType.icon_url) {
      return (
        <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center overflow-hidden">
          <img
            src={`${getBaseUrl()}${awardType.icon_url}`}
            alt={awardType.display_name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
              const parent = e.target.parentElement;
              parent.innerHTML = `<span class="text-3xl">${awardType.icon || "🏆"}</span>`;
            }}
          />
        </div>
      );
    }

    if (awardType.icon_type === "lucide" && awardType.lucide_icon) {
      const componentName = awardType.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];

      if (IconComponent) {
        return (
          <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center">
            <IconComponent size={48} />
          </div>
        );
      }
    }

    return (
      <div className="w-16 h-16 rounded bg-gray-700 flex items-center justify-center text-3xl">
        {awardType.icon || award.icon || "🏆"}
      </div>
    );
  };

  const getIconTypeLabel = (award) => {
    const awardType = awardTypesMap[award.id];
    if (!awardType) return "Emoji";

    if (awardType.icon_type === "custom") return "Custom";
    if (awardType.icon_type === "lucide") return "Lucide";
    return "Emoji";
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center">
        <Loader className="animate-spin text-purple-500" size={48} />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold">Moje Nagrody</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={customAwards.length >= 5}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors flex items-center gap-2"
            title={
              customAwards.length >= 5 ? "Maksymalnie 5 nagród" : "Utwórz nagrodę"
            }
          >
            <Plus size={20} />
            Nowa nagroda
          </button>
        </div>
        <p className="text-gray-400">
          Własne nagrody ({customAwards.length}/5)
        </p>
      </div>

      {customAwards.length === 0 ? (
        <div className="text-center py-16 bg-gray-800 rounded-lg border border-gray-700">
          <Award size={64} className="mx-auto mb-4 text-gray-600" />
          <p className="text-xl text-gray-300 mb-2">Nie masz jeszcze własnych nagród</p>
          <p className="text-gray-500 mb-6">
            Stwórz własne nagrody do przyznawania klipom
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors inline-flex items-center gap-2"
          >
            <Sparkles size={20} />
            Utwórz pierwszą nagrodę
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {customAwards.map((award) => {
              const awardType = awardTypesMap[award.id];

              return (
                <div
                  key={award.id}
                  className="bg-gray-800 rounded-lg p-5 border border-gray-700 hover:border-purple-600 transition-colors"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className="flex-shrink-0">{renderIcon(award)}</div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg truncate">
                          {award.display_name}
                        </h3>
                        {award.is_personal && (
                          <span className="text-xs bg-purple-600 px-2 py-0.5 rounded flex-shrink-0">
                            Imienna
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                        {award.description || "Brak opisu"}
                      </p>

                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <div className="flex items-center gap-1.5">
                          <div
                            className="w-4 h-4 rounded border border-gray-600"
                            style={{ backgroundColor: award.color }}
                          />
                          <span>{award.color}</span>
                        </div>

                        <span className="text-gray-600">•</span>

                        <span>{getIconTypeLabel(award)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-3 border-t border-gray-700">
                    <button
                      onClick={() => setEditingAward(award)}
                      className="flex-1 py-2 px-3 text-purple-400 hover:text-purple-300 hover:bg-gray-700 rounded transition-colors flex items-center justify-center gap-2 text-sm font-medium"
                    >
                      <Edit2 size={16} />
                      Edytuj
                    </button>

                    {!award.is_personal && (
                      <button
                        onClick={() => handleDelete(award.id, award.display_name)}
                        className="flex-1 py-2 px-3 text-red-400 hover:text-red-300 hover:bg-gray-700 rounded transition-colors flex items-center justify-center gap-2 text-sm font-medium"
                      >
                        <Trash2 size={16} />
                        Usuń
                      </button>
                    )}

                    {award.is_personal && (
                      <div className="flex-1 py-2 px-3 text-gray-500 text-center text-sm">
                        Chroniona
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Uproszczony info box */}
          <div className="bg-gray-800 rounded-lg p-4 border border-purple-700/30">
            <h3 className="font-semibold mb-2 text-sm flex items-center gap-2 text-purple-400">
              <Sparkles size={16} />
              Informacje
            </h3>
            <ul className="text-sm text-gray-400 space-y-1">
              <li>• Maksymalnie 5 własnych nagród</li>
              <li>• Nagrody imienne są chronione</li>
              <li>• Ikony: Lucide lub własne obrazki</li>
            </ul>
          </div>
        </>
      )}

      {showCreateModal && (
        <CreateAwardModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            fetchData();
            setShowCreateModal(false);
          }}
        />
      )}

      {editingAward && (
        <EditMyAwardModal
          award={editingAward}
          onClose={() => setEditingAward(null)}
          onSuccess={() => {
            fetchData();
            setEditingAward(null);
          }}
        />
      )}
    </div>
  );
}

export default MyAwardsPage;
