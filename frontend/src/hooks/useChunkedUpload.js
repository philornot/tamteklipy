/**
 * useChunkedUpload — Hook do uploadu dużych plików w chunkach
 */

import { useCallback, useRef, useState } from "react";
import api from "../services/api";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_PARALLEL = 3; // maks. liczba równoległych chunków

export const useChunkedUpload = () => {
  const [uploads, setUploads] = useState({});
  const controllersRef = useRef({}); // do anulowania uploadów

  /** Generuje UUID w bezpieczny sposób */
  const uuidv4 = () => {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    throw new Error("Web Crypto API not available — cannot generate UUID");
  };

  /** Oblicza hash pliku (SHA-256) */
  const calculateFileHash = async (file) => {
    const arrayBuffer = await file.arrayBuffer();
    const cryptoImpl = globalThis.crypto;
    if (!cryptoImpl?.subtle) {
      throw new Error("Web Crypto API not available for hashing");
    }
    const hashBuffer = await cryptoImpl.subtle.digest("SHA-256", arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  /** Upload pojedynczego chunku */
  const uploadChunk = async ({
    file,
    uploadId,
    chunkNumber,
    totalChunks,
    fileHash,
    onProgress,
    controller,
  }) => {
    const start = chunkNumber * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const chunk = file.slice(start, end);

    const formData = new FormData();
    formData.append("chunk", chunk);
    formData.append("upload_id", uploadId);
    formData.append("chunk_number", chunkNumber);
    formData.append("total_chunks", totalChunks);
    formData.append("filename", file.name);

    if (chunkNumber === totalChunks - 1) {
      formData.append("file_hash", fileHash);
    }

    const response = await api.post("/files/upload-chunk", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      signal: controller.signal,
      onUploadProgress: (e) => {
        if (e.total) {
          const chunkProgress = (e.loaded / e.total) * 100;
          const overallProgress =
            ((chunkNumber + chunkProgress / 100) / totalChunks) * 100;

          setUploads((prev) => ({
            ...prev,
            [uploadId]: {
              ...prev[uploadId],
              progress: Math.round(overallProgress),
            },
          }));

          onProgress?.(Math.round(overallProgress));
        }
      },
    });

    setUploads((prev) => ({
      ...prev,
      [uploadId]: {
        ...prev[uploadId],
        chunksUploaded: prev[uploadId].chunksUploaded + 1,
      },
    }));

    return response.data;
  };

  /** Główny upload pliku w chunkach */
  const uploadFile = useCallback(async (file, onProgress) => {
    const uploadId = uuidv4();
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

    const fileHash = await calculateFileHash(file);
    const controller = new AbortController();
    controllersRef.current[uploadId] = controller;

    setUploads((prev) => ({
      ...prev,
      [uploadId]: {
        filename: file.name,
        progress: 0,
        chunksUploaded: 0,
        totalChunks,
        status: "uploading",
      },
    }));

    try {
      const uploadQueue = Array.from({ length: totalChunks }, (_, i) => i);
      const activeUploads = new Set();

      const runNext = async () => {
        if (uploadQueue.length === 0) return;
        const chunkNumber = uploadQueue.shift();
        const promise = uploadChunk({
          file,
          uploadId,
          chunkNumber,
          totalChunks,
          fileHash,
          onProgress,
          controller,
        })
          .finally(() => activeUploads.delete(promise))
          .catch((err) => {
            throw err;
          });

        activeUploads.add(promise);
        if (activeUploads.size >= MAX_PARALLEL) {
          await Promise.race(activeUploads);
        }
        await runNext();
      };

      await runNext();
      await Promise.all(activeUploads);

      const finalResponse = await api.post(`/files/complete-upload`, {
        upload_id: uploadId,
        file_hash: fileHash,
      });

      setUploads((prev) => ({
        ...prev,
        [uploadId]: {
          ...prev[uploadId],
          status: "complete",
          clipId: finalResponse.data.clip_id,
          progress: 100,
        },
      }));

      delete controllersRef.current[uploadId];

      return {
        success: true,
        clipId: finalResponse.data.clip_id,
        uploadId,
      };
    } catch (error) {
      if (error.name === "AbortError") {
        console.warn("Upload aborted:", uploadId);
      }

      setUploads((prev) => ({
        ...prev,
        [uploadId]: {
          ...prev[uploadId],
          status: "error",
          error: error.message,
        },
      }));

      throw error;
    }
  }, []);

  /** Anuluje upload (lokalnie + serwerowo) */
  const cancelUpload = useCallback(async (uploadId) => {
    const controller = controllersRef.current[uploadId];
    if (controller) {
      controller.abort();
      delete controllersRef.current[uploadId];
    }

    try {
      await api.delete(`/files/upload-chunk/${uploadId}`);
      setUploads((prev) => {
        const newUploads = { ...prev };
        delete newUploads[uploadId];
        return newUploads;
      });
    } catch (error) {
      console.error("Cancel failed:", error);
    }
  }, []);

  return {
    uploads,
    uploadFile,
    cancelUpload,
  };
}

export default useChunkedUpload;
