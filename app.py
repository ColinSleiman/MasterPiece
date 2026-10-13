"""Streamlit presentation layer for Image Vectorizer."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

from image_processor import VectorizedImage, process_image


SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "bmp", "webp"]
ASSETS_PATH = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS_PATH / "img" / "logo.png"
APP_CSS = (ASSETS_PATH / "css" / "app.css").read_text(encoding="utf-8")
IMAGE_VIEWER_CSS = (ASSETS_PATH / "css" / "image_viewer.css").read_text(
    encoding="utf-8"
)
LOGO_DATA_URI = (
    "data:image/png;base64,"
    + base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
)

st.set_page_config(
    page_title="Masterpiece Image Vectorizer",
    page_icon=str(LOGO_PATH),
    layout="wide",
)

IMAGE_VIEWER_HTML = """
<figure class="viewer">
    <button class="viewer__trigger" type="button" aria-haspopup="dialog">
        <img class="viewer__preview" alt="">
        <span class="viewer__overlay">View</span>
    </button>
    <figcaption class="viewer__caption"></figcaption>
</figure>
<dialog class="viewer__dialog">
    <button class="viewer__close" type="button">Close</button>
    <img class="viewer__full-image" alt="">
</dialog>
"""

IMAGE_VIEWER_JS = """
export default function (component) {
    const { data, parentElement } = component
    const preview = parentElement.querySelector(".viewer__preview")
    const fullImage = parentElement.querySelector(".viewer__full-image")
    const caption = parentElement.querySelector(".viewer__caption")
    const trigger = parentElement.querySelector(".viewer__trigger")
    const dialog = parentElement.querySelector(".viewer__dialog")
    const closeButton = parentElement.querySelector(".viewer__close")
    if (!preview || !fullImage || !caption || !trigger || !dialog || !closeButton) return

    const source = `data:${data.mimeType};base64,${data.encodedImage}`
    preview.src = source
    preview.alt = data.filename
    fullImage.src = source
    fullImage.alt = data.filename
    caption.textContent = data.filename
    caption.title = data.filename
    caption.hidden = !data.showCaption
    preview.style.height = `${data.previewHeight}px`
    trigger.setAttribute("aria-label", `View ${data.filename} at full size`)

    trigger.onclick = () => dialog.showModal()
    closeButton.onclick = () => dialog.close()
    dialog.onclick = (event) => {
        if (event.target === dialog) dialog.close()
    }
}
"""

IMAGE_VIEWER = st.components.v2.component(
    "image_vectorizer_viewer",
    html=IMAGE_VIEWER_HTML,
    css=IMAGE_VIEWER_CSS,
    js=IMAGE_VIEWER_JS,
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
    st.session_state.setdefault("uploader_key", 0)

def clear_results() -> None:
    """Remove generated results and their associated errors."""
    st.session_state.processed_files = []
    st.session_state.processing_errors = []

def clear_selection() -> None:
    """Reset the uploader and remove results created from its previous files."""
    clear_results()
    st.session_state.uploader_key += 1

def render_viewable_image(
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    viewer_key: str,
    show_caption: bool = True,
    preview_height: int = 180,
) -> None:
    """Render an image with a hover overlay and an in-page full-size viewer."""
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    IMAGE_VIEWER(
        data={
            "encodedImage": encoded_image,
            "filename": filename,
            "mimeType": mime_type,
            "showCaption": show_caption,
            "previewHeight": preview_height,
        },
        key=viewer_key,
        width="stretch",
        height=preview_height + 30 if show_caption else preview_height,
    )

def render_previews(uploaded_files: list) -> None:
    """Render compact previews in a five-column grid."""
    st.subheader("Image previews")
    preview_columns = st.columns(5)
    for index, uploaded_file in enumerate(uploaded_files):
        with preview_columns[index % 5]:
            mime_type = uploaded_file.type or "image/png"
            render_viewable_image(
                uploaded_file.getvalue(),
                uploaded_file.name,
                mime_type,
                f"upload-viewer-{st.session_state.uploader_key}-{index}",
                preview_height=140,
            )

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

def render_processing_feedback() -> None:
    """Render persistent processing feedback beside the primary action."""
    processed_files: list[VectorizedImage] = st.session_state.processed_files
    processing_errors: list[str] = st.session_state.processing_errors

    if processed_files:
        st.caption(
            ":green[:material/check_circle: "
            f"Successfully processed {len(processed_files)} image(s).]"
        )

    if processing_errors:
        for message in processing_errors:
            st.caption(f":red[:material/error: Failed to process {message}]")

def render_results() -> None:
    """Render persistent download controls."""
    processed_files: list[VectorizedImage] = st.session_state.processed_files

    if not processed_files:
        return

    st.header("Download results")

    view_column, spacer_column, zip_column, clear_column = st.columns(
        [1.35, 2.85, 1.6, 1.1],
        vertical_alignment="center",
    )
    with view_column:
        results_view = st.segmented_control(
            "Results view",
            options=["Grid", "List"],
            default="Grid",
            key="results-view",
            required=True,
            label_visibility="collapsed",
            width="stretch",
        )
    with zip_column:
        st.download_button(
            "Download all as ZIP",
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
            "Clear results",
            key="clear-results",
            on_click=clear_results,
            icon=":material/delete_sweep:",
            width="stretch",
        )

    def render_result(result: VectorizedImage, index: int, compact: bool) -> None:
        with st.container(border=True, key=f"result-card-{index}"):
            if compact:
                render_viewable_image(
                    result["svg_bytes"],
                    result["original_filename"],
                    "image/svg+xml",
                    f"result-viewer-{index}",
                    show_caption=False,
                )
                st.markdown(f"**{result['original_filename']}**")
                st.caption(
                    f"{result['svg_filename']}  \n{result['pdf_filename']}"
                )
                svg_column, pdf_column = st.columns(2)
                with svg_column:
                    st.download_button(
                        "SVG",
                        data=result["svg_bytes"],
                        file_name=result["svg_filename"],
                        mime="image/svg+xml",
                        key=f"download-svg-grid-{index}",
                        on_click="ignore",
                        icon=":material/download:",
                        width="stretch",
                    )
                with pdf_column:
                    st.download_button(
                        "PDF",
                        data=result["pdf_bytes"],
                        file_name=result["pdf_filename"],
                        mime="application/pdf",
                        key=f"download-pdf-grid-{index}",
                        on_click="ignore",
                        icon=":material/download:",
                        width="stretch",
                    )
                st.download_button(
                    "SVG + PDF (ZIP)",
                    data=create_zip([result]),
                    file_name=f"{Path(result['svg_filename']).stem}.zip",
                    mime="application/zip",
                    key=f"download-zip-grid-{index}",
                    on_click="ignore",
                    icon=":material/folder_zip:",
                    width="stretch",
                )
                return

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
                    key=f"download-svg-list-{index}",
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
                    key=f"download-pdf-list-{index}",
                    on_click="ignore",
                    icon=":material/download:",
                    width="stretch",
                )

    if results_view == "Grid":
        result_columns = st.columns(3)
        for index, result in enumerate(processed_files):
            with result_columns[index % 3]:
                render_result(result, index, compact=True)
    else:
        for index, result in enumerate(processed_files):
            render_result(result, index, compact=False)

initialize_state()

st.html(f"<style>{APP_CSS}</style>")

st.title(f"![MasterPiece logo]({LOGO_DATA_URI}) MasterPiece - Image Vectorizer Tool")
st.caption(
    "Convert PNG, JPEG, BMP, or WebP images into scalable SVG and vector PDF files."
)

with st.container(border=False, key="upload-section"):
    st.subheader("Upload images")
    uploaded_files = st.file_uploader(
        "Upload images",
        type=SUPPORTED_IMAGE_TYPES,
        accept_multiple_files=True,
        help="Select one or more PNG, JPG, JPEG, BMP, or WebP files.",
        key=f"image-uploader-{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )
    with st.container(horizontal_alignment="left"):
        st.button(
            "Clear",
            key="clear-selection",
            on_click=clear_selection,
            disabled=not uploaded_files,
            icon=":material/close:",
            width="content",
        )

threshold_value = st.slider(
    "Threshold value (180 recommended)",
    min_value=0,
    max_value=255,
    value=180,
    step=1,
    help=(
        "180 is recommended for most images. Higher values include more light "
        "pixels in the traced foreground."
    ),
)

if uploaded_files:
    render_previews(uploaded_files)

process_column, feedback_column = st.columns(
    [1.4, 4.6],
    vertical_alignment="top",
)
with process_column:
    process_requested = st.button(
        "Process images",
        type="primary",
        disabled=not uploaded_files,
        key="process-images",
        icon=":material/conversion_path:",
        width="stretch",
    )

    if process_requested:
        process_uploads(uploaded_files, threshold_value)
    render_processing_feedback()

render_results()
