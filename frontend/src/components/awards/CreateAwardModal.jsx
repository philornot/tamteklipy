import {useState} from 'react'
import {Loader, Upload, X, Sparkles} from 'lucide-react'
import {resizeImage} from '../../utils/imageResize'
import api from '../../services/api'
import toast from 'react-hot-toast'
import LucideIconSelector from '../admin/LucideIconSelector'

function CreateAwardModal({onClose, onSuccess}) {
    const [displayName, setDisplayName] = useState('')
    const [description, setDescription] = useState('')
    const [color, setColor] = useState('#FFD700')
    const [iconMode, setIconMode] = useState('lucide')
    const [selectedFile, setSelectedFile] = useState(null)
    const [resizedPreview, setResizedPreview] = useState(null)
    const [selectedLucideIcon, setSelectedLucideIcon] = useState('')
    const [showLucideSelector, setShowLucideSelector] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleFileSelect = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        try {
            const resized = await resizeImage(file, 128)
            setResizedPreview(URL.createObjectURL(resized))
            setSelectedFile(resized)
        } catch (err) {
            toast.error(err.message)
        }
    }

    const handleSubmit = async () => {
        if (!displayName) {
            toast.error('Nazwa jest wymagana')
            return
        }

        if (iconMode === 'custom' && !selectedFile) {
            toast.error('Wybierz ikonę lub zmień tryb na Lucide')
            return
        }

        if (iconMode === 'lucide' && !selectedLucideIcon) {
            toast.error('Wybierz ikonę Lucide lub zmień tryb na Custom')
            return
        }

        setLoading(true)

        try {
            const createResponse = await api.post('/my-awards/my-award-types', null, {
                params: {
                    display_name: displayName,
                    description,
                    color
                }
            })

            const awardTypeId = createResponse.data.id

            if (iconMode === 'custom' && selectedFile) {
                const formData = new FormData()
                formData.append('file', selectedFile)

                await api.post(`/admin/award-types/${awardTypeId}/icon`, formData, {
                    headers: {'Content-Type': 'multipart/form-data'}
                })
            } else if (iconMode === 'lucide' && selectedLucideIcon) {
                await api.patch(`/admin/award-types/${awardTypeId}`, {
                    lucide_icon: selectedLucideIcon
                })
            }

            toast.success('Nagroda utworzona!')
            onSuccess()
            onClose()
        } catch (err) {
            console.error('Failed to create award:', err)
            toast.error(err.response?.data?.message || 'Nie udało się utworzyć nagrody')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div
                className="bg-gray-800 rounded-lg max-w-md w-full p-6 border border-gray-700 max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">Utwórz własną nagrodę</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
                        <X size={20}/>
                    </button>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-gray-300 mb-2">Nazwa nagrody *</label>
                        <input
                            type="text"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            placeholder="Epic Play"
                            maxLength={50}
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Opis</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            placeholder="Za niesamowitą zagrywkę..."
                            rows={3}
                            maxLength={200}
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Kolor</label>
                        <div className="flex gap-2">
                            <input
                                type="color"
                                value={color}
                                onChange={(e) => setColor(e.target.value)}
                                className="h-10 w-20 rounded cursor-pointer"
                            />
                            <input
                                type="text"
                                value={color}
                                onChange={(e) => setColor(e.target.value)}
                                className="flex-1 bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-lg"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-gray-300 mb-2">Typ ikony *</label>
                        <div className="flex gap-2 mb-3">
                            <button
                                type="button"
                                onClick={() => setIconMode('lucide')}
                                className={`flex-1 px-4 py-2 rounded-lg transition ${
                                    iconMode === 'lucide'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                }`}
                            >
                                ✨ Lucide
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
                                📁 Custom
                            </button>
                        </div>

                        {iconMode === 'lucide' && (
                            <div>
                                <button
                                    type="button"
                                    onClick={() => setShowLucideSelector(true)}
                                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition flex items-center justify-center gap-2"
                                >
                                    <Sparkles size={20}/>
                                    Wybierz ikonę Lucide
                                </button>
                                {selectedLucideIcon && (
                                    <div className="text-sm text-gray-400 text-center mt-2">
                                        Wybrano: <strong>{selectedLucideIcon}</strong>
                                    </div>
                                )}
                            </div>
                        )}

                        {iconMode === 'custom' && (
                            <div>
                                <input
                                    type="file"
                                    accept="image/png,image/jpeg"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                    id="icon-upload"
                                />
                                <label
                                    htmlFor="icon-upload"
                                    className="border-2 border-dashed border-gray-600 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition block"
                                >
                                    {resizedPreview ? (
                                        <div>
                                            <img src={resizedPreview} alt="Preview"
                                                 className="w-32 h-32 mx-auto mb-2"/>
                                            <p className="text-sm text-gray-400">Kliknij aby zmienić</p>
                                        </div>
                                    ) : (
                                        <div>
                                            <Upload size={32} className="mx-auto mb-2 text-gray-400"/>
                                            <p className="text-gray-400">Wybierz obrazek</p>
                                            <p className="text-xs text-gray-500 mt-1">PNG/JPG, max 100MB</p>
                                        </div>
                                    )}
                                </label>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleSubmit}
                        disabled={loading || !displayName || (iconMode === 'custom' && !selectedFile) || (iconMode === 'lucide' && !selectedLucideIcon)}
                        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader className="animate-spin" size={20}/>
                                Tworzenie...
                            </>
                        ) : (
                            'Utwórz nagrodę'
                        )}
                    </button>
                </div>

                <p className="text-xs text-gray-500 mt-4 text-center">
                    Możesz utworzyć maksymalnie 5 własnych nagród
                </p>
            </div>

            {showLucideSelector && (
                <LucideIconSelector
                    selectedIcon={selectedLucideIcon}
                    onSelect={(icon) => {
                        setSelectedLucideIcon(icon)
                        setShowLucideSelector(false)
                    }}
                    onClose={() => setShowLucideSelector(false)}
                />
            )}
        </div>
    )
}

export default CreateAwardModal