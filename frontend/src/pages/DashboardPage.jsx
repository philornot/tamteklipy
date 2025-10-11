import {useCallback, useEffect, useRef, useState} from "react";
import {useSearchParams} from "react-router-dom";
import api from "../services/api";
import ClipGrid from "../components/clips/ClipGrid";
import FloatingToolbar from "../components/clips/FloatingToolbar";
import SortFilter from "../components/ui/SortFilter";
import {AlertCircle, CheckSquare, Loader, Sparkles} from "lucide-react";
import usePageTitle from "../hooks/usePageTitle.js";
import {useBulkSelection} from "../hooks/useBulkSelection.js";

function DashboardPage() {
    usePageTitle("Dashboard");
    const [clips, setClips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState(null);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(1);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

    const [searchParams, setSearchParams] = useSearchParams();
    const observerTarget = useRef(null);
    const headerRef = useRef(null);

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

    // Parse query params
    const sortBy = searchParams.get("sort_by") || "created_at";
    const sortOrder = searchParams.get("sort_order") || "desc";
    const clipType = searchParams.get("clip_type") || "";

    // Track mouse position for gradient effect
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (headerRef.current) {
                const rect = headerRef.current.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                setMousePosition({ x, y });
            }
        };

        const headerElement = headerRef.current;
        if (headerElement) {
            headerElement.addEventListener('mousemove', handleMouseMove);
        }

        return () => {
            if (headerElement) {
                headerElement.removeEventListener('mousemove', handleMouseMove);
            }
        };
    }, []);

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

    // Calculate gradient angle based on mouse position
    const calculateGradient = () => {
        const angle = Math.atan2(mousePosition.y - 50, mousePosition.x - 50) * (180 / Math.PI);
        return `linear-gradient(${angle}deg, #111827, rgba(30, 27, 75, 0.4), rgba(112, 26, 117, 0.3))`;
    };

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

            setHasMore(response.data.page < response.data.pages);
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
        clearSelection();
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

    const handleBulkActionComplete = (action, result) => {
        console.log('Bulk action completed:', action, result);

        if (action === 'delete' && result?.success) {
            // Remove deleted clips from the list
            setClips(prev => prev.filter(clip => !selectedIds.includes(clip.id)));
        }

        // Clear selection after any action
        clearSelection();

        // Optionally refetch clips
        // fetchClips(1, false);
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
        <div className="container mx-auto px-4 py-8 min-h-screen">
            {/* Header z dynamicznym gradientem */}
            <div className="mb-8 relative">
                <div className="absolute -left-20 -top-20 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl pointer-events-none"/>
                <div className="absolute -right-20 -top-10 w-80 h-80 bg-fuchsia-500/5 rounded-full blur-3xl pointer-events-none"/>

                <div
                    ref={headerRef}
                    className="relative rounded-2xl p-6 border border-purple-500/20 backdrop-blur-sm transition-all duration-200"
                    style={{
                        background: calculateGradient()
                    }}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-fuchsia-400 to-purple-300 bg-clip-text text-transparent drop-shadow-lg">
                                    Dashboard
                                </h1>
                            </div>
                            <p className="text-gray-400 text-sm">
                                {clips.length} {clips.length === 1 ? "klip" : "klipów"} załadowanych
                                {hasSelection && (
                                    <span className="text-blue-400 ml-2">
                                        • {selectedCount} zaznaczonych
                                    </span>
                                )}
                            </p>
                        </div>

                        {/* Select All Button */}
                        {clips.length > 0 && (
                            <button
                                onClick={hasSelection ? clearSelection : selectAll}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-300 ${
                                    hasSelection
                                        ? 'bg-blue-600 border-blue-500 text-white hover:bg-blue-700'
                                        : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-500 hover:text-blue-400'
                                }`}
                            >
                                <CheckSquare size={18} />
                                <span className="font-medium">
                                    {hasSelection ? 'Odznacz wszystkie' : 'Zaznacz wszystkie'}
                                </span>
                            </button>
                        )}
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

            <ClipGrid
                clips={clips}
                loading={false}
                selectionMode={hasSelection}
                selectedIds={selectedIds}
                onSelectionToggle={toggleSelection}
            />

            {/* Floating Toolbar */}
            {hasSelection && (
                <FloatingToolbar
                    selectedCount={selectedCount}
                    selectedIds={selectedIds}
                    onActionComplete={handleBulkActionComplete}
                    onCancel={clearSelection}
                />
            )}

            {/* Intersection Observer Target */}
            <div ref={observerTarget} className="py-12 flex items-center justify-center">
                {loadingMore && (
                    <div className="flex items-center gap-3 text-purple-400 bg-gray-800/50 px-6 py-3 rounded-xl border border-purple-500/20">
                        <div className="relative">
                            <Loader className="animate-spin" size={24}/>
                            <div className="absolute inset-0 blur-md bg-purple-500/30 animate-pulse"/>
                        </div>
                        <span className="font-medium">Ładowanie kolejnych klipów...</span>
                    </div>
                )}

                {!hasMore && clips.length > 0 && (
                    <div className="text-center space-y-4">
                        <p className="text-gray-400 text-sm font-medium">
                            Wszystkie klipy zostały załadowane
                        </p>
                        <div className="relative w-32 h-1 mx-auto rounded-full overflow-hidden bg-gray-800">
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500 to-transparent animate-pulse"/>
                        </div>
                    </div>
                )}
            </div>

            {/* Load More button */}
            {!loadingMore && hasMore && clips.length > 0 && (
                <div className="flex justify-center pb-12">
                    <button
                        onClick={() => {
                            const nextPage = page + 1;
                            setPage(nextPage);
                            fetchClips(nextPage, true);
                        }}
                        className="group relative px-8 py-4 bg-gray-900/80 hover:bg-gray-800/90 border border-purple-500/30 hover:border-purple-400/50 text-white font-medium rounded-xl transition-all duration-300 shadow-lg hover:shadow-purple-500/20 hover:shadow-xl backdrop-blur-sm overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 via-fuchsia-500/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 group-hover:animate-pulse"/>
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 -translate-x-full group-hover:translate-x-full group-hover:duration-1000"/>
                        <span className="relative z-10 flex items-center gap-3 text-gray-100 group-hover:text-white">
                            Załaduj więcej
                            <Sparkles size={18} className="text-purple-400 group-hover:text-fuchsia-300 group-hover:animate-pulse transition-colors duration-300"/>
                        </span>
                    </button>
                </div>
            )}
        </div>
    );
}

export default DashboardPage;
