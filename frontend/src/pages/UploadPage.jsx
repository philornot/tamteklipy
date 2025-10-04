import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  X,
  FileVideo,
  Image as ImageIcon,
  Loader,
  CheckCircle,
} from "lucide-react";
import api from "../services/api";
import toast from "react-hot-toast";

function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const MAX_VIDEO_SIZE = 500 * 1024 * 1024;
  const MAX_IMAGE_SIZE = 10 * 1024 * 1024;
  const ALLOWED_VIDEO = ["video/mp4", "video/webm", "video/quicktime"];
  const ALLOWED_IMAGE = ["image/png", "image/jpeg", "image/jpg"];

  const validateAndAddFiles = (files) => {
    const fileArray = Array.from(files);

    const validFiles = fileArray.filter((file) => {
      const isVideo = ALLOWED_VIDEO.includes(file.type);
      const isImage = ALLOWED_IMAGE.includes(file.type);

      if (!isVideo && !isImage) {
        alert(`${file.name}: Niedozwolony format`);
        return false;
      }

      const maxSize = isVideo ? MAX_VIDEO_SIZE : MAX_IMAGE_SIZE;
      if (file.size > maxSize) {
        const maxMB = maxSize / (1024 * 1024);
        alert(`${file.name}: Plik za duży (max ${maxMB}MB)`);
        return false;
      }

      return true;
    });

    const filesWithPreviews = validFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      type: ALLOWED_VIDEO.includes(file.type) ? "video" : "image",
      status: "pending",
      progress: 0,
    }));

    setSelectedFiles((prev) => [...prev, ...filesWithPreviews]);
  };

  const handleFileSelect = (e) => {
    validateAndAddFiles(e.target.files);
  };

  // TK-373: onDragOver, onDrop handlers
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
    const newFiles = [...selectedFiles];
    URL.revokeObjectURL(newFiles[index].preview);
    newFiles.splice(index, 1);
    setSelectedFiles(newFiles);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    const results = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const fileObj = selectedFiles[i];

      try {
        const formData = new FormData();
        formData.append("file", fileObj.file);

        // TK-377: Progress tracking
        const response = await api.post("/files/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setSelectedFiles((prev) =>
              prev.map((f, idx) =>
                idx === i ? { ...f, progress: percentCompleted } : f
              )
            );
          },
        });

        if (response.data.success) {
          toast.success(`${response.data.filename} uploaded!`);
        } else {
          toast.error(`${response.data.filename} failed: ${response.data.message}`);
        }

        results.push({
          filename: fileObj.file.name,
          success: true,
          message: "Uploaded successfully",
          data: response.data,
        });

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: "success", progress: 100 } : f
          )
        );
      } catch (error) {
        results.push({
          filename: fileObj.file.name,
          success: false,
          message: error.response?.data?.message || "Upload failed",
        });

        setSelectedFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: "error", error: error.response?.data?.message }
              : f
          )
        );
      }
    }

    setUploadResults(results);
    setUploading(false);

    const allSuccess = results.every((r) => r.success);
    if (allSuccess) {
      setTimeout(() => navigate("/dashboard"), 2000);
    }
  };

  // TK-380: Cancel upload
  const cancelUpload = (index) => {
    // Simple implementation - just remove from list
    removeFile(index);
  };

  const formatFileSize = (bytes) => {
    const mb = bytes / (1024 * 1024);
    return mb < 1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Upload Plików</h1>

      {/* TK-372: Drag & Drop Area */}
      <div className="mb-6">
        <label className="block mb-2 text-gray-300">
          Wybierz pliki lub przeciągnij tutaj
        </label>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
            dragActive
              ? "border-blue-500 bg-blue-500/10"
              : "border-gray-600 hover:border-blue-500"
          }`}
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
          <label htmlFor="file-input" className="cursor-pointer">
            <Upload size={48} className="mx-auto mb-4 text-gray-400" />
            <p className="text-gray-400 mb-2">
              {dragActive
                ? "Upuść pliki tutaj"
                : "Kliknij lub przeciągnij pliki"}
            </p>
            <p className="text-sm text-gray-500">
              Video: MP4, WebM, MOV (max 500MB) | Obrazy: PNG, JPG (max 10MB)
            </p>
          </label>
        </div>
      </div>

      {/* Selected Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">
            Wybrane pliki ({selectedFiles.length})
          </h2>
          <div className="space-y-3">
            {selectedFiles.map((fileObj, index) => (
              <div
                key={index}
                className="bg-gray-800 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex items-center gap-4 mb-2">
                  {/* Preview */}
                  <div className="w-24 h-24 bg-gray-900 rounded flex-shrink-0 overflow-hidden">
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
                        <FileVideo size={16} />
                      ) : (
                        <ImageIcon size={16} />
                      )}
                      <span className="font-medium truncate">
                        {fileObj.file.name}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">
                      {formatFileSize(fileObj.file.size)} • {fileObj.type}
                    </p>

                    {/* Status */}
                    {fileObj.status === "success" && (
                      <div className="flex items-center gap-1 text-green-500 text-sm mt-1">
                        <CheckCircle size={14} />
                        <span>Uploaded</span>
                      </div>
                    )}
                    {fileObj.status === "error" && (
                      <div className="text-red-400 text-sm mt-1">
                        Error: {fileObj.error}
                      </div>
                    )}
                    {uploading && fileObj.status === "pending" && (
                      <div className="flex items-center gap-2 text-blue-400 text-sm mt-1">
                        <Loader size={14} className="animate-spin" />
                        <span>Uploading... {fileObj.progress}%</span>
                      </div>
                    )}
                  </div>

                  {/* Remove/Cancel button */}
                  {!uploading && (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 hover:bg-gray-700 rounded transition text-gray-400 hover:text-red-400"
                    >
                      <X size={20} />
                    </button>
                  )}
                  {uploading && fileObj.status === "pending" && (
                    <button
                      onClick={() => cancelUpload(index)}
                      className="p-2 hover:bg-gray-700 rounded transition text-gray-400 hover:text-red-400"
                      title="Cancel"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>

                {/* TK-377: Progress bar */}
                {uploading && fileObj.status === "pending" && (
                  <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full transition-all duration-300"
                      style={{ width: `${fileObj.progress}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Button */}
      {selectedFiles.length > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <Loader className="animate-spin" size={20} />
              Uploading...
            </>
          ) : (
            <>
              <Upload size={20} />
              Upload {selectedFiles.length}{" "}
              {selectedFiles.length === 1 ? "plik" : "plików"}
            </>
          )}
        </button>
      )}

      {/* Results */}
      {uploadResults.length > 0 && !uploading && (
        <div className="mt-6 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="font-semibold mb-3">Wyniki uploadu:</h3>
          <div className="space-y-2">
            {uploadResults.map((result, idx) => (
              <div
                key={idx}
                className={`text-sm p-2 rounded ${
                  result.success
                    ? "bg-green-900/50 text-green-200"
                    : "bg-red-900/50 text-red-200"
                }`}
              >
                <strong>{result.filename}:</strong> {result.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadPage;
