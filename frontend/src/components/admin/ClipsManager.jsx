import { useState, useEffect } from "react";
import {
  Trash2,
  Search,
  Film,
  Image,
  Loader,
  Calendar,
  User,
  HardDrive,
  Award
} from "lucide-react";
import api from "../../services/api.js";
import toast from "react-hot-toast";

function ClipsManager() {
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [deleting, setDeleting] = useState({});

  useEffect(() => {
    fetchClips();
  }, [currentPage, filterType]);

  const fetchClips = async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        limit: 10,
        sort_by: "created_at",
        sort_order: "desc"
      };

      if (filterType) {
        params.clip_type = filterType;
      }

      const response = await api.get("/files/clips", { params });
      setClips(response.data.clips);
      setTotalPages(response.data.pages);
    } catch (err) {
      toast.error("Nie udało się załadować klipów");
      console.error("Failed to fetch clips:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (clipId, clipName) => {
    if (!confirm(`Czy na pewno chcesz usunąć klip "${clipName}"?`)) {
      return;
    }

    setDeleting(prev => ({ ...prev, [clipId]: true }));

    try {
      // Endpoint do implementacji w backendzie: DELETE /api/admin/clips/{clipId}
      await api.delete(`/admin/clips/${clipId}`);

      toast.success("Klip został usunięty");

      // Odśwież listę
      await fetchClips();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się usunąć klipu");
      console.error("Failed to delete clip:", err);
    } finally {
      setDeleting(prev => ({ ...prev, [clipId]: false }));
    }
  };

  const formatFileSize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("pl-PL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return "-";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, "0")}`;
  };

  const filteredClips = clips.filter(clip =>
    clip.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    clip.uploader_username.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading && clips.length === 0) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">
          Zarządzanie klipami ({clips.length})
        </h2>

        {/* Filters */}
        <div className="flex gap-4 mb-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Szukaj po nazwie lub użytkowniku..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field w-full pl-10"
            />
          </div>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(1);
            }}
            className="input-field"
          >
            <option value="">Wszystkie typy</option>
            <option value="video">Video</option>
            <option value="screenshot">Screenshot</option>
          </select>
        </div>
      </div>

      {/* Clips Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                <th className="text-left p-4 text-gray-300">ID</th>
                <th className="text-left p-4 text-gray-300">Typ</th>
                <th className="text-left p-4 text-gray-300">Nazwa pliku</th>
                <th className="text-left p-4 text-gray-300">Uploader</th>
                <th className="text-left p-4 text-gray-300">Rozmiar</th>
                <th className="text-left p-4 text-gray-300">Czas</th>
                <th className="text-left p-4 text-gray-300">Nagrody</th>
                <th className="text-left p-4 text-gray-300">Data</th>
                <th className="text-left p-4 text-gray-300">Akcje</th>
              </tr>
            </thead>
            <tbody>
              {filteredClips.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-8 text-gray-400">
                    {searchTerm ? "Brak wyników wyszukiwania" : "Brak klipów"}
                  </td>
                </tr>
              ) : (
                filteredClips.map((clip) => (
                  <tr
                    key={clip.id}
                    className="border-b border-gray-700 hover:bg-gray-700/50 transition"
                  >
                    <td className="p-4 text-gray-400">#{clip.id}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {clip.clip_type === "video" ? (
                          <>
                            <Film size={16} className="text-blue-400" />
                            <span className="text-sm">Video</span>
                          </>
                        ) : (
                          <>
                            <Image size={16} className="text-green-400" />
                            <span className="text-sm">Image</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="max-w-xs truncate" title={clip.filename}>
                        {clip.filename}
                      </div>
                      {clip.has_thumbnail && (
                        <span className="text-xs text-gray-500">✓ thumbnail</span>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <User size={14} className="text-gray-400" />
                        <span>{clip.uploader_username}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <HardDrive size={14} className="text-gray-400" />
                        <span className="text-sm">{formatFileSize(clip.file_size)}</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm">
                      {formatDuration(clip.duration)}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Award size={14} className="text-yellow-500" />
                        <span>{clip.award_count || 0}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Calendar size={14} className="text-gray-400" />
                        <span className="text-sm">{formatDate(clip.created_at)}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handleDelete(clip.id, clip.filename)}
                        disabled={deleting[clip.id]}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-600 rounded transition disabled:opacity-50"
                        title="Usuń klip"
                      >
                        {deleting[clip.id] ? (
                          <Loader className="animate-spin" size={16} />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Poprzednia
          </button>

          <span className="px-4 py-2">
            Strona {currentPage} z {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Następna
          </button>
        </div>
      )}

      {/* Info about backend endpoint */}
      {clips.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-700 rounded text-yellow-300 text-sm">
          <strong>Uwaga:</strong> Funkcja usuwania wymaga implementacji endpointu DELETE /api/admin/clips/:id w backendzie
        </div>
      )}
    </div>
  );
}

export default ClipsManager;