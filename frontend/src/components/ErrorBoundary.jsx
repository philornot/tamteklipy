// frontend/src/components/ErrorBoundary.jsx
import {Component} from 'react';
import {AlertCircle} from 'lucide-react';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = {hasError: false, error: null};
    }

    static getDerivedStateFromError(error) {
        return {hasError: true, error};
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
                    <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full border border-red-700">
                        <div className="flex items-center gap-3 mb-4">
                            <AlertCircle className="text-red-500" size={32}/>
                            <h1 className="text-2xl font-bold text-white">Coś poszło nie tak</h1>
                        </div>

                        <p className="text-gray-300 mb-4">
                            Aplikacja napotkała nieoczekiwany błąd.
                        </p>

                        {this.props.showDetails && (
                            <details className="mb-4">
                                <summary className="text-sm text-gray-400 cursor-pointer">
                                    Szczegóły błędu
                                </summary>
                                <pre className="mt-2 text-xs text-red-400 bg-gray-900 p-2 rounded overflow-auto">
                  {this.state.error?.toString()}
                </pre>
                            </details>
                        )}

                        <button
                            onClick={() => window.location.href = '/'}
                            className="btn-primary w-full"
                        >
                            Wróć do strony głównej
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;