import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle,
  FileVideo,
  Image as ImageIcon,
  Loader,
  Upload,
  X,
} from "lucide-react";
import toast from "react-hot-toast";
import useOptimizedUpload from "../hooks/useOptimizedUpload";
import { usePageTitle } from "../hooks/usePageTitle";
import { Button, Card, Badge } from "../components/ui/StyledComponents";

const MAX_VIDEO_SIZE = 500 * 1024 * 1024;
const MAX_IMAGE_SIZE = 100 * 1024 * 1024;
const ALLOWED_VIDEO = ["video/mp4", "video/webm", "video/quicktime"];
const ALLOWED_IMAGE = ["image/png", "image/jpeg", "image/jpg"];

function UploadPage() {
  usePageTitle("Upload");
  const navigate = useNavigate();
  const { uploadFile } = useOptimizedUpload();

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const formatFileSize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return mb < 1
      ? `${(bytes / 1024).toFixed(0)} KB`
      : `${mb.toFixed(1)} MB`;
  };

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
    if (e.target.files?.length > 0) {
      validateAndAddFiles(e.target.files);
      e.target.value = "";
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (["dragenter", "dragover"].includes(e.type)) setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.length > 0) {
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
        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "uploading", progress: 0 } : f
          )
        );

        await uploadFile(fileObj.file, (progress) => {
          setSelectedFiles((prev) =>
            prev.map((f, idx) =>
              idx === i ? { ...f, progress } : f
            )
          );
        });

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "success", progress: 100 } : f
          )
        );

        successCount++;
        toast.success(`${fileObj.file.name} - przesłano!`);
      } catch (error) {
        const msg =
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          "Nieznany błąd";

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: "error", error: msg, progress: 0 }
              : f
          )
        );

        errorCount++;
        toast.error(`${fileObj.file.name} - błąd: ${msg}`);
      }
    }

    setUploading(false);

    if (successCount > 0 && errorCount === 0) {
      toast.success(`Wszystkie pliki przesłane (${successCount})`);
      setTimeout(() => navigate("/dashboard"), 1500);
    } else if (successCount > 0 && errorCount > 0) {
      toast(`Sukces: ${successCount}, Błędy: ${errorCount}`, { icon: "⚠️" });
    }
  };

  const pendingFiles = selectedFiles.filter((f) => f.status === "pending").length;
  const successFiles = selectedFiles.filter((f) => f.status === "success").length;
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
          className={`border-2 border-dashed rounded-card p-12 text-center transition-all duration-300 ${
            dragActive
              ? "border-primary-500 bg-primary-500/10"
              : "border-dark-600 hover:border-primary-500"
          } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            id="file-input"
            type="file"
            multiple
            accept={ALLOWED_VIDEO.concat(ALLOWED_IMAGE).join(",")}
            onChange={handleFileSelect}
            disabled={uploading}
            className="hidden"
          />
          <label htmlFor="file-input" className="cursor-pointer block">
            <Upload size={64} className="mx-auto mb-4 text-gray-500" />
            <p className="text-lg mb-2 text-gray-300">
              {dragActive ? "Upuść pliki tutaj" : "Kliknij lub przeciągnij pliki"}
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

          {/* Summary */}
          {(successFiles > 0 || errorFiles > 0) && (
            <div className="flex gap-4 mb-4 text-sm">
              {successFiles > 0 && (
                <Badge variant="success" className="flex items-center gap-2">
                  <CheckCircle size={16} />
                  Sukces: {successFiles}
                </Badge>
              )}
              {errorFiles > 0 && (
                <Badge variant="danger" className="flex items-center gap-2">
                  <AlertCircle size={16} />
                  Błędy: {errorFiles}
                </Badge>
              )}
              {pendingFiles > 0 && (
                <Badge variant="default" className="flex items-center gap-2">
                  Oczekuje: {pendingFiles}
                </Badge>
              )}
            </div>
          )}

          <div className="space-y-3">
            {selectedFiles.map((fileObj, index) => (
              <Card
                key={index}
                className={`p-4 ${
                  fileObj.status === "success"
                    ? "border-success"
                    : fileObj.status === "error"
                    ? "border-danger"
                    : ""
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 bg-dark-900 rounded overflow-hidden flex-shrink-0">
                    {fileObj.type === "video" ? (
                      <video src={fileObj.preview} className="w-full h-full object-cover" />
                    ) : (
                      <img src={fileObj.preview} alt="" className="w-full h-full object-cover" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {fileObj.type === "video" ? (
                        <FileVideo size={16} className="text-primary-400" />
                      ) : (
                        <ImageIcon size={16} className="text-success" />
                      )}
                      <span className="font-medium truncate">{fileObj.file.name}</span>
                    </div>

                    <p className="text-sm text-gray-400 mb-2">
                      {formatFileSize(fileObj.file.size)}
                    </p>

                    {fileObj.status === "success" && (
                      <Badge variant="success" className="flex items-center gap-2 w-fit">
                        <CheckCircle size={14} />
                        Przesłano pomyślnie
                      </Badge>
                    )}

                    {fileObj.status === "error" && (
                      <Badge variant="danger" className="flex items-center gap-2 w-fit">
                        <AlertCircle size={14} />
                        Błąd: {fileObj.error}
                      </Badge>
                    )}

                    {fileObj.status === "uploading" && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-primary-400 text-sm">
                          <Loader size={14} className="animate-spin" />
                          <span>Wysyłanie... {fileObj.progress}%</span>
                        </div>
                        <div className="w-full bg-dark-700 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-primary-500 h-full transition-all duration-300"
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

                  {!uploading && (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 hover:bg-dark-700 rounded-button transition text-gray-400 hover:text-red-400"
                      title="Usuń"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      {selectedFiles.length > 0 && pendingFiles > 0 && (
        <Button
          onClick={handleUpload}
          disabled={uploading}
          variant="primary"
          className="w-full"
        >
          {uploading ? (
            <>
              <Loader className="animate-spin" size={20} />
              Wysyłanie {pendingFiles} plików...
            </>
          ) : (
            <>
              <Upload size={20} />
              Wyślij {pendingFiles} {pendingFiles === 1 ? "plik" : "plików"}
            </>
          )}
        </Button>
      )}

      <Card variant="glow" className="mt-8 p-4">
        <h3 className="font-semibold mb-2 text-sm text-primary-400">
          Informacje
        </h3>
        <ul className="text-sm text-gray-400 space-y-1">
          <li>• Wiele plików naraz</li>
          <li>• Video: MP4, WebM, MOV (max {MAX_VIDEO_SIZE / (1024 * 1024)}MB)</li>
          <li>• Obrazy: PNG, JPG (max {MAX_IMAGE_SIZE / (1024 * 1024)}MB)</li>
        </ul>
      </Card>
    </div>
  );
}

export default UploadPage;
