import { ChevronLeft, ChevronRight } from "lucide-react";

function Pagination({ currentPage, totalPages, onPageChange }) {
  const pages = [];
  const maxVisible = 5;

  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="p-2 rounded bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
      >
        <ChevronLeft size={20} />
      </button>

      {startPage > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700"
          >
            1
          </button>
          {startPage > 2 && <span className="text-gray-500">...</span>}
        </>
      )}

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-4 py-2 rounded border ${
            page === currentPage
              ? "bg-blue-600 border-blue-600 text-white"
              : "bg-gray-800 border-gray-700 hover:bg-gray-700"
          }`}
        >
          {page}
        </button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && (
            <span className="text-gray-500">...</span>
          )}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="p-2 rounded bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
      >
        <ChevronRight size={20} />
      </button>
    </div>
  );
}

export default Pagination;
