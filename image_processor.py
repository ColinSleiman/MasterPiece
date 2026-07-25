from pathlib import Path
import subprocess
import tempfile

import cairosvg
import cv2
import numpy as np
from PIL import Image


def process_image(
    uploaded_file,
    threshold_value: int
) -> dict[str, bytes | str]:
    """
    Convert an uploaded raster image into SVG and vector PDF files.
    """

    file_bytes = np.asarray(
        bytearray(uploaded_file.getvalue()),
        dtype=np.uint8
    )

    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError(
            f"Unable to read image: {uploaded_file.name}"
        )

    _, bw = cv2.threshold(
        img,
        threshold_value,
        255,
        cv2.THRESH_BINARY
    )

    bw = 255 - bw

    original_name = Path(uploaded_file.name).stem

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)

        pbm_file = temp_path / f"{original_name}.pbm"
        svg_file = temp_path / f"{original_name}.svg"
        pdf_file = temp_path / f"{original_name}_vector.pdf"

        Image.fromarray(bw).save(pbm_file)

        subprocess.run(
            [
                "potrace",
                str(pbm_file),
                "-s",
                "-o",
                str(svg_file)
            ],
            check=True,
            capture_output=True,
            text=True
        )

        cairosvg.svg2pdf(
            url=str(svg_file),
            write_to=str(pdf_file)
        )

        return {
            "svg_filename": f"{original_name}.svg",
            "svg_data": svg_file.read_bytes(),
            "pdf_filename": f"{original_name}_vector.pdf",
            "pdf_data": pdf_file.read_bytes()
        }