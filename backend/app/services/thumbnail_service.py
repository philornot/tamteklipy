"""
Service do generowania thumbnails dla video i obrazów używając FFmpeg
Z obsługą WebP i fallback do JPEG
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from app.core.exceptions import FileUploadError

logger = logging.getLogger(__name__)


def generate_thumbnail(
        video_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
        width: int = 320,
        quality: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Generuje thumbnail z video używając FFmpeg
    Tworzy WebP jako primary i JPEG jako fallback

    Args:
        video_path: Ścieżka do pliku video
        output_path: Ścieżka gdzie zapisać thumbnail (bez rozszerzenia lub z .jpg)
        timestamp: Timestamp w formacie HH:MM:SS, z którego wziąć klatkę
        width: Szerokość thumbnail (wysokość auto)
        quality: Jakość JPEG (1-31, niższe = lepsza jakość, domyślnie 5)

    Returns:
        Tuple[bool, Optional[str]]: (success, webp_path)

    Raises:
        FileUploadError: Jeśli FFmpeg nie jest zainstalowany lub wystąpił błąd
    """
    try:
        # Sprawdź, czy FFmpeg jest zainstalowany
        check_ffmpeg = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )

        if check_ffmpeg.returncode != 0:
            raise FileUploadError(
                message="FFmpeg nie jest zainstalowany",
                reason="FFmpeg is required for thumbnail generation"
            )

        # Przygotuj ścieżki
        base_path = Path(output_path)
        if base_path.suffix:
            base_path = base_path.with_suffix('')

        jpeg_path = f"{base_path}.jpg"
        webp_path = f"{base_path}.webp"

        # 1. Generuj JPEG fallback (jakość 5 zamiast 2)
        cmd_jpeg = [
            "ffmpeg",
            "-ss", timestamp,
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            "-q:v", str(quality),
            "-y",
            jpeg_path
        ]

        logger.info(f"Generating JPEG thumbnail: {video_path} -> {jpeg_path}")

        result = subprocess.run(
            cmd_jpeg,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg JPEG error: {result.stderr}")
            raise FileUploadError(
                message="Błąd podczas generowania JPEG thumbnail",
                reason=result.stderr[:200]
            )

        if not Path(jpeg_path).exists():
            raise FileUploadError(
                message="JPEG thumbnail nie został utworzony",
                reason="Output file does not exist"
            )

        # 2. Generuj WebP (quality 75 dla WebP)
        cmd_webp = [
            "ffmpeg",
            "-ss", timestamp,
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:-1",
            "-c:v", "libwebp",
            "-quality", "75",
            "-y",
            webp_path
        ]

        logger.info(f"Generating WebP thumbnail: {video_path} -> {webp_path}")

        result = subprocess.run(
            cmd_webp,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.warning(f"FFmpeg WebP warning: {result.stderr}")
            # WebP failed, but we have JPEG fallback
            logger.info(f"WebP generation failed, using JPEG fallback")
            return True, None

        if not Path(webp_path).exists():
            logger.warning("WebP thumbnail not created, using JPEG fallback")
            return True, None

        logger.info(f"Thumbnails generated successfully: JPEG + WebP")
        return True, webp_path

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout")
        raise FileUploadError(
            message="Timeout podczas generowania thumbnail",
            reason="FFmpeg process timed out after 30 seconds"
        )
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        raise FileUploadError(
            message="FFmpeg nie jest zainstalowany",
            reason="FFmpeg executable not found in PATH"
        )
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        raise FileUploadError(
            message="Błąd podczas generowania thumbnail",
            reason=str(e)
        )


def generate_image_thumbnail(
        image_path: str,
        output_path: str,
        width: int = 320,
        quality: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Generuje thumbnail z obrazu używając FFmpeg
    Tworzy WebP jako primary i JPEG jako fallback

    Args:
        image_path: Ścieżka do pliku obrazu
        output_path: Ścieżka gdzie zapisać thumbnail (bez rozszerzenia lub z .jpg)
        width: Szerokość thumbnail (wysokość zostanie obliczona proporcjonalnie)
        quality: Jakość JPEG (1-31, niższe = lepsza jakość, domyślnie 5)

    Returns:
        Tuple[bool, Optional[str]]: (success, webp_path)

    Raises:
        FileUploadError: Jeśli FFmpeg nie jest zainstalowany lub wystąpił błąd
    """
    try:
        # Sprawdź, czy FFmpeg jest zainstalowany
        check_ffmpeg = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )

        if check_ffmpeg.returncode != 0:
            raise FileUploadError(
                message="FFmpeg nie jest zainstalowany",
                reason="FFmpeg is required for thumbnail generation"
            )

        # Przygotuj ścieżki
        base_path = Path(output_path)
        if base_path.suffix:
            base_path = base_path.with_suffix('')

        jpeg_path = f"{base_path}.jpg"
        webp_path = f"{base_path}.webp"

        # 1. Generuj JPEG fallback (jakość 5 zamiast 2)
        cmd_jpeg = [
            "ffmpeg",
            "-i", str(image_path),
            "-vf", f"scale={width}:-1",
            "-q:v", str(quality),
            "-y",
            jpeg_path
        ]

        logger.info(f"Generating JPEG image thumbnail: {image_path} -> {jpeg_path}")

        result = subprocess.run(
            cmd_jpeg,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg JPEG error: {result.stderr}")
            raise FileUploadError(
                message="Błąd podczas generowania JPEG thumbnail dla obrazu",
                reason=result.stderr[:200]
            )

        if not Path(jpeg_path).exists():
            raise FileUploadError(
                message="JPEG thumbnail nie został utworzony",
                reason="Output file does not exist"
            )

        # 2. Generuj WebP
        cmd_webp = [
            "ffmpeg",
            "-i", str(image_path),
            "-vf", f"scale={width}:-1",
            "-c:v", "libwebp",
            "-quality", "75",
            "-y",
            webp_path
        ]

        logger.info(f"Generating WebP image thumbnail: {image_path} -> {webp_path}")

        result = subprocess.run(
            cmd_webp,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            logger.warning(f"FFmpeg WebP warning: {result.stderr}")
            logger.info(f"WebP generation failed, using JPEG fallback")
            return True, None

        if not Path(webp_path).exists():
            logger.warning("WebP thumbnail not created, using JPEG fallback")
            return True, None

        logger.info(f"Image thumbnails generated successfully: JPEG + WebP")
        return True, webp_path

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout for image")
        raise FileUploadError(
            message="Timeout podczas generowania thumbnail dla obrazu",
            reason="FFmpeg process timed out after 15 seconds"
        )
    except FileNotFoundError:
        logger.error("FFmpeg not found")
        raise FileUploadError(
            message="FFmpeg nie jest zainstalowany",
            reason="FFmpeg executable not found in PATH"
        )
    except Exception as e:
        logger.error(f"Image thumbnail generation failed: {e}")
        raise FileUploadError(
            message="Błąd podczas generowania thumbnail dla obrazu",
            reason=str(e)
        )


def extract_video_metadata(video_path: str) -> Optional[dict]:
    """
    Wyciąga metadane z video (duration, width, height) używając FFprobe

    Args:
        video_path: Ścieżka do pliku video

    Returns:
        dict: Metadane video lub None jeśli błąd
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.error(f"FFprobe error: {result.stderr}")
            return None

        import json
        data = json.loads(result.stdout)

        # Wyciągnij dane
        stream = data.get("streams", [{}])[0]
        format_data = data.get("format", {})

        width = stream.get("width")
        height = stream.get("height")
        duration = stream.get("duration") or format_data.get("duration")

        if duration:
            duration = int(float(duration))

        return {
            "width": width,
            "height": height,
            "duration": duration
        }

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return None


def extract_image_metadata(image_path: str) -> Optional[dict]:
    """
    Wyciąga metadane z obrazu (width, height) używając FFprobe

    Args:
        image_path: Ścieżka do pliku obrazu

    Returns:
        dict: Metadane obrazu lub None, jeśli błąd
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(image_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            logger.error(f"FFprobe error for image: {result.stderr}")
            return None

        import json
        data = json.loads(result.stdout)

        stream = data.get("streams", [{}])[0]
        width = stream.get("width")
        height = stream.get("height")

        return {
            "width": width,
            "height": height,
            "duration": None  # Obrazy nie mają duration
        }

    except Exception as e:
        logger.error(f"Image metadata extraction failed: {e}")
        return None
