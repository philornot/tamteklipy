import { useState } from 'react';
import { Download, Tag, FolderPlus, Trash2, X } from 'lucide-react';
import api from '../../services/api';
import toast from "react-hot-toast";

/**
 * Floating toolbar pokazujący się przy zaznaczeniu klipów
 * Pozycjonowany fixed at bottom center
 */
function FloatingToolbar({ selectedCount, selectedIds, onActionComplete, onCancel }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    if (loading || selectedIds.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(
        '/files/download-bulk',
        { clip_ids: selectedIds },
        { responseType: 'blob' }
      );

      // Utwórz URL do pliku ZIP
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      link.setAttribute('download', `tamteklipy_${timestamp}.zip`);

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);

      onActionComplete?.('download');
    } catch (err) {
      console.error('Download failed:', err);
      setError('Nie udało się pobrać plików');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTags = async () => {
    // TODO: Otwórz modal do wyboru tagów
    alert('Funkcja dodawania tagów będzie dostępna wkrótce');
  };

  const handleAddToSession = async () => {
    // TODO: Otwórz modal do wyboru/utworzenia sesji
    alert('Funkcja dodawania do sesji będzie dostępna wkrótce');
  };

  const handleDelete = async () => {
    if (loading || selectedIds.length === 0) return;

    const confirmed = window.confirm(
      `Czy na pewno chcesz usunąć ${selectedCount} ${
        selectedCount === 1 ? 'klip' : 'klipy'
      }?`
    );

    if (!confirmed) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/files/clips/bulk-action', {
        clip_ids: selectedIds,
        action: 'delete',
      });

        if (response.data.success) {
          toast.success(response.data.message);
          onActionComplete?.('delete', response.data);
        } else {
          toast.error(response.data.message);
          onActionComplete?.('delete', response.data);
        }
    } catch (err) {
      console.error('Delete failed:', err);
      setError(err.response?.data?.message || 'Nie udało się usunąć klipów');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 animate-slideUp">
      <div className="bg-gray-900 border border-purple-500/50 rounded-2xl shadow-2xl shadow-purple-500/20 backdrop-blur-xl">
        {/* Error banner */}
        {error && (
          <div className="px-6 py-2 bg-red-900/50 border-b border-red-700/50 rounded-t-2xl text-red-200 text-sm">
            {error}
          </div>
        )}

        <div className="px-6 py-4 flex items-center gap-4">
          {/* Selection info */}
          <div className="flex items-center gap-3 pr-4 border-r border-gray-700">
            <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
              <span className="text-purple-400 font-bold text-sm">
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
              onClick={handleDownload}
              disabled={loading}
              className="px-4 py-2 bg-blue-600/90 hover:bg-blue-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Pobierz ZIP"
            >
              <Download size={16} />
              <span className="hidden sm:inline">ZIP</span>
            </button>

            <button
              onClick={handleAddTags}
              disabled={loading}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Dodaj tagi"
            >
              <Tag size={16} />
              <span className="hidden sm:inline">Tagi</span>
            </button>

            <button
              onClick={handleAddToSession}
              disabled={loading}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Dodaj do sesji"
            >
              <FolderPlus size={16} />
              <span className="hidden sm:inline">Sesja</span>
            </button>

            <div className="w-px h-6 bg-gray-700 mx-1" />

            <button
              onClick={handleDelete}
              disabled={loading}
              className="px-4 py-2 bg-red-600/90 hover:bg-red-600 text-white rounded-lg transition flex items-center gap-2 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              title="Usuń"
            >
              <Trash2 size={16} />
              <span className="hidden sm:inline">Usuń</span>
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

export default FloatingToolbar;