/**
 * Kompresja obrazów po stronie klienta PRZED uploadem
 * Zmniejsza rozmiar pliku o 60-80% bez widocznej utraty jakości
 */

export const compressImage = async (
  file,
  maxWidth = 1920,
  quality = 0.85,
  outputType = null
) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();

      img.onload = () => {
        const canvas = document.createElement("canvas");

        // Oblicz nowe wymiary (zachowaj aspect ratio)
        let width = img.width;
        let height = img.height;

        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);

        // Wybierz typ wyjściowy: zadany albo oryginalny, jeśli to obraz, inaczej jpeg
        const desiredType =
          outputType ||
          (file.type?.startsWith("image/") ? file.type : "image/jpeg");
        // dla PNG/GIF parametr quality jest ignorowany przez większość przeglądarek
        const qualityParam =
          desiredType === "image/png" || desiredType === "image/gif"
            ? undefined
            : quality;

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error("Canvas toBlob failed"));
              return;
            }

            const compressedFile = new File([blob], file.name, {
              type: blob.type || desiredType,
              lastModified: Date.now(),
            });

            console.log(
              `Compressed (${desiredType}): ${(file.size / 1024).toFixed(
                0
              )}KB → ${(blob.size / 1024).toFixed(0)}KB`
            );
            resolve(compressedFile);
          },
          desiredType,
          qualityParam
        );
      };

      img.onerror = reject;
      img.src = e.target.result;
    };

    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
