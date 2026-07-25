"""Streamlit presentation layer for Image Vectorizer."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

from image_processor import VectorizedImage, process_image


SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "bmp", "webp"]

st.set_page_config(
    page_title="Image Vectorizer",
    page_icon=":material/polyline:",
    layout="wide",
)


def create_zip(processed_files: list[VectorizedImage]) -> bytes:
    """Build an in-memory archive containing every successful result."""
    zip_buffer = BytesIO()
    used_names: set[str] = set()

    def unique_archive_name(filename: str) -> str:
        path = Path(filename)
        candidate = filename
        counter = 2
        while candidate.casefold() in used_names:
            candidate = f"{path.stem}_{counter}{path.suffix}"
            counter += 1
        used_names.add(candidate.casefold())
        return candidate

    with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        for result in processed_files:
            zip_file.writestr(
                unique_archive_name(result["svg_filename"]),
                result["svg_bytes"],
            )
            zip_file.writestr(
                unique_archive_name(result["pdf_filename"]),
                result["pdf_bytes"],
            )
    return zip_buffer.getvalue()


def initialize_state() -> None:
    """Initialize persistent values used across Streamlit reruns."""
    st.session_state.setdefault("processed_files", [])
    st.session_state.setdefault("processing_errors", [])


def clear_results() -> None:
    """Remove generated results and their associated errors."""
    st.session_state.processed_files = []
    st.session_state.processing_errors = []


def render_previews(uploaded_files: list) -> None:
    """Render compact previews in a four-column grid."""
    st.subheader("Image previews")
    preview_columns = st.columns(4)
    for index, uploaded_file in enumerate(uploaded_files):
        with preview_columns[index % 4]:
            st.image(uploaded_file, caption=uploaded_file.name, width=210)


def process_uploads(uploaded_files: list, threshold_value: int) -> None:
    """Process every upload independently and retain successes and errors."""
    processed_files: list[VectorizedImage] = []
    processing_errors: list[str] = []
    progress_bar = st.progress(0)
    status_message = st.empty()

    for index, uploaded_file in enumerate(uploaded_files):
        status_message.write(f"Processing `{uploaded_file.name}`...")
        try:
            processed_files.append(process_image(uploaded_file, threshold_value))
        except Exception as error:
            processing_errors.append(f"{uploaded_file.name}: {error}")

        progress_bar.progress((index + 1) / len(uploaded_files))

    status_message.empty()
    progress_bar.empty()
    st.session_state.processed_files = processed_files
    st.session_state.processing_errors = processing_errors


def render_results() -> None:
    """Render persistent processing messages and download controls."""
    processed_files: list[VectorizedImage] = st.session_state.processed_files
    processing_errors: list[str] = st.session_state.processing_errors

    if processing_errors:
        for message in processing_errors:
            st.error(f"Failed to process {message}")

    if not processed_files:
        return

    st.success(f"Successfully processed {len(processed_files)} image(s).")

    results_heading, zip_column, clear_column = st.columns(
        [3.5, 1.5, 1.2],
        vertical_alignment="center",
    )
    with results_heading:
        st.header("Download results")
    with zip_column:
        st.download_button(
            "Download All as ZIP",
            data=create_zip(processed_files),
            file_name="vectorized_images.zip",
            mime="application/zip",
            key="download-all-zip",
            on_click="ignore",
            type="primary",
            icon=":material/folder_zip:",
            width="stretch",
        )
    with clear_column:
        st.button(
            "Clear Results",
            key="clear-results",
            on_click=clear_results,
            icon=":material/delete_sweep:",
            width="stretch",
        )

    for index, result in enumerate(processed_files):
        with st.container(border=True):
            information_column, svg_column, pdf_column = st.columns(
                [4, 1.25, 1.25],
                vertical_alignment="center",
            )
            with information_column:
                st.markdown(f"#### {result['original_filename']}")
                st.caption(
                    f"SVG: {result['svg_filename']}  \n"
                    f"PDF: {result['pdf_filename']}"
                )
            with svg_column:
                st.download_button(
                    "Download SVG",
                    data=result["svg_bytes"],
                    file_name=result["svg_filename"],
                    mime="image/svg+xml",
                    key=f"download-svg-{index}",
                    on_click="ignore",
                    icon=":material/download:",
                    width="stretch",
                )
            with pdf_column:
                st.download_button(
                    "Download PDF",
                    data=result["pdf_bytes"],
                    file_name=result["pdf_filename"],
                    mime="application/pdf",
                    key=f"download-pdf-{index}",
                    on_click="ignore",
                    icon=":material/download:",
                    width="stretch",
                )


initialize_state()

st.html(
    """
    <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
        }
        [data-testid="stImage"] img {
            border-radius: 0.6rem;
            object-fit: contain;
        }
        [data-testid="stFileUploader"] {
            max-width: 760px;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            min-height: 2.6rem;
            border-radius: 0.5rem;
        }
    </style>
    """
)

st.title("Image Vectorizer")
st.caption(
    "Convert PNG, JPEG, BMP, or WebP images into scalable SVG and vector PDF files."
)

uploaded_files = st.file_uploader(
    "Upload images",
    type=SUPPORTED_IMAGE_TYPES,
    accept_multiple_files=True,
    help="Select one or more PNG, JPG, JPEG, BMP, or WebP files.",
)
threshold_value = st.slider(
    "Threshold value",
    min_value=0,
    max_value=255,
    value=180,
    step=1,
    help="Higher values include more light pixels in the traced foreground.",
)

if uploaded_files:
    render_previews(uploaded_files)

if st.button(
    "Process Images",
    type="primary",
    disabled=not uploaded_files,
    key="process-images",
    icon=":material/conversion_path:",
):
    process_uploads(uploaded_files, threshold_value)

render_results()
