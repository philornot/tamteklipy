import {useEffect, useState} from "react";
import {useAuth} from "../hooks/useAuth";
import {Loader, Lock, Mail, Save, User, LockOpen} from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";
import usePageTitle from "../hooks/usePageTitle.js";
import { Button, Card, Input } from "../components/ui/StyledComponents";

function ProfilePage() {
    usePageTitle("Profil użytkownika");
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
                updateData.password = "";
            } else if (formData.password) {
                updateData.password = formData.password;
            }

            const response = await api.patch("/auth/me", updateData);

            setUser(response.data);
            localStorage.setItem("user", JSON.stringify(response.data));

            toast.success("Profil zaktualizowany");

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

    const handleSetEmptyPasswordAndSave = async () => {
        if (!user || loading) return;
        setLoading(true);
        try {
            const updateData = {
                full_name: formData.full_name,
                email: formData.email || null,
                password: "",
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

            <Card className="p-6">
                <form onSubmit={handleSubmit} className="space-y-6" autoComplete="on">
                    {/* Username (read-only) */}
                    <Input
                        label={
                            <span className="flex items-center gap-2">
                                <User size={16} />
                                Username
                            </span>
                        }
                        type="text"
                        name="username"
                        value={user.username}
                        readOnly
                        autoComplete="username"
                        className="bg-dark-700 cursor-not-allowed"
                        containerClassName="mb-4"
                    />
                    <p className="text-xs text-gray-500 -mt-4">
                        Username nie może być zmieniony
                    </p>

                    {/* Full Name */}
                    <Input
                        label="Wyświetlana nazwa"
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleChange}
                        placeholder="Jan Kowalski"
                        maxLength={100}
                        autoComplete="name"
                    />

                    {/* Email */}
                    <div>
                        <Input
                            label={
                                <span className="flex items-center gap-2">
                                    <Mail size={16} />
                                    Email
                                </span>
                            }
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="email@example.com"
                            autoComplete="email"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Opcjonalne - będzie używany do resetu hasła
                        </p>
                    </div>

                    {/* Password */}
                    <div>
                        <Input
                            label={
                                <span className="flex items-center gap-2">
                                    <Lock size={16} />
                                    Nowe hasło
                                </span>
                            }
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="Zostaw puste aby nie zmieniać"
                            autoComplete="new-password"
                        />
                        <div className="flex items-center gap-2 mt-3">
                            <Button
                                type="button"
                                onClick={handleSetEmptyPasswordAndSave}
                                disabled={loading}
                                variant="danger"
                                size="sm"
                                className="inline-flex items-center gap-2"
                                title="Ustaw puste hasło i zapisz zmiany"
                            >
                                <LockOpen size={16} />
                                Ustaw puste hasło i zapisz
                            </Button>
                            <span className="text-xs text-warning">
                                Puste hasło jest niezalecane, no ale co ja ci będę bronić.
                            </span>
                        </div>
                    </div>

                    {/* Confirm Password */}
                    {formData.password && (
                        <Input
                            label="Potwierdź hasło"
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="Powtórz nowe hasło"
                            autoComplete="new-password"
                        />
                    )}

                    {/* Submit */}
                    <Button
                        type="submit"
                        disabled={loading}
                        variant="primary"
                        className="w-full"
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
                    </Button>
                </form>
            </Card>

            {/* Account Info */}
            <Card className="mt-6 p-4">
                <h3 className="font-semibold mb-2">Informacje o koncie</h3>
                <div className="text-sm text-gray-400 space-y-1">
                    <p>Typ konta: {user.is_admin ? "Administrator" : "Użytkownik"}</p>
                    <p>Status: {user.is_active ? "Aktywny" : "Nieaktywny"}</p>
                </div>
            </Card>
        </div>
    );
}

export default ProfilePage;
