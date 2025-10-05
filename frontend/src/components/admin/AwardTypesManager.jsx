import { useEffect, useState } from "react";
import * as LucideIcons from "lucide-react";
import { Edit2, Loader, Plus, Sparkles, Trash2, Upload } from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";
import LucideIconSelector from "./LucideIconSelector";

function EditAwardTypeModal({ awardType, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    display_name: awardType.display_name,
    description: awardType.description || "",
    icon: awardType.icon,
    lucide_icon: awardType.lucide_icon || "",
    color: awardType.color,
    is_personal: awardType.is_personal,
  });
  const [loading, setLoading] = useState(false);
  const [showLucideSelector, setShowLucideSelector] = useState(false);
  const [uploadingIcon, setUploadingIcon] = useState(false);
  const [iconMode, setIconMode] = useState(
    awardType.icon_type === "custom" ? "custom" :
    awardType.icon_type === "lucide" ? "lucide" : "emoji"
  );

  const handleSave = async () => {
    setLoading(true);

    try {
      // Przygotuj dane do wysłania
      const updateData = {
        display_name: formData.display_name,
        description: formData.description,
        icon: formData.icon,
        color: formData.color,
        is_personal: formData.is_personal,
      };

      // Dodaj lucide_icon tylko jeśli iconMode === "lucide"
      if (iconMode === "lucide") {
        updateData.lucide_icon = formData.lucide_icon;
      } else if (iconMode === "emoji") {
        updateData.lucide_icon = ""; // Wyczyść lucide icon
      }

      await api.patch(`/admin/award-types/${awardType.id}`, updateData);
      toast.success("Typ nagrody zaktualizowany");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się zaktualizować");
    } finally {
      setLoading(false);
    }
  };

  const handleIconUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingIcon(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      await api.post(`/admin/award-types/${awardType.id}/icon`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success("Ikona uploaded");
      setIconMode("custom");
      onSuccess();
    } catch (err) {
      toast.error(
        err.response?.data?.message || "Nie udało się uploadować ikony"
      );
    } finally {
      setUploadingIcon(false);
    }
  };

  const handleClearIcon = () => {
    setIconMode("emoji");
    setFormData({ ...formData, lucide_icon: "" });
  };

  const renderCurrentIcon = () => {
    if (awardType.icon_type === "custom") {
      return (
        <img
          src={`${import.meta.env.VITE_API_URL}${awardType.icon_url}`}
          alt="Custom icon"
          className="w-16 h-16 rounded"
        />
      );
    } else if (awardType.icon_type === "lucide" && awardType.lucide_icon) {
      const componentName = awardType.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];
      return IconComponent ? (
        <IconComponent size={64} />
      ) : (
        <span className="text-4xl">🏆</span>
      );
    } else {
      return <span className="text-4xl">{awardType.icon}</span>;
    }
  };

  const renderIconPreview = () => {
    if (iconMode === "custom" && awardType.icon_type === "custom") {
      return (
        <img
          src={`${import.meta.env.VITE_API_URL}${awardType.icon_url}`}
          alt="Custom icon"
          className="w-16 h-16 rounded"
        />
      );
    } else if (iconMode === "lucide" && formData.lucide_icon) {
      const componentName = formData.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];
      return IconComponent ? (
        <IconComponent size={64} />
      ) : (
        <span className="text-4xl">🏆</span>
      );
    } else {
      return <span className="text-4xl">{formData.icon}</span>;
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 rounded-lg max-w-lg w-full p-6 border border-gray-700 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold mb-4">Edytuj typ nagrody</h2>

        {/* Current Icon Preview */}
        <div className="mb-4 p-4 bg-gray-900 rounded border border-gray-700 text-center">
          <p className="text-sm text-gray-400 mb-2">Aktualna ikona:</p>
          <div className="flex justify-center">{renderCurrentIcon()}</div>
          <p className="text-xs text-gray-500 mt-2">
            Typ:{" "}
            {awardType.icon_type === "custom"
              ? "Custom"
              : awardType.icon_type === "lucide"
              ? "Lucide"
              : "Emoji"}
          </p>
        </div>

        {/* Display Name */}
        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Nazwa wyświetlana</label>
          <input
            type="text"
            value={formData.display_name}
            onChange={(e) =>
              setFormData({ ...formData, display_name: e.target.value })
            }
            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
            maxLength={100}
          />
        </div>

        {/* Description */}
        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Opis</label>
          <textarea
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
            rows={3}
            maxLength={500}
          />
        </div>

        {/* Color */}
        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Kolor</label>
          <div className="flex gap-2">
            <input
              type="color"
              value={formData.color}
              onChange={(e) =>
                setFormData({ ...formData, color: e.target.value })
              }
              className="h-10 w-20 rounded cursor-pointer"
            />
            <input
              type="text"
              value={formData.color}
              onChange={(e) =>
                setFormData({ ...formData, color: e.target.value })
              }
              className="flex-1 bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
              pattern="^#[0-9A-Fa-f]{6}$"
            />
          </div>
        </div>

        {/* Icon Mode Selector */}
        <div className="mb-4">
          <label className="block text-gray-300 mb-2">Typ ikony</label>
          <div className="flex gap-2 mb-3">
            <button
              type="button"
              onClick={() => setIconMode("emoji")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                iconMode === "emoji"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              Emoji
            </button>
            <button
              type="button"
              onClick={() => setIconMode("lucide")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                iconMode === "lucide"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              Lucide
            </button>
            <button
              type="button"
              onClick={() => setIconMode("custom")}
              className={`flex-1 px-4 py-2 rounded-lg transition ${
                iconMode === "custom"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              Custom
            </button>
          </div>

          {/* Icon Preview */}
          <div className="p-4 bg-gray-900 rounded border border-gray-700 text-center mb-3">
            <p className="text-xs text-gray-400 mb-2">Podgląd:</p>
            <div className="flex justify-center">{renderIconPreview()}</div>
          </div>

          {/* Emoji Input */}
          {iconMode === "emoji" && (
            <div>
              <label className="block text-gray-300 mb-2">Emoji fallback</label>
              <input
                type="text"
                value={formData.icon}
                onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                maxLength={10}
                placeholder="🏆"
              />
            </div>
          )}

          {/* Lucide Selector */}
          {iconMode === "lucide" && (
            <div>
              <button
                type="button"
                onClick={() => setShowLucideSelector(true)}
                className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center justify-center gap-2"
              >
                <Sparkles size={20} />
                Wybierz Lucide Icon
              </button>
              {formData.lucide_icon && (
                <div className="text-sm text-gray-400 text-center mt-2">
                  Wybrano: <strong>{formData.lucide_icon}</strong>
                </div>
              )}
            </div>
          )}

          {/* Custom Upload */}
          {iconMode === "custom" && (
            <label className="block">
              <input
                type="file"
                accept="image/png,image/jpeg"
                onChange={handleIconUpload}
                className="hidden"
                id={`icon-upload-${awardType.id}`}
              />
              <div className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center justify-center gap-2 cursor-pointer">
                {uploadingIcon ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    Upload Custom Icon
                  </>
                )}
              </div>
            </label>
          )}
        </div>

        {/* Personal Flag */}
        {awardType.created_by_user_id && (
          <div className="mb-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_personal}
                onChange={(e) =>
                  setFormData({ ...formData, is_personal: e.target.checked })
                }
                className="w-4 h-4"
              />
              <span className="text-gray-300">
                Nagroda imienna (nie można usunąć)
              </span>
            </label>
          </div>
        )}

        {/* Info about protection */}
        {(awardType.is_system_award || awardType.is_personal) && (
          <div className="mb-4 p-3 bg-blue-900/20 border border-blue-700 rounded text-blue-300 text-sm">
            {awardType.is_system_award && (
              <p>⚠️ Nagroda systemowa - nie można usunąć</p>
            )}
            {awardType.is_personal && (
              <p>⚠️ Nagroda imienna - nie można usunąć</p>
            )}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
          >
            Anuluj
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
          >
            {loading ? "Zapisywanie..." : "Zapisz"}
          </button>
        </div>
      </div>

      {showLucideSelector && (
        <LucideIconSelector
          selectedIcon={formData.lucide_icon}
          onSelect={(icon) => {
            setFormData({ ...formData, lucide_icon: icon });
            setShowLucideSelector(false);
          }}
          onClose={() => setShowLucideSelector(false)}
        />
      )}
    </div>
  );
}

function AwardTypesManager() {
  const [awardTypes, setAwardTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingType, setEditingType] = useState(null);
  const [deleting, setDeleting] = useState({});

  useEffect(() => {
    fetchAwardTypes();
  }, []);

  const fetchAwardTypes = async () => {
    try {
      const response = await api.get("/admin/award-types/detailed");
      setAwardTypes(response.data);
    } catch (err) {
      toast.error("Nie udało się załadować typów nagród");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (typeId, typeName) => {
    if (!confirm(`Czy na pewno chcesz usunąć "${typeName}"?`)) return;

    setDeleting((prev) => ({ ...prev, [typeId]: true }));

    try {
      await api.delete(`/admin/award-types/${typeId}/force`);
      toast.success("Typ nagrody usunięty");
      await fetchAwardTypes();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się usunąć");
    } finally {
      setDeleting((prev) => ({ ...prev, [typeId]: false }));
    }
  };

  const renderIcon = (awardType) => {
    if (awardType.icon_type === "custom") {
      return (
        <img
          src={`${import.meta.env.VITE_API_URL}${awardType.icon_url}`}
          alt={awardType.display_name}
          className="w-12 h-12 rounded"
        />
      );
    } else if (awardType.icon_type === "lucide" && awardType.lucide_icon) {
      const componentName = awardType.lucide_icon
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join("");
      const IconComponent = LucideIcons[componentName];
      return IconComponent ? (
        <IconComponent size={48} />
      ) : (
        <span className="text-4xl">🏆</span>
      );
    } else {
      return <span className="text-4xl">{awardType.icon}</span>;
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
        <h2 className="text-xl font-semibold">
          Typy Nagród ({awardTypes.length})
        </h2>
        <button
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2"
          disabled
        >
          <Plus size={20} />
          Dodaj typ (TODO)
        </button>
      </div>

      <div className="space-y-3">
        {awardTypes.map((type) => (
          <div
            key={type.id}
            className="bg-gray-800 rounded-lg p-4 border border-gray-700 flex items-center gap-4"
          >
            {/* Icon */}
            <div className="flex-shrink-0">{renderIcon(type)}</div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold">{type.display_name}</h3>
                {type.is_system_award && (
                  <span className="text-xs bg-purple-600 px-2 py-1 rounded">
                    System
                  </span>
                )}
                {type.is_personal && (
                  <span className="text-xs bg-blue-600 px-2 py-1 rounded">
                    Personal
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-400">{type.description}</p>
              <div className="flex items-center gap-3 mt-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: type.color }}
                />
                <span className="text-xs text-gray-500">{type.name}</span>
                <span className="text-xs text-gray-500">
                  Icon: {type.icon_type}
                  {type.lucide_icon && ` (${type.lucide_icon})`}
                </span>
                {type.created_by_username && (
                  <span className="text-xs text-gray-500">
                    by {type.created_by_username}
                  </span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => setEditingType(type)}
                className="p-2 hover:bg-gray-700 rounded text-blue-400 hover:text-blue-300"
                title="Edytuj"
              >
                <Edit2 size={16} />
              </button>
              <button
                onClick={() => handleDelete(type.id, type.display_name)}
                disabled={
                  deleting[type.id] || type.is_system_award || type.is_personal
                }
                className="p-2 hover:bg-gray-700 rounded text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                title={
                  type.is_system_award || type.is_personal
                    ? "Nie można usunąć"
                    : "Usuń"
                }
              >
                {deleting[type.id] ? (
                  <Loader className="animate-spin" size={16} />
                ) : (
                  <Trash2 size={16} />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingType && (
        <EditAwardTypeModal
          awardType={editingType}
          onClose={() => setEditingType(null)}
          onSuccess={fetchAwardTypes}
        />
      )}
    </div>
  );
}

export default AwardTypesManager;
