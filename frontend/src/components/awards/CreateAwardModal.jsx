import {useState} from 'react'
import {Loader, Upload, X} from 'lucide-react'
import {resizeImage} from '../../utils/imageResize'
import api from '../../services/api'
import toast from 'react-hot-toast'

function CreateAwardModal({onClose, onSuccess}) {
    const [displayName, setDisplayName] = useState('')
    const [description, setDescription] = useState('')
    const [color, setColor] = useState('#FFD700')
    const [selectedFile, setSelectedFile] = useState(null)
    const [preview, setPreview] = useState(null)
    const [resizedPreview, setResizedPreview] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleFileSelect = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        try {
            // Original preview
            setPreview(URL.createObjectURL(file))
            setSelectedFile(file)

            // Resize
            const resized = await resizeImage(file, 128)
            setResizedPreview(URL.createObjectURL(resized))
            setSelectedFile(resized)
        } catch (err) {
            toast.error(err.message)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!displayName || !selectedFile) {
            toast.error('Nazwa i ikona są wymagane')
            return
        }

        setLoading(true)

        try {
            // 1. Create award type
            const createResponse = await api.post('/my-awards/my-award-types', null, {
                params: {
                    display_name: displayName,
                    description,
                    color
                }
            })

            const awardTypeId = createResponse.data.id

            // 2. Upload icon
            const formData = new FormData()
            formData.append('file', selectedFile)

            await api.post(`/admin/award-types/${awardTypeId}/icon`, formData, {
                headers: {'Content-Type': 'multipart/form-data'}
            })

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
                className="bg-gray-800 rounded-lg max-w-md w-full p-6 border border-gray-700"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">Utwórz własną nagrodę</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded">
                        <X size={20}/>
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    {/* Display Name */}
                    <div className="mb-4">
                        <label className="block text-gray-300 mb-2">Nazwa nagrody *</label>
                        <input
                            type="text"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            className="input-field w-full"
                            placeholder="Epic Play"
                            maxLength={50}
                            required
                        />
                    </div>

                    {/* Description */}
                    <div className="mb-4">
                        <label className="block text-gray-300 mb-2">Opis</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="input-field w-full"
                            placeholder="Za niesamowitą zagrywkę..."
                            rows={3}
                            maxLength={200}
                        />
                    </div>

                    {/* Color */}
                    <div className="mb-4">
                        <label className="block text-gray-300 mb-2">Kolor</label>
                        <input
                            type="color"
                            value={color}
                            onChange={(e) => setColor(e.target.value)}
                            className="h-10 w-20 rounded cursor-pointer"
                        />
                    </div>

                    {/* Icon Upload */}
                    <div className="mb-4">
                        <label className="block text-gray-300 mb-2">Ikona * (128x128px)</label>
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
                                    <img src={resizedPreview} alt="Preview" className="w-32 h-32 mx-auto mb-2"/>
                                    <p className="text-sm text-gray-400">Kliknij aby zmienić</p>
                                </div>
                            ) : (
                                <div>
                                    <Upload size={32} className="mx-auto mb-2 text-gray-400"/>
                                    <p className="text-gray-400">Wybierz obrazek</p>
                                    <p className="text-xs text-gray-500 mt-1">PNG/JPG, max 10MB</p>
                                </div>
                            )}
                        </label>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading || !displayName || !selectedFile}
                        className="btn-primary w-full flex items-center justify-center gap-2"
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
                </form>

                <p className="text-xs text-gray-500 mt-4">
                    Możesz utworzyć maksymalnie 5 własnych nagród
                </p>
            </div>
        </div>
    )
}

export default CreateAwardModal