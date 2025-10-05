import {useEffect, useState} from "react";
import {useAuth} from "../hooks/useAuth";
import {Loader, Lock, Mail, Save, User, LockOpen} from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";

function ProfilePage() {
    const {user, setUser} = useAuth();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
    });
    const [emptyPassword, setEmptyPassword] = useState(false);

    useEffect(() => {
        if (user) {
            setFormData({
                full_name: user.full_name || "",
                email: user.email || "",
                password: "",
                confirmPassword: "",
            });
            setEmptyPassword(false);
        }
    }, [user]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Walidacja hasła (tylko zgodność, gdy ustawiane)
        if (!emptyPassword && formData.password && formData.password !== formData.confirmPassword) {
            toast.error("Hasła nie są identyczne");
            return;
        }

        setLoading(true);

        try {
            const updateData = {
                full_name: formData.full_name,
                email: formData.email || null,
            };

            if (emptyPassword) {
                // jawnie ustaw puste hasło
                updateData.password = "";
            } else if (formData.password) {
                updateData.password = formData.password;
            }

            const response = await api.patch("/auth/me", updateData);

            // Zaktualizuj user w context i localStorage
            setUser(response.data);
            localStorage.setItem("user", JSON.stringify(response.data));

            toast.success("Profil zaktualizowany");

            // Wyczyść hasła i flagę
            setFormData({
                ...formData,
                password: "",
                confirmPassword: "",
            });
            setEmptyPassword(false);
        } catch (err) {
            console.error("Failed to update profile:", err);
            toast.error(err.response?.data?.message || "Nie udało się zaktualizować profilu");
        } finally {
            setLoading(false);
        }
    };

    // Ustaw puste hasło i od razu zapisz zmiany
    const handleSetEmptyPasswordAndSave = async () => {
        if (!user || loading) return;
        setLoading(true);
        try {
            const updateData = {
                full_name: formData.full_name,
                email: formData.email || null,
                password: "", // jawnie puste hasło
            };
            const response = await api.patch("/auth/me", updateData);
            setUser(response.data);
            localStorage.setItem("user", JSON.stringify(response.data));
            toast.success("Hasło ustawione jako puste. Profil zaktualizowany");
            setFormData({
                ...formData,
                password: "",
                confirmPassword: "",
            });
            setEmptyPassword(false);
        } catch (err) {
            console.error("Failed to set empty password:", err);
            toast.error(err.response?.data?.message || "Nie udało się ustawić pustego hasła");
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === "password") {
            // Każde ręczne wpisanie hasła anuluje tryb pustego hasła
            if (value !== "") setEmptyPassword(false);
        }
        setFormData({
            ...formData,
            [name]: value,
        });
    };

    if (!user) return null;

    return (
        <div className="container mx-auto px-4 py-8 max-w-2xl">
            <h1 className="text-3xl font-bold mb-6">Profil użytkownika</h1>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <form onSubmit={handleSubmit} className="space-y-6" autoComplete="on">
                    {/* Username (read-only) */}
                    <div>
                        <label className="block text-gray-300 mb-2">
                            <User size={16} className="inline mr-2"/>
                            Username
                        </label>
                        <input
                            type="text"
                            name="username"
                            value={user.username}
                            readOnly
                            autoComplete="username"
                            className="input-field w-full bg-gray-700 cursor-not-allowed"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Username nie może być zmieniony
                        </p>
                    </div>

                    {/* Full Name */}
                    <div>
                        <label className="block text-gray-300 mb-2">
                            Wyświetlana nazwa
                        </label>
                        <input
                            type="text"
                            name="full_name"
                            value={formData.full_name}
                            onChange={handleChange}
                            className="input-field w-full"
                            placeholder="Jan Kowalski"
                            maxLength={100}
                            autoComplete="name"
                        />
                    </div>

                    {/* Email */}
                    <div>
                        <label className="block text-gray-300 mb-2">
                            <Mail size={16} className="inline mr-2"/>
                            Email
                        </label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            className="input-field w-full"
                            placeholder="email@example.com"
                            autoComplete="email"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Opcjonalne - będzie używany do resetu hasła
                        </p>
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-gray-300 mb-2">
                            <Lock size={16} className="inline mr-2"/>
                            Nowe hasło
                        </label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            className="input-field w-full"
                            placeholder="Zostaw puste aby nie zmieniać"
                            autoComplete="new-password"
                        />
                        <div className="flex items-center gap-2 mt-3">
                            <button
                                type="button"
                                onClick={handleSetEmptyPasswordAndSave}
                                disabled={loading}
                                className="inline-flex items-center gap-2 text-sm px-3 py-2 rounded bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                                title="Ustaw puste hasło i zapisz zmiany"
                            >
                                <LockOpen size={16} />
                                Ustaw puste hasło i zapisz
                            </button>
                            <span className="text-xs text-yellow-400">Puste hasło jest niezalecane, no ale co ja ci będę bronić.</span>
                        </div>
                    </div>

                    {/* Confirm Password */}
                    {formData.password && (
                        <div>
                            <label className="block text-gray-300 mb-2">
                                Potwierdź hasło
                            </label>
                            <input
                                type="password"
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                className="input-field w-full"
                                placeholder="Powtórz nowe hasło"
                                autoComplete="new-password"
                            />
                        </div>
                    )}

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader className="animate-spin" size={20}/>
                                Zapisywanie...
                            </>
                        ) : (
                            <>
                                <Save size={20}/>
                                Zapisz zmiany
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Dodatkowe info */}
            <div className="mt-6 bg-gray-800 rounded-lg p-4 border border-gray-700">
                <h3 className="font-semibold mb-2">Informacje o koncie</h3>
                <div className="text-sm text-gray-400 space-y-1">
                    <p>Typ konta: {user.is_admin ? "Administrator" : "Użytkownik"}</p>
                    <p>Status: {user.is_active ? "Aktywny" : "Nieaktywny"}</p>
                </div>
            </div>
        </div>
    );
}

export default ProfilePage;
