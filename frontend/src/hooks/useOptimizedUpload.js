/**
 * Wrapper hook który łączy compression + chunked upload
 */
import { useCallback } from 'react';
import useChunkedUpload from './useChunkedUpload';
import { compressImage } from '../utils/imageCompression';

const CHUNKED_THRESHOLD = 50 * 1024 * 1024; // 50MB - powyżej tego używaj chunków

export const useOptimizedUpload = () => {
  const { uploads, uploadFile: uploadChunked, cancelUpload } = useChunkedUpload();

  const uploadFile = useCallback(async (file, onProgress) => {
    let processedFile = file;

    // 1. Kompresuj obrazy
    if (file.type.startsWith('image/')) {
      console.log(`🗜️ Compressing image: ${file.name}`);

      try {
        processedFile = await compressImage(file, 1920, 0.85);
        console.log(`✅ Compressed: ${(file.size / 1024).toFixed(0)}KB → ${(processedFile.size / 1024).toFixed(0)}KB`);
      } catch (error) {
        console.warn('Compression failed, using original:', error);
        processedFile = file;
      }
    }

    // 2. Użyj chunked upload dla dużych plików
    if (processedFile.size > CHUNKED_THRESHOLD) {
      console.log(`📦 Using chunked upload (${(processedFile.size / (1024 * 1024)).toFixed(1)}MB > 50MB)`);
      return uploadChunked(processedFile, onProgress);
    }

    // 3. Standardowy upload dla małych plików
    console.log(`📤 Using standard upload (${(processedFile.size / (1024 * 1024)).toFixed(1)}MB)`);

    const formData = new FormData();
    formData.append('file', processedFile);

                try {
      const { default: api } = await import('../services/api');

      const response = await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            const progress = Math.round((e.loaded * 100) / e.total);
            onProgress?.(progress);
          }
        }
      });

      return {
        success: true,
        clipId: response.data.clip_id,
        uploadId: null
      };
    } catch (error) {
      console.error('Standard upload failed:', error);
      return {
        success: false,
        error: error.message || error.toString(),
        clipId: null,
        uploadId: null
      };
    }

  }, [uploadChunked]);

  return {
    uploads,
    uploadFile,
    cancelUpload
  };
};

export default useOptimizedUpload;
