/**
 * Resize obrazka w przeglądarce używając Canvas API
 * @param {File} file - Plik obrazka
 * @param {number} maxSize - Max wymiar (width/height)
 * @returns {Promise<File>} - Zresizowany plik
 */
export const resizeImage = (file, maxSize = 128) => {
    return new Promise((resolve, reject) => {
        // Walidacja formatu
        if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
            reject(new Error('Tylko PNG i JPG są dozwolone'))
            return
        }

        // Walidacja rozmiaru przed resize (max 100MB)
        if (file.size > 100 * 1024 * 1024) {
            reject(new Error('Plik za duży (max 100MB)'))
            return
        }

        const reader = new FileReader()

        reader.onerror = () => reject(new Error('Nie można odczytać pliku'))

        reader.onload = (e) => {
            const img = new Image()

            img.onerror = () => reject(new Error('Nieprawidłowy obrazek'))

            img.onload = () => {
                // Canvas do resize
                const canvas = document.createElement('canvas')
                canvas.width = maxSize
                canvas.height = maxSize

                const ctx = canvas.getContext('2d')

                // Calculate crop (center)
                const size = Math.min(img.width, img.height)
                const x = (img.width - size) / 2
                const y = (img.height - size) / 2

                // Draw centered & cropped
                ctx.drawImage(
                    img,
                    x, y, size, size,  // Source
                    0, 0, maxSize, maxSize  // Destination
                )

                // Convert to Blob
                canvas.toBlob(
                    (blob) => {
                        if (!blob) {
                            reject(new Error('Nie można przetworzyć obrazka'))
                            return
                        }

                        // Create new File
                        const resizedFile = new File([blob], file.name, {
                            type: 'image/png',
                            lastModified: Date.now()
                        })

                        resolve(resizedFile)
                    },
                    'image/png',
                    0.85  // Quality
                )
            }

            img.src = e.target.result
        }

        reader.readAsDataURL(file)
    })
}