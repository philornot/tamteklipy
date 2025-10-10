import { useState, useEffect, useCallback } from "react";
import {
  Trash2,
  Search,
  Film,
  Image,
  Loader,
  Calendar,
  User,
  HardDrive,
  Award,
  CheckSquare,
  X,
  RefreshCw
} from "lucide-react";
import api from "../../services/api.js";
import toast from "react-hot-toast";
import { useBulkSelection } from "../../hooks/useBulkSelection.js";

function AdminFloatingToolbar({ selectedCount, selectedIds, onActionComplete, onCancel }) {
  const [loading, setLoading] = useState(false);

  const handleBulkDelete = async () => {
    if (!confirm(`Czy na pewno chcesz usunąć ${selectedCount} ${selectedCount === 1 ? 'klip' : 'klipy'}?`)) {
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/files/clips/bulk-action', {
        clip_ids: selectedIds,
        action: 'delete',
      });

      if (response.data.success) {
        toast.success(response.data.message);
        onActionComplete('delete', response.data);
      } else {
        toast.error(response.data.message);
      }
    } catch (err) {
      console.error('Bulk delete failed:', err);
      toast.error(err.response?.data?.message || 'Nie udało się usunąć klipów');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkRestore = async () => {
    // TODO: Implementacja bulk restore po dodaniu endpointu
    toast.error('Funkcja przywracania będzie dostępna wkrótce');
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 animate-slideUp">
      <div className="bg-gray-900 border border-red-500/50 rounded-2xl shadow-2xl shadow-red-500/20 backdrop-blur-xl">
        <div className="px-6 py-4 flex items-center gap-4">
          {/* Selection info */}
          <div className="flex items-center gap-3 pr-4 border-r border-gray-700">
            <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
              <span className="text-red-400 font-bold text-sm">
                {selectedCount}
              </span>
            </div>
            <span className="text-sm text-gray-300">
              {selectedCount === 1 ? 'klip zaznaczony' : 'klipy zaznaczone'}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleBulkRestore}
              disabled={loading}
              className="px-4 py-2 bg-green-600/90 hover:bg-green-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Przywróć zaznaczone"
            >
              <RefreshCw size={16} />
              <span className="hidden sm:inline">Przywróć</span>
            </button>

            <div className="w-px h-6 bg-gray-700 mx-1" />

            <button
              onClick={handleBulkDelete}
              disabled={loading}
              className="px-4 py-2 bg-red-600/90 hover:bg-red-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Usuń zaznaczone"
            >
              {loading ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  <span className="hidden sm:inline">Usuwanie...</span>
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

function ClipsManager() {
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
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
  } = useBulkSelection(clips);

  const fetchClips = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        limit: 20, // Więcej klipów dla admina
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
  }, [currentPage, filterType]);

  useEffect(() => {
    fetchClips();
  }, [fetchClips]);

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

  const handleDelete = async (clipId, clipName) => {
    if (!confirm(`Czy na pewno chcesz usunąć klip "${clipName}"?`)) {
      return;
    }

    setDeleting(prev => ({ ...prev, [clipId]: true }));

    try {
      await api.delete(`/admin/clips/${clipId}`);
      toast.success("Klip został usunięty");
      await fetchClips();
    } catch (err) {
      toast.error(err.response?.data?.message || "Nie udało się usunąć klipu");
      console.error("Failed to delete clip:", err);
    } finally {
      setDeleting(prev => ({ ...prev, [clipId]: false }));
    }
  };

const handleBulkActionComplete = async (action, result) => {
  console.log('Bulk action completed:', action, result);
  clearSelection();
  await fetchClips();
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
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">
              Zarządzanie klipami ({clips.length})
            </h2>
            {hasSelection && (
              <p className="text-sm text-red-400 mt-1">
                Zaznaczono {selectedCount} {selectedCount === 1 ? 'klip' : 'klipów'}
              </p>
            )}
          </div>

          {/* Select All Button */}
          {clips.length > 0 && (
            <button
              onClick={hasSelection ? clearSelection : selectAll}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-300 ${
                hasSelection
                  ? 'bg-red-600 border-red-500 text-white hover:bg-red-700'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-red-500 hover:text-red-400'
              }`}
            >
              <CheckSquare size={18} />
              <span className="font-medium">
                {hasSelection ? 'Odznacz wszystkie' : 'Zaznacz wszystkie'}
              </span>
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Szukaj po nazwie lub użytkowniku..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 pl-10 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition"
            />
          </div>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(1);
              clearSelection();
            }}
            className="bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition"
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
                <th className="text-left p-4 text-gray-300 w-12">
                  {/* Checkbox header */}
                  <input
                    type="checkbox"
                    checked={hasSelection && selectedCount === filteredClips.length}
                    onChange={hasSelection ? clearSelection : selectAll}
                    className="w-4 h-4 rounded border-gray-600"
                  />
                </th>
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
                  <td colSpan="10" className="text-center py-8 text-gray-400">
                    {searchTerm ? "Brak wyników wyszukiwania" : "Brak klipów"}
                  </td>
                </tr>
              ) : (
                filteredClips.map((clip, index) => (
                  <tr
                    key={clip.id}
                    className={`border-b border-gray-700 transition ${
                      isSelected(clip.id)
                        ? 'bg-red-900/20 hover:bg-red-900/30'
                        : 'hover:bg-gray-700/50'
                    }`}
                  >
                    <td className="p-4">
                      <input
                        type="checkbox"
                        checked={isSelected(clip.id)}
                        onChange={(e) => toggleSelection(clip.id, index, e.shiftKey)}
                        className="w-4 h-4 rounded border-gray-600"
                      />
                    </td>
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

      {/* Floating Toolbar */}
      {hasSelection && (
        <AdminFloatingToolbar
          selectedCount={selectedCount}
          selectedIds={selectedIds}
          onActionComplete={handleBulkActionComplete}
          onCancel={clearSelection}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => {
              setCurrentPage(prev => Math.max(1, prev - 1));
              clearSelection();
            }}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Poprzednia
          </button>

          <span className="px-4 py-2 text-gray-300">
            Strona {currentPage} z {totalPages}
          </span>

          <button
            onClick={() => {
              setCurrentPage(prev => Math.min(totalPages, prev + 1));
              clearSelection();
            }}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Następna
          </button>
        </div>
      )}
    </div>
  );
}

export default ClipsManager;
