import { useState, useEffect } from "react";
import { Plus, Edit2, Trash2, Loader } from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";

function AwardTypesManager() {
  const [awardTypes, setAwardTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAwardTypes();
  }, []);

  const fetchAwardTypes = async () => {
    try {
      const response = await api.get("/admin/award-types");
      setAwardTypes(response.data);
    } catch (err) {
      toast.error("Nie udało się załadować typów nagród");
    } finally {
      setLoading(false);
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
        <button className="btn-primary flex items-center gap-2" disabled>
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
            {type.icon_url ? (
              <img
                src={`${import.meta.env.VITE_API_URL}${type.icon_url}`}
                alt={type.display_name}
                className="w-12 h-12 rounded"
              />
            ) : (
              <div className="w-12 h-12 rounded bg-gray-700 flex items-center justify-center text-2xl">
                {type.icon}
              </div>
            )}

            {/* Info */}
            <div className="flex-1">
              <h3 className="font-semibold">{type.display_name}</h3>
              <p className="text-sm text-gray-400">{type.description}</p>
              <div className="flex items-center gap-2 mt-1">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: type.color }}
                />
                <span className="text-xs text-gray-500">{type.name}</span>
              </div>
            </div>

            {/* Actions - TODO: implement edit/delete modals */}
            <div className="flex gap-2">
              <button
                className="p-2 hover:bg-gray-700 rounded opacity-50 cursor-not-allowed"
                title="Edytuj (TODO)"
                disabled
              >
                <Edit2 size={16} />
              </button>
              <button
                className="p-2 hover:bg-gray-700 rounded text-red-400 opacity-50 cursor-not-allowed"
                title="Usuń (TODO)"
                disabled
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AwardTypesManager;
