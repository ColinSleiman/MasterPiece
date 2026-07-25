# Image Vectorizer

Image Vectorizer is a Streamlit application that converts raster images into
scalable SVG files and vector PDF documents. It applies an adjustable grayscale
threshold with OpenCV, traces the resulting bitmap with Potrace, and converts
the SVG output to PDF with CairoSVG.

## Features

- Upload and preview multiple PNG, JPG, JPEG, BMP, or WebP images.
- Adjust the binary threshold from 0 to 255.
- Continue a batch when an individual file fails.
- Download each generated SVG and PDF independently.
- Download all successful results in one compressed ZIP archive.
- Keep results available across Streamlit reruns and download clicks.
- Clear results explicitly when they are no longer needed.
- Run locally with Python 3.11 or in an isolated Docker container.

## Technologies

| Technology | Responsibility |
| --- | --- |
| Python 3.11 | Application runtime |
| Streamlit | Web interface and session state |
| OpenCV and NumPy | Image decoding, grayscale data, and thresholding |
| Pillow | Temporary PBM creation |
| Potrace | Bitmap-to-SVG vector tracing |
| CairoSVG and Cairo | SVG-to-vector-PDF conversion |
| Docker and Docker Compose | Reproducible Linux packaging and operation |

## Project Structure

```text
ImageVectorizer/
|-- app.py
|-- image_processor.py
|-- requirements.txt
|-- Dockerfile
|-- compose.yaml
|-- packages.txt
|-- .dockerignore
|-- .gitignore
`-- README.md
```

## Solution Architecture

```text
Browser
  |
  v
Streamlit presentation and session state (app.py)
  |
  v
Image-processing business logic (image_processor.py)
  |
  +-- OpenCV: decode, grayscale, threshold, invert
  +-- Pillow: create temporary PBM
  +-- Potrace: create SVG
  `-- CairoSVG/Cairo: create vector PDF
```

Temporary PBM, SVG, and PDF files exist only inside a
`tempfile.TemporaryDirectory`. The application reads the final SVG and PDF into
memory before that directory is removed.

## Separation of Concerns

`app.py` contains the presentation layer: page configuration, uploads,
previews, controls, progress, messages, ZIP creation, downloads, and Streamlit
session state. It does not contain OpenCV, Potrace, PBM, SVG, or PDF processing.

`image_processor.py` contains the business logic. It reads an uploaded-file-like
object, performs the raster processing pipeline, invokes Potrace, converts the
SVG to PDF, and returns structured filenames and bytes. It has no Streamlit
dependency.

The remaining files define dependencies, container packaging, deployment
metadata, ignore rules, and documentation.

## Local Installation with Conda

Create and activate the requested Python 3.11 environment:

```bash
conda create -n imagevectorizer_env python=3.11
conda activate imagevectorizer_env
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The direct Python dependencies are pinned in `requirements.txt`. The headless
OpenCV distribution is used because the application does not need OpenCV desktop
windows.

### Required Native Dependencies

Potrace is an executable, and Cairo is the native rendering library used by
CairoSVG. They are not pip packages.

For a Conda environment on Windows, macOS, or Linux:

```bash
conda install -c conda-forge cairo potrace
```

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libgomp1 potrace
```

On macOS with Homebrew:

```bash
brew install cairo potrace
```

Verify the local environment:

```bash
python -c "import cv2, numpy, PIL, cairosvg, streamlit; print('Python dependencies import successfully')"
potrace --version
```

## Run Locally

Activate the environment and start Streamlit:

```bash
conda activate imagevectorizer_env
python -m streamlit run app.py
```

Open <http://localhost:8501>.

## Run with Docker

Docker builds its own isolated Debian-based Python 3.11 environment. It does not
use or depend on the local Conda environment.

Build the image:

```bash
docker compose build --no-cache
```

Start in the foreground:

```bash
docker compose up
```

Or start in the background:

```bash
docker compose up -d
```

Useful lifecycle commands:

```bash
docker compose logs -f
docker compose ps
docker compose down
```

The application is available at <http://localhost:8501>. The container health
check calls `http://localhost:8501/_stcore/health`.

## Image-Processing Workflow

For each uploaded file, the processor:

1. Reads the uploaded bytes and decodes the image as grayscale.
2. Applies `cv2.THRESH_BINARY` with the selected threshold.
3. Inverts the binary result.
4. Writes a temporary PBM bitmap.
5. runs `potrace input.pbm -s -o output.svg`.
6. Converts the SVG to a vector PDF with CairoSVG.
7. Returns both generated files as bytes for download.
8. Automatically removes all temporary processing files.

## Usage

1. Upload one or more supported raster images.
2. Review the compact image previews.
3. Adjust the threshold. A higher value includes more light pixels in the
   traced foreground.
4. Select **Process Images** and follow the batch progress.
5. Review any per-file errors; other valid files continue processing.
6. Download individual SVG or PDF files, or select **Download All as ZIP**.
7. Select **Clear Results** when finished.

## Troubleshooting

### `Potrace is not installed or is not available on PATH`

Install Potrace with Conda or the platform package manager, reactivate the shell,
and verify `potrace --version`. Docker installs Potrace automatically.

### Cairo or CairoSVG cannot load a native library

Install the native Cairo package, reactivate `imagevectorizer_env`, and retry the
import check. On Windows, installing Cairo from `conda-forge` inside the active
environment avoids hard-coded machine-specific library paths.

### An image cannot be decoded

Confirm that the file contains valid PNG, JPEG, BMP, or WebP image data. Changing
a filename extension does not convert the underlying format.

### Port 8501 is already in use

Stop the other service or change the host side of the Compose mapping, for
example `"8502:8501"`, then open `http://localhost:8502`.

### Docker commands cannot connect to the daemon

Start Docker Desktop. On Windows, confirm that the WSL 2 engine is enabled, then
run `docker compose ps` again.

### Inspect container startup failures

```bash
docker compose ps
docker compose logs
```

## Notes About Cairo and Potrace

Potrace performs the actual bitmap tracing and must be available as a command on
`PATH`. CairoSVG is a Python package, but it uses the native Cairo library for
PDF rendering. `packages.txt` supports Debian-package-aware deployment
platforms; the Dockerfile installs the same runtime dependencies explicitly.

## Deployment Considerations

- Use a platform that permits the `potrace` executable and native Cairo library.
- Prefer the included Docker image when the platform supports containers.
- Keep port 8501 reachable and preserve the Streamlit health endpoint.
- Uploaded and generated files are processed in memory or temporary storage;
  results are not persisted after the Streamlit session or container ends.
- Apply platform upload-size, memory, CPU, and request-time limits appropriate
  for the expected image volume.
- No credentials or external services are required for the current application.

## Future Improvements

- Live threshold previews before vectorization.
- Additional exposed Potrace tracing options.
- Duplicate-output-name disambiguation for unusually named batches.
- Automated unit and browser tests in continuous integration.
- Optional limits for image dimensions and total batch size.
- Additional vector export formats.

## Author

Colin Sleiman
Computer Science Graduate, Antonine University, Lebanon
