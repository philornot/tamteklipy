import {useCallback, useEffect, useRef, useState} from "react";
import {useSearchParams} from "react-router-dom";
import api from "../services/api";
import ClipGrid from "../components/clips/ClipGrid";
import SortFilter from "../components/ui/SortFilter";
import {AlertCircle, Loader, Sparkles} from "lucide-react";

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
                limit: 12,
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

            // HTTP/2 Server Push działa automatycznie przez Link header
            // Przeglądarka automatycznie pobierze thumbnails w tle
            console.log("✓ Clips fetched, thumbnails preloaded via HTTP/2 Server Push");

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
                rootMargin: "200px",
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
                <div className="relative">
                    <Loader className="animate-spin text-purple-500" size={48}/>
                    <div className="absolute inset-0 blur-xl bg-purple-500/20 animate-pulse"/>
                </div>
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
            {/* Header z akcentem */}
            <div className="mb-8 relative">
                <div className="absolute -left-20 -top-20 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl pointer-events-none"/>
                <div className="absolute -right-20 -top-10 w-80 h-80 bg-fuchsia-500/5 rounded-full blur-3xl pointer-events-none"/>

                <div className="relative bg-gradient-to-br from-gray-800/40 to-gray-800/10 rounded-2xl p-6 border border-purple-500/10 backdrop-blur-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-fuchsia-400 to-purple-300 bg-clip-text text-transparent drop-shadow-lg">
                                    Dashboard
                                </h1>
                                <Sparkles className="text-purple-400" size={28}/>
                            </div>
                            <p className="text-gray-400 text-sm">
                                {clips.length} {clips.length === 1 ? "klip" : "klipów"} załadowanych
                            </p>
                        </div>
                    </div>
                </div>
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
                    <div className="flex items-center gap-2 text-purple-400">
                        <div className="relative">
                            <Loader className="animate-spin" size={24}/>
                            <div className="absolute inset-0 blur-md bg-purple-500/30 animate-pulse"/>
                        </div>
                        <span>Ładowanie kolejnych klipów...</span>
                    </div>
                )}

                {!hasMore && clips.length > 0 && (
                    <div className="text-center">
                        <p className="text-gray-500 text-sm mb-2">
                            Wszystkie klipy zostały załadowane
                        </p>
                        <div className="w-16 h-1 bg-gradient-to-r from-transparent via-purple-500/30 to-transparent mx-auto rounded-full"/>
                    </div>
                )}
            </div>

            {/* Fallback: Load More button z akcentem */}
            {!loadingMore && hasMore && clips.length > 0 && (
                <div className="flex justify-center mt-8">
                    <button
                        onClick={() => {
                            const nextPage = page + 1;
                            setPage(nextPage);
                            fetchClips(nextPage, true);
                        }}
                        className="relative px-6 py-3 bg-gradient-to-r from-purple-600 to-lavender-600 hover:from-purple-700 hover:to-lavender-700 text-white rounded-lg transition-all duration-300 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105"
                    >
                        <span className="relative z-10">Załaduj więcej</span>
                        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-purple-400/0 via-white/20 to-purple-400/0 opacity-0 hover:opacity-100 transition-opacity duration-300"/>
                    </button>
                </div>
            )}
        </div>
    );
}

export default DashboardPage;