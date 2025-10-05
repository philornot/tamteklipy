import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../services/api";
import ClipGrid from "../components/clips/ClipGrid";
import Pagination from "../components/ui/Pagination";
import SortFilter from "../components/ui/SortFilter";
import { Loader, AlertCircle } from "lucide-react";

function DashboardPage() {
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  const [searchParams, setSearchParams] = useSearchParams();

  // Parse query params
  const page = parseInt(searchParams.get("page")) || 1;
  const sortBy = searchParams.get("sort_by") || "created_at";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const clipType = searchParams.get("clip_type") || "";

  const fetchClips = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page,
        limit: 20,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (clipType) {
        params.clip_type = clipType;
      }

      const response = await api.get("/files/clips", { params });

      setClips(response.data.clips);
      setPagination({
        page: response.data.page,
        limit: response.data.limit,
        total: response.data.total,
        pages: response.data.pages,
      });
    } catch (err) {
      console.error("Failed to fetch clips:", err);
      setError("Nie udało się załadować klipów");
    } finally {
      setLoading(false);
    }
  }, [page, sortBy, sortOrder, clipType]);

  useEffect(() => {
    fetchClips();
  }, [fetchClips]);

  const handlePageChange = (newPage) => {
    setSearchParams({
      page: newPage,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(clipType && { clip_type: clipType }),
    });
  };

  const handleSortChange = (newSortBy, newSortOrder) => {
    setSearchParams({
      page: 1,
      sort_by: newSortBy,
      sort_order: newSortOrder,
      ...(clipType && { clip_type: clipType }),
    });
  };

  const handleFilterChange = (newClipType) => {
    setSearchParams({
      page: 1,
      sort_by: sortBy,
      sort_order: sortOrder,
      ...(newClipType && { clip_type: newClipType }),
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
        <Loader className="animate-spin text-blue-500" size={48} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-6 py-4 rounded-lg flex items-center gap-3">
          <AlertCircle size={24} />
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
          {pagination.total} {pagination.total === 1 ? "klip" : "klipów"}
        </p>
      </div>

      <SortFilter
        sortBy={sortBy}
        sortOrder={sortOrder}
        clipType={clipType}
        onSortChange={handleSortChange}
        onFilterChange={handleFilterChange}
      />

      <ClipGrid clips={clips} loading={loading} />

      {pagination.pages > 1 && (
        <Pagination
          currentPage={pagination.page}
          totalPages={pagination.pages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}

export default DashboardPage;
