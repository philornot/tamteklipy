import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileVideo,
  Image as ImageIcon,
  Loader,
  CheckCircle,
  X,
  AlertCircle,
} from "lucide-react";
import toast from "react-hot-toast";
import api from "../services/api";
import { usePageTitle } from "../hooks/usePageTitle";
import { Button, Card, Badge } from "../components/ui/StyledComponents";

const MAX_VIDEO_SIZE = 500 * 1024 * 1024; // 500MB
const MAX_IMAGE_SIZE = 100 * 1024 * 1024; // 100MB
const ALLOWED_VIDEO = ["video/mp4", "video/webm", "video/quicktime"];
const ALLOWED_IMAGE = ["image/png", "image/jpeg", "image/jpg"];

function UploadPage() {
  usePageTitle("Upload");
  const navigate = useNavigate();

  const [files, setFiles] = useState([]); // Array z plikami i ich statusami
  const [dragActive, setDragActive] = useState(false);
  const uploadingRef = useRef(false);

  const formatFileSize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  };

  const validateAndAddFiles = (selectedFiles) => {
    const fileArray = Array.from(selectedFiles);
    const validFiles = [];

    for (const file of fileArray) {
      const isVideo = ALLOWED_VIDEO.includes(file.type);
      const isImage = ALLOWED_IMAGE.includes(file.type);

      if (!isVideo && !isImage) {
        toast.error(`${file.name}: Niedozwolony format`);
        continue;
      }

      const maxSize = isVideo ? MAX_VIDEO_SIZE : MAX_IMAGE_SIZE;
      if (file.size > maxSize) {
        const maxMB = Math.round(maxSize / (1024 * 1024));
        toast.error(`${file.name}: Za duży (max ${maxMB}MB)`);
        continue;
      }

      validFiles.push({
        file,
        preview: URL.createObjectURL(file),
        status: "pending", // pending, uploading, processing, success, error
        progress: 0,
        clipId: null,
        error: null,
        isVideo: isVideo,
      });
    }

    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
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
    setFiles((prev) => {
      const newFiles = [...prev];
      URL.revokeObjectURL(newFiles[index].preview);
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const uploadSingleFile = async (fileObj, index) => {
    const formData = new FormData();
    formData.append("file", fileObj.file);

    try {
      // Update status: uploading
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: "uploading", progress: 0 } : f
        )
      );

      const response = await api.post("/files/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) {
            const progress = Math.round((e.loaded * 100) / e.total);
            setFiles((prev) =>
              prev.map((f, i) => (i === index ? { ...f, progress } : f))
            );
          }
        },
      });

      const clipId = response.data.clip_id;

      // Update status: processing (czeka na thumbnail)
      setFiles((prev) =>
        prev.map((f, i) =>
          i === index
            ? { ...f, status: "processing", clipId, progress: 100 }
            : f
        )
      );

      // Poll thumbnail status
      await pollThumbnailStatus(clipId, index);

    } catch (error) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        "Błąd uploadu";

      setFiles((prev) =>
        prev.map((f, i) =>
          i === index ? { ...f, status: "error", error: msg } : f
        )
      );
    }
  };

  const pollThumbnailStatus = async (clipId, index) => {
    const maxAttempts = 30; // 30 * 2s = 60s max
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await api.get(`/files/clips/${clipId}/thumbnail-status`);

        if (response.data.status === "ready") {
          setFiles((prev) =>
            prev.map((f, i) =>
              i === index ? { ...f, status: "success" } : f
            )
          );
          return true;
        }

        attempts++;
        if (attempts >= maxAttempts) {
          // Timeout - ale to nie błąd, po prostu thumbnail trwa długo
          setFiles((prev) =>
            prev.map((f, i) =>
              i === index ? { ...f, status: "success" } : f
            )
          );
          return true;
        }

        // Czekaj 2s i spróbuj ponownie
        await new Promise((resolve) => setTimeout(resolve, 2000));
        return poll();
      } catch (error) {
        // Błąd podczas pollingu - ale plik jest już uploadowany
        setFiles((prev) =>
          prev.map((f, i) =>
            i === index ? { ...f, status: "success" } : f
          )
        );
        return true;
      }
    };

    return poll();
  };

  const handleUploadAll = async () => {
    if (uploadingRef.current) return;
    uploadingRef.current = true;

    const pendingFiles = files
      .map((f, index) => ({ ...f, index }))
      .filter((f) => f.status === "pending");

    if (pendingFiles.length === 0) {
      uploadingRef.current = false;
      return;
    }

    toast.success(`Rozpoczynam upload ${pendingFiles.length} plików...`);

    // Upload sekwencyjnie (jeden po drugim)
    for (const fileObj of pendingFiles) {
      await uploadSingleFile(fileObj, fileObj.index);
    }

    uploadingRef.current = false;

    // Wszystkie pliki uploadowane
    const allSuccess = files.every((f) =>
      f.status === "success" || f.status === "pending"
    );

    if (allSuccess) {
      toast.success("Wszystkie pliki przesłane!");
      setTimeout(() => {
        navigate("/dashboard", { state: { fromUpload: true } });
      }, 1500);
    } else {
      toast("Niektóre pliki nie zostały przesłane", { icon: "⚠️" });
    }
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const uploadingCount = files.filter(
    (f) => f.status === "uploading" || f.status === "processing"
  ).length;
  const successCount = files.filter((f) => f.status === "success").length;
  const errorCount = files.filter((f) => f.status === "error").length;

  const isUploading = uploadingRef.current || uploadingCount > 0;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Upload Plików</h1>
        <p className="text-gray-400">
          Prześlij klipy video lub screenshoty (wiele naraz)
        </p>
      </div>

      {/* Drag & Drop Area */}
      <div className="mb-6">
        <div
          className={`border-2 border-dashed rounded-card p-12 text-center transition-all duration-300 ${
            dragActive
              ? "border-primary-500 bg-primary-500/10"
              : "border-dark-600 hover:border-primary-500"
          } ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
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
            disabled={isUploading}
            className="hidden"
          />
          <label htmlFor="file-input" className="cursor-pointer block">
            <Upload size={64} className="mx-auto mb-4 text-gray-500" />
            <p className="text-lg mb-2 text-gray-300">
              {dragActive
                ? "Upuść pliki tutaj"
                : "Kliknij lub przeciągnij pliki"}
            </p>
            <div className="text-sm text-gray-500 space-y-1">
              <p>Video: MP4, WebM, MOV (max 500MB)</p>
              <p>Obrazy: PNG, JPG (max 100MB)</p>
              <p className="text-primary-400 mt-2">
                💡 Możesz wybrać wiele plików naraz
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Files List */}
      {files.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Pliki ({files.length})</h2>
            {!isUploading && files.length > 0 && (
              <button
                onClick={() => {
                  files.forEach((f) => URL.revokeObjectURL(f.preview));
                  setFiles([]);
                }}
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Wyczyść wszystko
              </button>
            )}
          </div>

          {/* Summary */}
          {(successCount > 0 || errorCount > 0 || uploadingCount > 0) && (
            <div className="flex flex-wrap gap-2 mb-4 text-sm">
              {uploadingCount > 0 && (
                <Badge variant="default" className="flex items-center gap-2">
                  <Loader size={14} className="animate-spin" />
                  Wysyłanie: {uploadingCount}
                </Badge>
              )}
              {successCount > 0 && (
                <Badge variant="success" className="flex items-center gap-2">
                  <CheckCircle size={14} />
                  Sukces: {successCount}
                </Badge>
              )}
              {errorCount > 0 && (
                <Badge variant="danger" className="flex items-center gap-2">
                  <AlertCircle size={14} />
                  Błędy: {errorCount}
                </Badge>
              )}
              {pendingCount > 0 && (
                <Badge className="flex items-center gap-2">
                  Oczekuje: {pendingCount}
                </Badge>
              )}
            </div>
          )}

          {/* Files */}
          <div className="space-y-3">
            {files.map((fileObj, index) => (
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
                  {/* Preview */}
                  <div className="w-20 h-20 bg-dark-900 rounded overflow-hidden flex-shrink-0">
                    {fileObj.isVideo ? (
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
                      {fileObj.isVideo ? (
                        <FileVideo size={16} className="text-primary-400" />
                      ) : (
                        <ImageIcon size={16} className="text-success" />
                      )}
                      <span className="font-medium truncate text-sm">
                        {fileObj.file.name}
                      </span>
                    </div>

                    <p className="text-xs text-gray-400 mb-2">
                      {formatFileSize(fileObj.file.size)}
                    </p>

                    {/* Status */}
                    {fileObj.status === "pending" && (
                      <Badge variant="default" size="sm">
                        Oczekuje
                      </Badge>
                    )}

                    {fileObj.status === "uploading" && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs text-primary-400">
                          <Loader size={12} className="animate-spin" />
                          Wysyłanie... {fileObj.progress}%
                        </div>
                        <div className="w-full bg-dark-700 rounded-full h-1 overflow-hidden">
                          <div
                            className="bg-primary-500 h-full transition-all"
                            style={{ width: `${fileObj.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {fileObj.status === "processing" && (
                      <Badge variant="default" size="sm" className="flex items-center gap-1 w-fit">
                        <Loader size={12} className="animate-spin" />
                        Generowanie miniaturki...
                      </Badge>
                    )}

                    {fileObj.status === "success" && (
                      <Badge variant="success" size="sm" className="flex items-center gap-1 w-fit">
                        <CheckCircle size={12} />
                        Przesłano
                      </Badge>
                    )}

                    {fileObj.status === "error" && (
                      <Badge variant="danger" size="sm" className="flex items-center gap-1 w-fit">
                        <AlertCircle size={12} />
                        {fileObj.error || "Błąd"}
                      </Badge>
                    )}
                  </div>

                  {/* Remove Button */}
                  {!isUploading && fileObj.status === "pending" && (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 hover:bg-dark-700 rounded-button transition text-gray-400 hover:text-red-400"
                    >
                      <X size={18} />
                    </button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      {pendingCount > 0 && (
        <Button
          onClick={handleUploadAll}
          disabled={isUploading}
          variant="primary"
          className="w-full"
        >
          {isUploading ? (
            <>
              <Loader className="animate-spin" size={20} />
              Wysyłanie...
            </>
          ) : (
            <>
              <Upload size={20} />
              Wyślij {pendingCount} {pendingCount === 1 ? "plik" : "plików"}
            </>
          )}
        </Button>
      )}

      {/* Info */}
      <Card variant="glow" className="mt-8 p-4">
        <ul className="text-sm text-gray-400 space-y-1">
          <li>• Wybierz wiele plików naraz (Ctrl+klik lub przeciągnij)</li>
          <li>• Pliki są wysyłane kolejno, jeden po drugim</li>
          <li>• Miniaturki generują się w tle (~10s każda)</li>
          <li>• Automatyczne przekierowanie gdy wszystkie gotowe</li>
        </ul>
      </Card>
    </div>
  );
}

export default UploadPage;
