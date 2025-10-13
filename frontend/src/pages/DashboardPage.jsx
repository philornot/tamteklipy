import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams, useLocation } from "react-router-dom";
import api from "../services/api";
import ClipGrid from "../components/clips/ClipGrid";
import FloatingToolbar from "../components/clips/FloatingToolbar";
import SortFilter from "../components/ui/SortFilter";
import { AlertCircle, CheckSquare, Sparkles } from "lucide-react";
import usePageTitle from "../hooks/usePageTitle.js";
import { useBulkSelection } from "../hooks/useBulkSelection.js";
import { Button, SectionHeader, Spinner } from "../components/ui/StyledComponents";
import { logger } from "../utils/logger";

function DashboardPage() {
  usePageTitle("Dashboard");
  const location = useLocation();

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
  const refreshTimeoutRef = useRef(null);

  const {
    selectedIds,
    selectedCount,
    toggleSelection,
    selectAll,
    clearSelection,
    hasSelection,
  } = useBulkSelection(clips);

  const sortBy = searchParams.get("sort_by") || "created_at";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const clipType = searchParams.get("clip_type") || "";

  // Mouse tracking dla gradient effect
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
      headerElement.addEventListener("mousemove", handleMouseMove);
    }

    return () => {
      if (headerElement) {
        headerElement.removeEventListener("mousemove", handleMouseMove);
      }
    };
  }, []);

  // ESC key handler
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape" && hasSelection) {
        clearSelection();
      }
    };

    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [hasSelection, clearSelection]);

  // Calculate dynamic gradient
  const calculateGradient = () => {
    const angle =
      Math.atan2(mousePosition.y - 50, mousePosition.x - 50) * (180 / Math.PI);
    return `linear-gradient(${angle}deg, #111827, rgba(30, 27, 75, 0.4), rgba(112, 26, 117, 0.3))`;
  };

  // Fetch clips function
  const fetchClips = useCallback(
    async (pageNum, append = false) => {
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

        const response = await api.get("/files/clips", { params });

        if (append) {
          setClips((prev) => [...prev, ...response.data.clips]);
        } else {
          setClips(response.data.clips);
        }

        setHasMore(response.data.page < response.data.pages);
        logger.info("Clips fetched, thumbnails preloaded via HTTP/2 Server Push");
      } catch (err) {
        logger.error("Failed to fetch clips:", err);
        setError("Nie udało się załadować klipów");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    []
  );

  // AUTO-REFRESH po powrocie z upload page
  useEffect(() => {
    const fromUpload = location.state?.fromUpload;

    if (fromUpload) {
      logger.info("Returned from upload, scheduling refreshes...");

      // Odśwież natychmiast
      fetchClips(1, false);

      // Harmonogram refreshy (thumbnails mogą się jeszcze generować)
      refreshTimeoutRef.current = setTimeout(() => {
        logger.info("Refresh 1/3 (2s)");
        fetchClips(1, false);

        refreshTimeoutRef.current = setTimeout(() => {
          logger.info("Refresh 2/3 (5s)");
          fetchClips(1, false);

          refreshTimeoutRef.current = setTimeout(() => {
            logger.info("Refresh 3/3 (10s - final)");
            fetchClips(1, false);
          }, 5000);
        }, 3000);
      }, 2000);

      // Wyczyść state
      window.history.replaceState({}, document.title);
    }

    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, [location.state, fetchClips]);

  // Initial load i zmiana sortowania/filtrów
  useEffect(() => {
    setPage(1);
    setClips([]);
    setHasMore(true);
    clearSelection();
    fetchClips(1, false);
  }, [sortBy, sortOrder, clipType, fetchClips, clearSelection]);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingMore && !loading && hasMore) {
          const scrollPercentage =
            (window.scrollY + window.innerHeight) /
            document.documentElement.scrollHeight;

          if (scrollPercentage > 0.8) {
            setPage((prev) => {
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
        threshold: 0.1,
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
      ...(clipType && { clip_type: clipType }),
    });
  };

  const handleFilterChange = (newClipType) => {
    setSearchParams({
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(newClipType && { clip_type: newClipType }),
    });
  };

  const handleBulkActionComplete = (action, result) => {
    logger.info("Bulk action completed:", action, result);

    if (action === "delete" && result?.success) {
      setClips((prev) => prev.filter((clip) => !selectedIds.includes(clip.id)));
    }

    clearSelection();
  };

  const handleClipUpdate = useCallback((clipId) => {
    setClips((prevClips) => {
      const index = prevClips.findIndex((c) => c.id === clipId);
      if (index === -1) return prevClips;

      api
        .get(`/files/clips/${clipId}`)
        .then((response) => {
          setClips((prev) => {
            const newClips = [...prev];
            newClips[index] = {
              ...newClips[index],
              award_count: response.data.awards?.length || 0,
              award_icons: response.data.award_icons || [],
            };
            return newClips;
          });
        })
        .catch((err) => logger.error("Failed to refresh clip:", err));

      return prevClips;
    });
  }, []);

  // Loading state
  if (loading && clips.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
        <div className="relative">
          <Spinner size="xl" color="primary" />
          <div className="absolute inset-0 blur-xl bg-purple-500/20 animate-pulse" />
        </div>
      </div>
    );
  }

  // Error state
  if (error && clips.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-500/10 border border-red-500 text-red-200 px-6 py-4 rounded-card flex items-center gap-3">
          <AlertCircle size={24} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 min-h-screen">
      {/* Header z dynamic gradient */}
      <SectionHeader
        ref={headerRef}
        title="Dashboard"
        subtitle={
          <>
            {clips.length} {clips.length === 1 ? "klip" : "klipów"} załadowanych
            {hasSelection && (
              <span className="text-purple-400 ml-2">
                • {selectedCount} zaznaczonych
              </span>
            )}
          </>
        }
        gradient
        action={
          clips.length > 0 && (
            <Button
              variant={hasSelection ? "primary" : "outline"}
              size="md"
              onClick={hasSelection ? clearSelection : selectAll}
            >
              <CheckSquare size={18} />
              <span className="font-medium">
                {hasSelection ? "Odznacz wszystkie" : "Zaznacz wszystkie"}
              </span>
            </Button>
          )
        }
        className="mb-8"
        style={{ background: calculateGradient() }}
      />

      {/* Sort & Filter */}
      <SortFilter
        sortBy={sortBy}
        sortOrder={sortOrder}
        clipType={clipType}
        onSortChange={handleSortChange}
        onFilterChange={handleFilterChange}
      />

      {/* Clips Grid */}
      <ClipGrid
        clips={clips}
        loading={false}
        selectionMode={hasSelection}
        selectedIds={selectedIds}
        onSelectionToggle={toggleSelection}
        onClipUpdate={handleClipUpdate}
      />

      {/* Floating Toolbar (bulk actions) */}
      {hasSelection && (
        <FloatingToolbar
          selectedCount={selectedCount}
          selectedIds={selectedIds}
          onActionComplete={handleBulkActionComplete}
          onCancel={clearSelection}
        />
      )}

      {/* Infinite Scroll Observer Target */}
      <div ref={observerTarget} className="py-12 flex items-center justify-center">
        {loadingMore && (
          <div className="flex items-center gap-3 text-purple-400 bg-gray-800/50 px-6 py-3 rounded-xl border border-purple-500/20 backdrop-blur-sm">
            <div className="relative">
              <Spinner size="md" color="primary" />
              <div className="absolute inset-0 blur-md bg-purple-500/30 animate-pulse" />
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
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500 to-transparent animate-pulse" />
            </div>
          </div>
        )}
      </div>

      {/* Manual Load More Button */}
      {!loadingMore && hasMore && clips.length > 0 && (
        <div className="flex justify-center pb-12">
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              const nextPage = page + 1;
              setPage(nextPage);
              fetchClips(nextPage, true);
            }}
            className="group relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-primary opacity-0 group-hover:opacity-10 transition-opacity duration-500" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 -translate-x-full group-hover:translate-x-full group-hover:duration-1000" />
            <span className="relative z-10 flex items-center gap-3">
              Załaduj więcej
              <Sparkles size={18} className="text-purple-400 group-hover:text-fuchsia-300 group-hover:animate-pulse transition-colors duration-300" />
            </span>
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!loading && clips.length === 0 && (
        <div className="text-center py-20">
          <div className="relative inline-block mb-6">
            <div className="absolute inset-0 blur-2xl bg-purple-500/20 animate-pulse" />
            <Sparkles size={64} className="relative text-purple-400" />
          </div>
          <h3 className="text-2xl font-bold text-gray-300 mb-2">
            Brak klipów
          </h3>
          <p className="text-gray-400 mb-6">
            {clipType || sortBy !== "created_at"
              ? "Spróbuj zmienić filtry"
              : "Rozpocznij od przesłania pierwszego pliku"}
          </p>
          <Button
            variant="primary"
            size="lg"
            onClick={() => window.location.href = "/upload"}
          >
            Prześlij pierwszy klip
          </Button>
        </div>
      )}
    </div>
  );
}

export default DashboardPage;
