"""Raster-to-vector processing for Image Vectorizer."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile
from typing import BinaryIO, Protocol, TypedDict

import cairosvg
import cv2
import numpy as np
from PIL import Image


class UploadedFileLike(Protocol):
    """Minimal interface accepted from Streamlit or file-like upload objects."""

    name: str

    def read(self, size: int = -1) -> bytes: ...


class VectorizedImage(TypedDict):
    """Generated files returned to the presentation layer."""

    original_filename: str
    svg_filename: str
    svg_bytes: bytes
    pdf_filename: str
    pdf_bytes: bytes


def _uploaded_filename(uploaded_file: UploadedFileLike | BinaryIO) -> str:
    """Return a basename without trusting any client-supplied directory path."""
    supplied_name = str(getattr(uploaded_file, "name", "uploaded_image"))
    basename = supplied_name.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    return basename or "uploaded_image"


def _read_uploaded_bytes(uploaded_file: UploadedFileLike | BinaryIO) -> bytes:
    """Read upload content without depending on Streamlit internals."""
    getvalue = getattr(uploaded_file, "getvalue", None)
    if callable(getvalue):
        data = getvalue()
    else:
        seek = getattr(uploaded_file, "seek", None)
        tell = getattr(uploaded_file, "tell", None)
        original_position = tell() if callable(tell) else None

        if callable(seek):
            seek(0)
        data = uploaded_file.read()
        if callable(seek) and original_position is not None:
            seek(original_position)

    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("The uploaded file did not provide binary image data.")
    if not data:
        raise ValueError("The uploaded image is empty.")

    return bytes(data)


def _safe_output_stem(filename: str) -> str:
    """Create a portable output stem while keeping the original name in results."""
    stem = Path(filename).stem
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    safe_stem = (safe_stem or "vectorized_image")[:96]
    windows_reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
    if safe_stem.upper() in windows_reserved_names:
        safe_stem = f"_{safe_stem}"
    return safe_stem


def process_image(
    uploaded_file: UploadedFileLike | BinaryIO,
    threshold_value: int,
) -> VectorizedImage:
    """Convert one uploaded raster image into SVG and vector PDF bytes."""
    if not 0 <= threshold_value <= 255:
        raise ValueError("Threshold value must be between 0 and 255.")

    original_filename = _uploaded_filename(uploaded_file)
    file_bytes = np.frombuffer(_read_uploaded_bytes(uploaded_file), dtype=np.uint8)
    decoded_image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

    if decoded_image is None:
        raise ValueError(f"Unable to decode image: {original_filename}")

    if decoded_image.ndim == 3 and decoded_image.shape[2] == 4:
        # OpenCV's grayscale decoder discards alpha. Transparent black pixels
        # would otherwise become a black background and trace as an empty page.
        foreground_gray = cv2.cvtColor(decoded_image, cv2.COLOR_BGRA2GRAY)
        channel_max = np.iinfo(decoded_image.dtype).max
        alpha = decoded_image[:, :, 3].astype(np.float32) / channel_max
        grayscale_image = np.rint(
            (foreground_gray.astype(np.float32) / channel_max * alpha
             + (1 - alpha)) * 255
        ).astype(np.uint8)
    else:
        grayscale_image = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)

    _, binary_image = cv2.threshold(
        grayscale_image,
        threshold_value,
        255,
        cv2.THRESH_BINARY,
    )
    if not np.any(binary_image):
        raise ValueError(
            "The selected threshold leaves no traceable detail. "
            "Try a lower threshold or an image with more contrast."
        )
    inverted_image = 255 - binary_image
    output_stem = _safe_output_stem(original_filename)
    svg_filename = f"{output_stem}.svg"
    pdf_filename = f"{output_stem}_vector.pdf"

    with tempfile.TemporaryDirectory(prefix="image-vectorizer-") as temp_directory:
        temp_path = Path(temp_directory)
        pbm_path = temp_path / f"{output_stem}.pbm"
        svg_path = temp_path / svg_filename
        pdf_path = temp_path / pdf_filename

        Image.fromarray(inverted_image).convert(
            "1",
            dither=Image.Dither.NONE,
        ).save(pbm_path)

        try:
            completed_process = subprocess.run(
                ["potrace", str(pbm_path), "-s", "-o", str(svg_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "Potrace is not installed or is not available on PATH."
            ) from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"Potrace timed out while processing {original_filename}."
            ) from error
        except subprocess.CalledProcessError as error:
            details = (
                error.stderr or error.stdout or "No error details returned."
            ).strip()
            raise RuntimeError(
                f"Potrace failed for {original_filename}: {details}"
            ) from error

        if not svg_path.is_file():
            details = (
                completed_process.stderr.strip() or "SVG output was not created."
            )
            raise RuntimeError(f"Potrace failed for {original_filename}: {details}")

        try:
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
        except Exception as error:
            raise RuntimeError(
                f"PDF conversion failed for {original_filename}: {error}"
            ) from error

        return {
            "original_filename": original_filename,
            "svg_filename": svg_filename,
            "svg_bytes": svg_path.read_bytes(),
            "pdf_filename": pdf_filename,
            "pdf_bytes": pdf_path.read_bytes(),
        }
