import {Link} from "react-router-dom";
import {Home, Search} from "lucide-react";

function NotFoundPage() {
    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
            <div className="text-center max-w-md">
                <div className="mb-8">
                    <Search size={80} className="mx-auto text-gray-600 mb-4"/>
                    <h1 className="text-6xl font-bold text-white mb-4">404</h1>
                    <p className="text-xl text-gray-400 mb-2">Strona nie znaleziona</p>
                    <p className="text-gray-500">
                        Ta strona nie istnieje lub została przeniesiona
                    </p>
                </div>

                <Link
                    to="/dashboard"
                    className="inline-flex items-center gap-2 btn-primary"
                >
                    <Home size={20}/>
                    Wróć do Dashboard
                </Link>
            </div>
        </div>
    );
}

export default NotFoundPage;