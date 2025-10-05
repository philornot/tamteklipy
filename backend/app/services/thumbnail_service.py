"""
Service do generowania thumbnails dla video i obrazów używając FFmpeg
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional

from app.core.exceptions import FileUploadError

logger = logging.getLogger(__name__)


def generate_thumbnail(
        video_path: str,
        output_path: str,
        timestamp: str = "00:00:01",
        width: int = 320,
        quality: int = 2
) -> bool:
    """
    Generuje thumbnail z video używając FFmpeg

    Args:
        video_path: Ścieżka do pliku video
        output_path: Ścieżka gdzie zapisać thumbnail
        timestamp: Timestamp w formacie HH:MM:SS, z którego wziąć klatkę
        width: Szerokość thumbnail (wysokość auto)
        quality: Jakość JPEG (1-31, niższe = lepsza jakość)

    Returns:
        bool: True, jeśli sukces, False, jeśli błąd

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

        # Komenda FFmpeg do generowania thumbnail
        cmd = [
            "ffmpeg",
            "-ss", timestamp,  # Seek do timestamp
            "-i", str(video_path),  # Input file
            "-vframes", "1",  # Jedna klatka
            "-vf", f"scale={width}:-1",  # Skaluj do szerokości (wysokość auto)
            "-q:v", str(quality),  # Jakość JPEG
            "-y",  # Nadpisz, jeśli istnieje
            str(output_path)  # Output file
        ]

        logger.info(f"Generating thumbnail: {video_path} -> {output_path}")

        # Uruchom FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Timeout 30 sekund
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise FileUploadError(
                message="Błąd podczas generowania thumbnail",
                reason=result.stderr[:200]  # Pierwsze 200 znaków błędu
            )

        # Sprawdź, czy plik został utworzony
        if not Path(output_path).exists():
            raise FileUploadError(
                message="Thumbnail nie został utworzony",
                reason="Output file does not exist"
            )

        logger.info(f"Thumbnail generated successfully: {output_path}")
        return True

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
        quality: int = 2
) -> bool:
    """
    Generuje thumbnail z obrazu używając FFmpeg

    FFmpeg świetnie radzi sobie z obrazami (PNG, JPG) i jest lżejszy niż PIL

    Args:
        image_path: Ścieżka do pliku obrazu
        output_path: Ścieżka gdzie zapisać thumbnail
        width: Szerokość thumbnail (wysokość zostanie obliczona proporcjonalnie)
        quality: Jakość JPEG (1-31, niższe = lepsza jakość)

    Returns:
        bool: True, jeśli sukces

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

        # Komenda FFmpeg do skalowania obrazu
        # -i: input
        # -vf scale: skaluj do szerokości (wysokość auto, zachowaj proporcje)
        # -q:v: jakość JPEG
        cmd = [
            "ffmpeg",
            "-i", str(image_path),  # Input image
            "-vf", f"scale={width}:-1",  # Skaluj do szerokości (wysokość auto)
            "-q:v", str(quality),  # Jakość JPEG
            "-y",  # Nadpisz, jeśli istnieje
            str(output_path)  # Output file
        ]

        logger.info(f"Generating image thumbnail: {image_path} -> {output_path}")

        # Uruchom FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15  # Timeout 15 sekund (obrazy są szybsze)
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise FileUploadError(
                message="Błąd podczas generowania thumbnail dla obrazu",
                reason=result.stderr[:200]
            )

        # Sprawdź, czy plik został utworzony
        if not Path(output_path).exists():
            raise FileUploadError(
                message="Thumbnail nie został utworzony",
                reason="Output file does not exist"
            )

        logger.info(f"Image thumbnail generated successfully: {output_path}")
        return True

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
