import {useEffect, useState, useCallback} from "react";
import {Calendar, Edit2, Film, Loader, Save, Search, Trash2, User, X} from "lucide-react";
import api from "../../services/api";
import toast from "react-hot-toast";

function EditAwardModal({award, onClose, onSuccess}) {
    const [formData, setFormData] = useState({
        award_name: award.award_name,
        clip_id: award.clip.id
    });
    const [loading, setLoading] = useState(false);
    const [awardTypes, setAwardTypes] = useState([]);

    useEffect(() => {
        fetchAwardTypes();
    }, []);

    const fetchAwardTypes = async () => {
        try {
            const response = await api.get("/admin/award-types");
            setAwardTypes(response.data);
        } catch (err) {
            console.error("Failed to fetch award types:", err);
        }
    };

    const handleSave = async () => {
        setLoading(true);

        try {
            await api.patch(`/admin/awards/${award.id}`, formData);
            toast.success("Nagroda zaktualizowana");
            onSuccess();
            onClose();
        } catch (err) {
            toast.error(err.response?.data?.message || "Nie udało się zaktualizować nagrody");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div
                className="bg-gray-800 rounded-lg max-w-md w-full p-6 border border-gray-700"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">Edytuj nagrodę</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
                        <X size={20}/>
                    </button>
                </div>

                {/* Current Info */}
                <div className="mb-4 p-3 bg-gray-900 rounded border border-gray-700">
                    <div className="text-sm text-gray-400 space-y-1">
                        <p><strong>ID:</strong> #{award.id}</p>
                        <p><strong>Użytkownik:</strong> {award.user.username}</p>
                        <p><strong>Klip:</strong> {award.clip.filename}</p>
                        <p><strong>Data:</strong> {new Date(award.awarded_at).toLocaleString("pl-PL")}</p>
                    </div>
                </div>

                {/* Award Type */}
                <div className="mb-4">
                    <label className="block text-gray-300 mb-2">Typ nagrody</label>
                    <select
                        value={formData.award_name}
                        onChange={(e) => setFormData({...formData, award_name: e.target.value})}
                        className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                    >
                        {awardTypes.map((type) => (
                            <option key={type.id} value={type.name}>
                                {type.icon} {type.display_name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Clip ID */}
                <div className="mb-4">
                    <label className="block text-gray-300 mb-2">ID Klipa</label>
                    <input
                        type="number"
                        value={formData.clip_id}
                        onChange={(e) => setFormData({...formData, clip_id: parseInt(e.target.value)})}
                        className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                        min="1"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        Uwaga: zmiana klipa może spowodować konflikty
                    </p>
                </div>

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
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader className="animate-spin" size={16}/>
                                Zapisywanie...
                            </>
                        ) : (
                            <>
                                <Save size={16}/>
                                Zapisz
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

function AwardsManager() {
    const [awards, setAwards] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [editingAward, setEditingAward] = useState(null);
    const [deleting, setDeleting] = useState({});
    const [filterAwardType, setFilterAwardType] = useState("");

    const fetchAwards = useCallback(async () => {
        setLoading(true);
        try {
            const params = {
                page: currentPage,
                limit: 20,
                sort_by: "awarded_at",
                sort_order: "desc"
            };

            if (filterAwardType) {
                params.award_name = filterAwardType;
            }

            const response = await api.get("/admin/awards", {params});
            setAwards(response.data.awards);
            setTotalPages(response.data.pages);
        } catch (err) {
            toast.error("Nie udało się załadować nagród");
            console.error("Failed to fetch awards:", err);
        } finally {
            setLoading(false);
        }
    }, [currentPage, filterAwardType]);

    useEffect(() => {
        fetchAwards();
    }, [fetchAwards]);

    const handleDelete = async (awardId) => {
        if (!confirm("Czy na pewno chcesz usunąć tę nagrodę?")) {
            return;
        }

        setDeleting(prev => ({...prev, [awardId]: true}));

        try {
            await api.delete(`/admin/awards/${awardId}`);
            toast.success("Nagroda usunięta");
            await fetchAwards();
        } catch (err) {
            toast.error(err.response?.data?.message || "Nie udało się usunąć nagrody");
            console.error("Failed to delete award:", err);
        } finally {
            setDeleting(prev => ({...prev, [awardId]: false}));
        }
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

    const filteredAwards = awards.filter(award =>
        award.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        award.clip.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        award.award_display_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading && awards.length === 0) {
        return (
            <div className="flex justify-center py-8">
                <Loader className="animate-spin" size={32}/>
            </div>
        );
    }

    return (
        <div>
            <div className="mb-6">
                <h2 className="text-xl font-semibold mb-4">
                    Zarządzanie nagrodami ({awards.length})
                </h2>

                {/* Filters */}
                <div className="flex gap-4 mb-4">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20}/>
                        <input
                            type="text"
                            placeholder="Szukaj po użytkowniku, klipie lub typie nagrody..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-600 text-white pl-10 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Award Type Filter */}
                    <select
                        value={filterAwardType}
                        onChange={(e) => {
                            setFilterAwardType(e.target.value);
                            setCurrentPage(1);
                        }}
                        className="bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">Wszystkie nagrody</option>
                        <option value="award:epic_clip">Epic Clip</option>
                        <option value="award:funny">Funny</option>
                    </select>
                </div>
            </div>

            {/* Awards Table */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-900 border-b border-gray-700">
                        <tr>
                            <th className="text-left p-4 text-gray-300">ID</th>
                            <th className="text-left p-4 text-gray-300">Nagroda</th>
                            <th className="text-left p-4 text-gray-300">Użytkownik</th>
                            <th className="text-left p-4 text-gray-300">Klip</th>
                            <th className="text-left p-4 text-gray-300">Data</th>
                            <th className="text-left p-4 text-gray-300">Akcje</th>
                        </tr>
                        </thead>
                        <tbody>
                        {filteredAwards.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="text-center py-8 text-gray-400">
                                    {searchTerm ? "Brak wyników wyszukiwania" : "Brak nagród"}
                                </td>
                            </tr>
                        ) : (
                            filteredAwards.map((award) => (
                                <tr
                                    key={award.id}
                                    className="border-b border-gray-700 hover:bg-gray-700/50 transition"
                                >
                                    <td className="p-4 text-gray-400">#{award.id}</td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <span className="text-2xl">{award.award_icon}</span>
                                            <div>
                                                <p className="font-medium">{award.award_display_name}</p>
                                                <p className="text-xs text-gray-500">{award.award_name}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <User size={14} className="text-gray-400"/>
                                            <span>{award.user.username}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <Film size={14} className="text-blue-400"/>
                                                <span className="text-sm truncate max-w-xs">{award.clip.filename}</span>
                                            </div>
                                            <p className="text-xs text-gray-500">
                                                by {award.clip.uploader_username}
                                            </p>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <Calendar size={14} className="text-gray-400"/>
                                            <span className="text-sm">{formatDate(award.awarded_at)}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setEditingAward(award)}
                                                className="p-2 text-blue-400 hover:text-blue-300 hover:bg-gray-600 rounded transition"
                                                title="Edytuj nagrodę"
                                            >
                                                <Edit2 size={16}/>
                                            </button>
                                            <button
                                                onClick={() => handleDelete(award.id)}
                                                disabled={deleting[award.id]}
                                                className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-600 rounded transition disabled:opacity-50"
                                                title="Usuń nagrodę"
                                            >
                                                {deleting[award.id] ? (
                                                    <Loader className="animate-spin" size={16}/>
                                                ) : (
                                                    <Trash2 size={16}/>
                                                )}
                                            </button>
                                        </div>
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

            {/* Backend Notice */}
            <div className="mt-6 p-4 bg-yellow-900/20 border border-yellow-700 rounded text-yellow-300 text-sm">
                <strong>⚠️ Wymagane nowe endpointy backendu:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>GET /api/admin/awards - lista nagród z paginacją i filtrami</li>
                    <li>PATCH /api/admin/awards/:id - aktualizacja nagrody</li>
                    <li>DELETE /api/admin/awards/:id - usunięcie nagrody</li>
                </ul>
                <p className="mt-2">Zobacz artifact "admin_awards_endpoints" z implementacją Python.</p>
            </div>

            {/* Edit Modal */}
            {editingAward && (
                <EditAwardModal
                    award={editingAward}
                    onClose={() => setEditingAward(null)}
                    onSuccess={fetchAwards}
                />
            )}
        </div>
    );
}

export default AwardsManager;