from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

from image_processor import process_image


st.set_page_config(
    page_title="Image Vectorizer",
    page_icon="🖼️",
    layout="wide"
)


# Store generated files across Streamlit reruns.
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []


def create_zip(processed_files: list[dict]) -> bytes:
    """
    Create a ZIP archive containing all generated SVG and PDF files.
    """

    zip_buffer = BytesIO()

    with ZipFile(
        zip_buffer,
        mode="w",
        compression=ZIP_DEFLATED
    ) as zip_file:
        for result in processed_files:
            zip_file.writestr(
                result["svg_filename"],
                result["svg_data"]
            )

            zip_file.writestr(
                result["pdf_filename"],
                result["pdf_data"]
            )

    return zip_buffer.getvalue()


# Small UI improvements.
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stImage"] img {
            border-radius: 10px;
            object-fit: contain;
        }

        [data-testid="stFileUploader"] {
            max-width: 750px;
        }

        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            border-radius: 8px;
            min-height: 42px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("Image Vectorizer")

st.caption(
    "Upload one or more images, select a threshold, "
    "and generate SVG and vector PDF files."
)

st.divider()


uploaded_files = st.file_uploader(
    "Upload images",
    type=["png", "jpg", "jpeg", "bmp", "webp"],
    accept_multiple_files=True,
    help="Supported formats: PNG, JPG, JPEG, BMP and WebP."
)

threshold_value = st.slider(
    "Threshold value",
    min_value=0,
    max_value=255,
    value=180,
    step=1,
    help=(
        "Lower values preserve darker areas. "
        "Higher values include more of the image."
    )
)


if uploaded_files:
    st.subheader("Image Preview")

    preview_columns = st.columns(4)

    for index, uploaded_file in enumerate(uploaded_files):
        with preview_columns[index % 4]:
            st.image(
                uploaded_file,
                caption=uploaded_file.name,
                width=220
            )


process_clicked = st.button(
    "Process Images",
    type="primary",
    disabled=not uploaded_files,
    use_container_width=False
)


if process_clicked:
    processed_files = []

    progress_bar = st.progress(0)
    status_message = st.empty()

    for index, uploaded_file in enumerate(uploaded_files):
        status_message.write(
            f"Processing `{uploaded_file.name}`..."
        )

        try:
            result = process_image(
                uploaded_file,
                threshold_value
            )

            processed_files.append(result)

        except Exception as error:
            st.error(
                f"Failed to process {uploaded_file.name}: {error}"
            )

        progress = int(
            ((index + 1) / len(uploaded_files)) * 100
        )

        progress_bar.progress(progress)

    status_message.empty()
    progress_bar.empty()

    # Save results so they remain after download clicks and reruns.
    st.session_state.processed_files = processed_files


processed_files = st.session_state.processed_files


if processed_files:
    st.divider()

    st.success(
        f"Successfully processed {len(processed_files)} image(s)."
    )

    results_header, zip_column = st.columns(
        [3, 1],
        vertical_alignment="center"
    )

    with results_header:
        st.header("Download Results")

    with zip_column:
        zip_data = create_zip(processed_files)

        st.download_button(
            label="Download All as ZIP",
            data=zip_data,
            file_name="vectorized_images.zip",
            mime="application/zip",
            key="download-all-zip",
            on_click="ignore",
            type="primary",
            use_container_width=True
        )

    for index, result in enumerate(processed_files):
        with st.container(border=True):
            information_column, svg_column, pdf_column = st.columns(
                [4, 1.2, 1.2],
                vertical_alignment="center"
            )

            with information_column:
                original_filename = result["svg_filename"].removesuffix(
                    ".svg"
                )

                st.markdown(
                    f"#### {original_filename}"
                )

                st.caption(
                    f"{result['svg_filename']} · "
                    f"{result['pdf_filename']}"
                )

            with svg_column:
                st.download_button(
                    label="Download SVG",
                    data=result["svg_data"],
                    file_name=result["svg_filename"],
                    mime="image/svg+xml",
                    key=f"svg-{index}-{result['svg_filename']}",
                    on_click="ignore",
                    use_container_width=True
                )

            with pdf_column:
                st.download_button(
                    label="Download PDF",
                    data=result["pdf_data"],
                    file_name=result["pdf_filename"],
                    mime="application/pdf",
                    key=f"pdf-{index}-{result['pdf_filename']}",
                    on_click="ignore",
                    use_container_width=True
                )

    if st.button("Clear Results"):
        st.session_state.processed_files = []
        st.rerun()