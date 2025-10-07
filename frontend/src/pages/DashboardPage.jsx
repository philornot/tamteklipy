import {useCallback, useEffect, useRef, useState} from "react";
import {useSearchParams} from "react-router-dom";
import api from "../services/api";
import ClipGrid from "../components/clips/ClipGrid";
import SortFilter from "../components/ui/SortFilter";
import {AlertCircle, Loader} from "lucide-react";

function DashboardPage() {
    const [clips, setClips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState(null);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(1);

    const [searchParams, setSearchParams] = useSearchParams();
    const observerTarget = useRef(null);

    // Parse query params
    const sortBy = searchParams.get("sort_by") || "created_at";
    const sortOrder = searchParams.get("sort_order") || "desc";
    const clipType = searchParams.get("clip_type") || "";

    const fetchClips = useCallback(async (pageNum, append = false) => {
        if (append) {
            setLoadingMore(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const params = {
                page: pageNum,
                limit: 12, // Zmniejszony initial limit
                sort_by: sortBy,
                sort_order: sortOrder,
            };

            if (clipType) {
                params.clip_type = clipType;
            }

            const response = await api.get("/files/clips", {params});

            if (append) {
                setClips(prev => [...prev, ...response.data.clips]);
            } else {
                setClips(response.data.clips);
            }

            // Sprawdź czy są jeszcze kolejne strony
            setHasMore(response.data.page < response.data.pages);

        } catch (err) {
            console.error("Failed to fetch clips:", err);
            setError("Nie udało się załadować klipów");
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, [sortBy, sortOrder, clipType]);

    // Initial load
    useEffect(() => {
        setPage(1);
        setClips([]);
        setHasMore(true);
        fetchClips(1, false);
    }, [sortBy, sortOrder, clipType]);

    // Intersection Observer dla infinite scroll
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                // Załaduj więcej gdy:
                // - element jest widoczny
                // - nie ładujemy już
                // - są jeszcze dane do pobrania
                // - użytkownik przewinął 80% strony
                if (entries[0].isIntersecting && !loadingMore && !loading && hasMore) {
                    const scrollPercentage = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;

                    if (scrollPercentage > 0.8) {
                        setPage(prev => {
                            const nextPage = prev + 1;
                            fetchClips(nextPage, true);
                            return nextPage;
                        });
                    }
                }
            },
            {
                root: null,
                rootMargin: "200px", // Zacznij ładować 200px przed końcem
                threshold: 0.1
            }
        );

        if (observerTarget.current) {
            observer.observe(observerTarget.current);
        }

        return () => {
            if (observerTarget.current) {
                observer.unobserve(observerTarget.current);
            }
        };
    }, [loadingMore, loading, hasMore, fetchClips]);

    const handleSortChange = (newSortBy, newSortOrder) => {
        setSearchParams({
            sort_by: newSortBy,
            sort_order: newSortOrder,
            ...(clipType && {clip_type: clipType}),
        });
    };

    const handleFilterChange = (newClipType) => {
        setSearchParams({
            sort_by: sortBy,
            sort_order: sortOrder,
            ...(newClipType && {clip_type: newClipType}),
        });
    };

    if (loading && clips.length === 0) {
        return (
            <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
                <Loader className="animate-spin text-blue-500" size={48}/>
            </div>
        );
    }

    if (error && clips.length === 0) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div
                    className="bg-red-900/50 border border-red-700 text-red-200 px-6 py-4 rounded-lg flex items-center gap-3">
                    <AlertCircle size={24}/>
                    <span>{error}</span>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
                <p className="text-gray-400">
                    {clips.length} {clips.length === 1 ? "klip" : "klipów"} załadowanych
                </p>
            </div>

            <SortFilter
                sortBy={sortBy}
                sortOrder={sortOrder}
                clipType={clipType}
                onSortChange={handleSortChange}
                onFilterChange={handleFilterChange}
            />

            <ClipGrid clips={clips} loading={false}/>

            {/* Intersection Observer Target */}
            <div ref={observerTarget} className="h-20 flex items-center justify-center">
                {loadingMore && (
                    <div className="flex items-center gap-2 text-gray-400">
                        <Loader className="animate-spin" size={24}/>
                        <span>Ładowanie kolejnych klipów...</span>
                    </div>
                )}

                {!hasMore && clips.length > 0 && (
                    <p className="text-gray-500 text-sm">
                        Wszystkie klipy zostały załadowane
                    </p>
                )}
            </div>

            {/* Fallback: Load More button dla starszych przeglądarek */}
            {!loadingMore && hasMore && clips.length > 0 && (
                <div className="flex justify-center mt-8">
                    <button
                        onClick={() => {
                            const nextPage = page + 1;
                            setPage(nextPage);
                            fetchClips(nextPage, true);
                        }}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                    >
                        Załaduj więcej
                    </button>
                </div>
            )}
        </div>
    );
}

export default DashboardPage;