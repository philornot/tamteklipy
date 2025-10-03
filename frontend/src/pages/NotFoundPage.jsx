import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-white mb-4">404</h1>
        <p className="text-gray-400 mb-6">Strona nie znaleziona</p>
        <Link to="/" className="text-blue-500 hover:text-blue-400">
          Wróć do strony głównej
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
