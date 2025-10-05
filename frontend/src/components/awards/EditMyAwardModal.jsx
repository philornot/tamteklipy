// frontend/src/components/awards/EditMyAwardModal.jsx
import {useState} from 'react'
import {Loader, Upload, X, Sparkles} from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import {resizeImage} from '../../utils/imageResize'
import api from '../../services/api'
import toast from 'react-hot-toast'
import LucideIconSelector from '../admin/LucideIconSelector'

function EditMyAwardModal({award, onClose, onSuccess}) {
    const [formData, setFormData] = useState({
        display_name: award.display_name,
        description: award.description || '',
        color: award.color,
        lucide_icon: award.lucide_icon || ''
    })

    const [iconMode, setIconMode] = useState(
        award.icon_url ? 'custom' :
        award.lucide_icon ? 'lucide' : 'emoji'
    )

    const [loading, setLoading] = useState(false)
    const [uploadingIcon, setUploadingIcon] = useState(false)
    const [showLucideSelector, setShowLucideSelector] = useState(false)

    const handleSave = async () => {
        if (!formData.display_name) {
            toast.error('Nazwa jest wymagana')
            return
        }

        setLoading(true)

        try {
            const updateData = {
                display_name: formData.display_name,
                description: formData.description,
                color: formData.color
            }

            if (iconMode === 'lucide') {
                updateData.lucide_icon = formData.lucide_icon
            } else if (iconMode === 'emoji') {
                updateData.lucide_icon = ''
            }

            await api.patch(`/admin/award-types/${award.id}`, updateData)
            toast.success('Nagroda zaktualizowana')
            onSuccess()
            onClose()
        } catch (err) {
            toast.error(err.response?.data?.message || 'Nie udało się zaktualizować')
        } finally {
            setLoading(false)
        }
    }

    const handleIconUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        setUploadingIcon(true)

        try {
            const resized = await resizeImage(file, 128)
            const formDataUpload = new FormData()
            formDataUpload.append('file', resized)

            await api.post(`/admin/award-types/${award.id}/icon`, formDataUpload, {
                headers: {'Content-Type': 'multipart/form-data'}
            })

            toast.success('Ikona zaktualizowana')
            setIconMode('custom')
            onSuccess()
        } catch (err) {
            toast.error(err.response?.data?.message || 'Nie udało się uploadować ikony')
        } finally {
            setUploadingIcon(false)
        }
    }

    const renderCurrentIcon = () => {
        if (award.icon_url) {
            return (
                <img
                    src={`${import.meta.env.VITE_API_URL}${award.icon_url}`}
                    alt="Custom icon"
                    className="w-16 h-16 rounded"
                />
            )
        } else if (award.lucide_icon) {
            const componentName = award.lucide_icon
                .split('-')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join('')
            const IconComponent = LucideIcons[componentName]
            return IconComponent ? (
                <IconComponent size={64}/>
            ) : (
                <span className="text-4xl">🏆</span>
            )
        } else {
            return <span className="text-4xl">{award.icon}</span>
        }
    }

    const renderIconPreview = () => {
        if (iconMode === 'custom' && award.icon_url) {
            return (
                <img
                    src={`${import.meta.env.VITE_API_URL}${award.icon_url}`}
                    alt="Custom icon"
                    className="w-16 h-16 rounded"
                />
            )
        } else if (iconMode === 'lucide' && formData.lucide_icon) {
            const componentName = formData.lucide_icon
                .split('-')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join('')
            const IconComponent = LucideIcons[componentName]
            return IconComponent ? (
                <IconComponent size={64}/>
            ) : (
                <span className="text-4xl">🏆</span>
            )
        } else {
            return <span className="text-4xl">{award.icon}</span>
        }
    }

    return (
        <div
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            onClick={onClose}
        >
            <div
                className="bg-gray-800 rounded-lg max-w-lg w-full p-6 border border-gray-700 max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">Edytuj nagrodę</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
                        <X size={20}/>
                    </button>
                </div>

                <div className="mb-4 p-4 bg-gray-900 rounded border border-gray-700 text-center">
                    <p className="text-sm text-gray-400 mb-2">Aktualna ikona:</p>
                    <div className="flex justify-center">{renderCurrentIcon()}</div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-gray-300 mb-2">Nazwa wyświetlana</label>
                        <input
                            type="text"
                            value={formData.display_name}
                            onChange={(e) =>
                                setFormData({...formData, display_name: e.target.value})
                            }
                            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            maxLength={100}
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Opis</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) =>
                                setFormData({...formData, description: e.target.value})
                            }
                            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            rows={3}
                            maxLength={500}
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Kolor</label>
                        <div className="flex gap-2">
                            <input
                                type="color"
                                value={formData.color}
                                onChange={(e) =>
                                    setFormData({...formData, color: e.target.value})
                                }
                                className="h-10 w-20 rounded cursor-pointer"
                            />
                            <input
                                type="text"
                                value={formData.color}
                                onChange={(e) =>
                                    setFormData({...formData, color: e.target.value})
                                }
                                className="flex-1 bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Typ ikony</label>
                        <div className="flex gap-2 mb-3">
                            <button
                                type="button"
                                onClick={() => setIconMode('emoji')}
                                className={`flex-1 px-4 py-2 rounded-lg transition ${
                                    iconMode === 'emoji'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                            >
                                Emoji
                            </button>
                            <button
                                type="button"
                                onClick={() => setIconMode('lucide')}
                                className={`flex-1 px-4 py-2 rounded-lg transition ${
                                    iconMode === 'lucide'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                            >
                                Lucide
                            </button>
                            <button
                                type="button"
                                onClick={() => setIconMode('custom')}
                                className={`flex-1 px-4 py-2 rounded-lg transition ${
                                    iconMode === 'custom'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                            >
                                Custom
                            </button>
                        </div>

                        <div className="p-4 bg-gray-900 rounded border border-gray-700 text-center mb-3">
                            <p className="text-xs text-gray-400 mb-2">Podgląd:</p>
                            <div className="flex justify-center">{renderIconPreview()}</div>
                        </div>

                        {iconMode === 'lucide' && (
                            <div>
                                <button
                                    type="button"
                                    onClick={() => setShowLucideSelector(true)}
                                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center justify-center gap-2"
                                >
                                    <Sparkles size={20}/>
                                    Wybierz Lucide Icon
                                </button>
                                {formData.lucide_icon && (
                                    <div className="text-sm text-gray-400 text-center mt-2">
                                        Wybrano: <strong>{formData.lucide_icon}</strong>
                                    </div>
                                )}
                            </div>
                        )}

                        {iconMode === 'custom' && (
                            <label className="block">
                                <input
                                    type="file"
                                    accept="image/png,image/jpeg"
                                    onChange={handleIconUpload}
                                    className="hidden"
                                    id={`icon-upload-${award.id}`}
                                />
                                <div
                                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center justify-center gap-2 cursor-pointer">
                                    {uploadingIcon ? (
                                        <>
                                            <Loader className="animate-spin" size={20}/>
                                            Uploading...
                                        </>
                                    ) : (
                                        <>
                                            <Upload size={20}/>
                                            Upload Custom Icon
                                        </>
                                    )}
                                </div>
                            </label>
                        )}
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
                        >
                            Anuluj
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={loading}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
                        >
                            {loading ? 'Zapisywanie...' : 'Zapisz'}
                        </button>
                    </div>
                </div>
            </div>

            {showLucideSelector && (
                <LucideIconSelector
                    selectedIcon={formData.lucide_icon}
                    onSelect={(icon) => {
                        setFormData({...formData, lucide_icon: icon})
                        setShowLucideSelector(false)
                    }}
                    onClose={() => setShowLucideSelector(false)}
                />
            )}
        </div>
    )
}

export default EditMyAwardModal