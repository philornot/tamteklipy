import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  X,
  FileVideo,
  Image as ImageIcon,
  Loader,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";

const MAX_VIDEO_SIZE = 500 * 1024 * 1024;
const MAX_IMAGE_SIZE = 100 * 1024 * 1024;
const ALLOWED_VIDEO = ["video/mp4", "video/webm", "video/quicktime"];
const ALLOWED_IMAGE = ["image/png", "image/jpeg", "image/jpg"];

function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const validateAndAddFiles = (files) => {
    const fileArray = Array.from(files);
    const validFiles = [];

    for (const file of fileArray) {
      const isVideo = ALLOWED_VIDEO.includes(file.type);
      const isImage = ALLOWED_IMAGE.includes(file.type);

      if (!isVideo && !isImage) {
        toast.error(`${file.name}: Niedozwolony format pliku`);
        continue;
      }

      const maxSize = isVideo ? MAX_VIDEO_SIZE : MAX_IMAGE_SIZE;
      if (file.size > maxSize) {
        const maxMB = Math.round(maxSize / (1024 * 1024));
        toast.error(`${file.name}: Plik za duży (max ${maxMB}MB)`);
        continue;
      }

      validFiles.push({
        file,
        preview: URL.createObjectURL(file),
        type: isVideo ? "video" : "image",
        status: "pending",
        progress: 0,
        error: null,
      });
    }

    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles]);
      toast.success(`Dodano ${validFiles.length} plików`);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(e.target.files);
      e.target.value = "";
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => {
      const newFiles = [...prev];
      URL.revokeObjectURL(newFiles[index].preview);
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const fileObj = selectedFiles[i];

      if (fileObj.status !== "pending") continue;

      try {
        const formData = new FormData();
        formData.append("file", fileObj.file);

        const response = await api.post("/files/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );

              setSelectedFiles((prev) =>
                prev.map((f, idx) =>
                  idx === i ? { ...f, progress: percentCompleted } : f
                )
              );
            }
          },
        });

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "success", progress: 100 } : f
          )
        );

        successCount++;
        toast.success(`${fileObj.file.name} - przesłano!`);
      } catch (error) {
        const errorMessage =
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          "Nieznany błąd";

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: "error", error: errorMessage, progress: 0 }
              : f
          )
        );

        errorCount++;
        toast.error(`${fileObj.file.name} - błąd: ${errorMessage}`);
      }
    }

    setUploading(false);

    if (successCount > 0 && errorCount === 0) {
      toast.success(`Wszystkie pliki przesłane (${successCount})`);
      setTimeout(() => navigate("/dashboard"), 1500);
    } else if (successCount > 0 && errorCount > 0) {
      toast(`Sukces: ${successCount}, Błędy: ${errorCount}`, {
        icon: "⚠️",
      });
    }
  };

  const formatFileSize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  };

  const pendingFiles = selectedFiles.filter(
    (f) => f.status === "pending"
  ).length;
  const successFiles = selectedFiles.filter(
    (f) => f.status === "success"
  ).length;
  const errorFiles = selectedFiles.filter((f) => f.status === "error").length;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Upload Plików</h1>
        <p className="text-gray-400">Prześlij klipy video lub screenshoty</p>
      </div>

      {/* Drag & Drop Area */}
      <div className="mb-6">
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive
              ? "border-purple-500 bg-purple-500/10"
              : "border-gray-600 hover:border-purple-500"
          } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            multiple
            accept=".mp4,.webm,.mov,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
            disabled={uploading}
            className="hidden"
            id="file-input"
          />

          <label htmlFor="file-input" className="cursor-pointer block">
            <Upload size={64} className="mx-auto mb-4 text-gray-500" />

            <p className="text-lg mb-2 text-gray-300">
              {dragActive
                ? "Upuść pliki tutaj"
                : "Kliknij lub przeciągnij pliki"}
            </p>

            <div className="text-sm text-gray-500 space-y-1">
                <p>Video: MP4, WebM, MOV (max {MAX_VIDEO_SIZE / (1024 * 1024)}MB)</p>
                <p>Obrazy: PNG, JPG (max {MAX_IMAGE_SIZE / (1024 * 1024)}MB)</p>
            </div>
          </label>
        </div>
      </div>

      {/* Files List */}
      {selectedFiles.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              Pliki ({selectedFiles.length})
            </h2>

            {!uploading && (
              <button
                onClick={() => {
                  selectedFiles.forEach((f) => URL.revokeObjectURL(f.preview));
                  setSelectedFiles([]);
                  toast.success("Wyczyszczono listę");
                }}
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Wyczyść wszystko
              </button>
            )}
          </div>

          {/* Status Summary */}
          {(successFiles > 0 || errorFiles > 0) && (
            <div className="flex gap-4 mb-4 text-sm">
              {successFiles > 0 && (
                <div className="flex items-center gap-2 text-green-400">
                  <CheckCircle size={16} />
                  <span>Sukces: {successFiles}</span>
                </div>
              )}
              {errorFiles > 0 && (
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle size={16} />
                  <span>Błędy: {errorFiles}</span>
                </div>
              )}
              {pendingFiles > 0 && (
                <div className="flex items-center gap-2 text-gray-400">
                  <span>Oczekuje: {pendingFiles}</span>
                </div>
              )}
            </div>
          )}

          <div className="space-y-3">
            {selectedFiles.map((fileObj, index) => (
              <div
                key={index}
                className={`bg-gray-800 rounded-lg p-4 border transition-colors ${
                  fileObj.status === "success"
                    ? "border-green-700"
                    : fileObj.status === "error"
                    ? "border-red-700"
                    : "border-gray-700"
                }`}
              >
                <div className="flex items-center gap-4">
                  {/* Preview */}
                  <div className="w-20 h-20 bg-gray-900 rounded flex-shrink-0 overflow-hidden">
                    {fileObj.type === "video" ? (
                      <video
                        src={fileObj.preview}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <img
                        src={fileObj.preview}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {fileObj.type === "video" ? (
                        <FileVideo size={16} className="text-purple-400" />
                      ) : (
                        <ImageIcon size={16} className="text-green-400" />
                      )}
                      <span className="font-medium truncate">
                        {fileObj.file.name}
                      </span>
                    </div>

                    <p className="text-sm text-gray-400 mb-2">
                      {formatFileSize(fileObj.file.size)}
                    </p>

                    {/* Status */}
                    {fileObj.status === "success" && (
                      <div className="flex items-center gap-2 text-green-400 text-sm">
                        <CheckCircle size={14} />
                        <span>Przesłano pomyślnie</span>
                      </div>
                    )}

                    {fileObj.status === "error" && (
                      <div className="flex items-center gap-2 text-red-400 text-sm">
                        <AlertCircle size={14} />
                        <span>Błąd: {fileObj.error}</span>
                      </div>
                    )}

                    {fileObj.status === "pending" && uploading && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-purple-400 text-sm">
                          <Loader size={14} className="animate-spin" />
                          <span>Wysyłanie... {fileObj.progress}%</span>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-purple-500 h-full transition-all duration-300"
                            style={{ width: `${fileObj.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {fileObj.status === "pending" && !uploading && (
                      <span className="text-sm text-gray-500">
                        Oczekuje na wysłanie
                      </span>
                    )}
                  </div>

                  {/* Remove button */}
                  {!uploading && (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 hover:bg-gray-700 rounded transition text-gray-400 hover:text-red-400"
                      title="Usuń"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      {selectedFiles.length > 0 && pendingFiles > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <Loader className="animate-spin" size={20} />
              <span>Wysyłanie {pendingFiles} plików...</span>
            </>
          ) : (
            <>
              <Upload size={20} />
              <span>
                Wyślij {pendingFiles} {pendingFiles === 1 ? "plik" : "plików"}
              </span>
            </>
          )}
        </button>
      )}

      {/* Uproszczony info box */}
      <div className="mt-8 bg-gray-800 rounded-lg p-4 border border-purple-700/30">
        <h3 className="font-semibold mb-2 text-sm text-purple-400">Informacje</h3>
        <ul className="text-sm text-gray-400 space-y-1">
          <li>• Wiele plików naraz</li>
          <li>• Video: MP4, WebM, MOV (max {MAX_VIDEO_SIZE / (1024 * 1024)}MB)</li>
          <li>• Obrazy: PNG, JPG (max {MAX_IMAGE_SIZE / (1024 * 1024)}MB)</li>
        </ul>
      </div>
    </div>
  );
}

export default UploadPage;
