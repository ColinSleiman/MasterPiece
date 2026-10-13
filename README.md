# MasterPiece Image Vectorizer

MasterPiece Image Vectorizer is a Streamlit application that converts raster
images into scalable SVG files and vector PDF documents. It uses OpenCV to
prepare a black-and-white bitmap, Potrace to trace that bitmap as SVG, and
CairoSVG to produce a vector PDF from the SVG.

## Table of contents

- [Live application](#live-application)
- [Features](#features)
- [Project structure](#project-structure)
  - [File responsibilities](#file-responsibilities)
- [Processing workflow](#processing-workflow)
- [Run with Docker (recommended)](#run-with-docker-recommended)
  - [Prerequisites](#prerequisites)
  - [Start the application](#start-the-application)
  - [Run in the background](#run-in-the-background)
  - [Force a clean rebuild](#force-a-clean-rebuild)
- [Run directly with Conda](#run-directly-with-conda)
  - [1. Create the environment](#1-create-the-environment)
  - [2. Install native dependencies](#2-install-native-dependencies)
  - [3. Install Python dependencies](#3-install-python-dependencies)
  - [4. Verify the environment](#4-verify-the-environment)
  - [5. Start Streamlit](#5-start-streamlit)
- [Using the application](#using-the-application)
- [Production deployment on Render](#production-deployment-on-render)
- [Troubleshooting](#troubleshooting)
- [Operational notes](#operational-notes)
- [Potential improvements](#potential-improvements)
- [Author](#author)

## Live application

The deployed application is available at
[https://masterpiece-0rgt.onrender.com/](https://masterpiece-0rgt.onrender.com/).

## Features

- Upload multiple PNG, JPG, JPEG, BMP, or WebP images.
- Preview uploaded images before processing.
- Adjust the grayscale threshold from 0 to 255; `180` is the default.
- Continue processing a batch when an individual image fails.
- Review results in a grid or list layout.
- Download each result as SVG, vector PDF, or a ZIP containing both files.
- Download all successful results in a ZIP archive.
- Keep generated results available during Streamlit reruns and download clicks.
- Clear the selected uploads or generated results explicitly.

## Project structure

```text
Masterpiece/
`-- ImageVectorizer/                  # Repository root
    |-- .git/                         # Local Git metadata
    |-- .vscode/                      # Local VS Code workspace settings
    |   `-- settings.json
    |-- assets/                       # Application presentation assets
    |   |-- css/
    |   |   |-- app.css
    |   |   `-- image_viewer.css
    |   `-- img/
    |       `-- logo.png
    |-- docker/                       # Container configuration
    |   |-- Dockerfile
    |   |-- Dockerfile.dockerignore
    |   `-- compose.yaml
    |-- .gitignore
    |-- app.py                        # Streamlit entry point
    |-- image_processor.py            # Raster-to-vector processing
    |-- packages.txt                  # Native package manifest
    |-- requirements.txt              # Python dependencies
    `-- README.md
```

`Masterpiece/` is the parent folder on the local machine. `ImageVectorizer/` is
the repository and command-working directory. Run all documented Python,
Docker, and Git commands from `ImageVectorizer/` unless a section explicitly
states otherwise.

### File responsibilities

- `app.py` defines the Streamlit page, upload controls, previews, session state,
  processing feedback, and download controls. It loads the logo and CSS from
  `assets/`.
- `image_processor.py` contains the raster-to-vector processing pipeline. It
  has no Streamlit dependency.
- `assets/css/app.css` contains page-level Streamlit styling.
- `assets/css/image_viewer.css` styles the reusable preview and full-size image
  viewer component.
- `assets/img/logo.png` is used beside the page title and as the browser favicon.
- `requirements.txt` pins the Python dependencies.
- `packages.txt` lists native packages for Debian-compatible platforms that
  support this manifest. The Docker image installs its native packages directly.
- `docker/Dockerfile` defines the production-compatible container image.
- `docker/compose.yaml` builds and runs the image locally on port `8501`.
- `docker/Dockerfile.dockerignore` excludes local environments, caches, secrets,
  and generated files from the Docker build context.

The `.git/` and `.vscode/` entries describe the current local workspace. Their
contents can differ between machines. Editor settings are excluded from Git and
from the Docker image; `.git/` itself stores the repository metadata.

## Processing workflow

For each uploaded image, the application:

1. Reads the uploaded bytes and decodes the image as grayscale.
2. Applies the selected binary threshold.
3. Inverts the black-and-white result for Potrace.
4. Creates a temporary PBM bitmap.
5. Runs Potrace to generate an SVG.
6. Converts the SVG to a vector PDF with CairoSVG.
7. Reads the SVG and PDF into memory for download.
8. Removes the temporary processing directory automatically.

Uploaded and generated files are not stored permanently by the application.
Results remain in the active Streamlit session until they are cleared or the
session ends.

## Run with Docker (recommended)

Docker is the simplest local setup because the image includes Python 3.11,
Potrace, Cairo, and the other native runtime libraries.

### Prerequisites

- Docker Desktop on Windows or macOS, or Docker Engine on Linux.
- Docker Compose v2, available through the `docker compose` command.

### Start the application

Run this command from the repository root:

```bash
docker compose -f docker/compose.yaml up --build
```

Open [http://localhost:8501](http://localhost:8501).

Press `Ctrl+C` to stop a foreground run. Then remove the stopped container and
network with:

```bash
docker compose -f docker/compose.yaml down
```

### Run in the background

```bash
docker compose -f docker/compose.yaml up -d --build
```

Useful lifecycle commands:

```bash
docker compose -f docker/compose.yaml ps
docker compose -f docker/compose.yaml logs -f
docker compose -f docker/compose.yaml down
```

### Force a clean rebuild

Use a clean rebuild when changing base packages or diagnosing a stale Docker
cache:

```bash
docker compose -f docker/compose.yaml build --no-cache
docker compose -f docker/compose.yaml up
```

The Compose file is stored in `docker/`, but its build context is the repository
root. This is intentional: the Dockerfile must be able to copy `app.py`,
`image_processor.py`, `requirements.txt`, and `assets/` into the image.

The container health check uses
[http://localhost:8501/_stcore/health](http://localhost:8501/_stcore/health).
A healthy response is `ok` with HTTP status `200`.

## Run directly with Conda

Use this option when you want to run Streamlit without Docker. Python packages
alone are not enough: Potrace and Cairo are native dependencies and must also be
installed.

### 1. Create the environment

```bash
conda create -n imagevectorizer_env python=3.11
conda activate imagevectorizer_env
```

### 2. Install native dependencies

On Windows, macOS, or Linux with Conda:

```bash
conda install -c conda-forge cairo potrace
```

On Debian or Ubuntu without Conda-managed native packages:

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libgomp1 potrace
```

On macOS with Homebrew:

```bash
brew install cairo potrace
```

### 3. Install Python dependencies

From the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Verify the environment

```bash
python -c "import cv2, numpy, PIL, cairosvg, streamlit; print('Python dependencies are available')"
potrace --version
```

### 5. Start Streamlit

```bash
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

## Using the application

1. Select one or more supported raster images.
2. Review the image previews.
3. Adjust the threshold if necessary. Higher values include more light pixels
   in the traced foreground.
4. Select **Process images**.
5. Review any per-file error messages; other valid files continue processing.
6. Download individual SVG or PDF results, or download all results as a ZIP.
7. Select **Clear results** when the generated files are no longer needed.

## Production deployment on Render

The production service uses the repository's Docker image. Render does not use
`docker/compose.yaml`; Compose is only for local container management.

Configure the Render web service as follows:

| Setting | Value |
| --- | --- |
| Repository | `ColinSleiman/MasterPiece` |
| Branch | `main` |
| Runtime | Docker |
| Dockerfile path | `./docker/Dockerfile` |
| Docker build context | Repository root |
| Environment variable | `PORT=8501` |
| Health check path | `/_stcore/health` |
| Auto-deploy | Enabled for `main` |

The Docker command starts Streamlit on `0.0.0.0:8501`, allowing Render to route
traffic to the container. The health check confirms that the Streamlit server
is ready before a deployment is considered healthy.

After validating a change locally:

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

A successful push to `main` triggers a new Render deployment when auto-deploy is
enabled. Deployment progress and runtime output are available in the service's
**Events** and **Logs** pages.

## Troubleshooting

| Problem | Likely cause | Resolution |
| --- | --- | --- |
| **Streamlit or another Python dependency is missing** | The intended Conda environment is inactive, or its packages are incomplete. | Run `conda activate imagevectorizer_env`, then `python -m pip install -r requirements.txt`. |
| **Potrace is unavailable** | Potrace is not installed or is missing from `PATH`. | Install Potrace through Conda or the operating-system package manager, then run `potrace --version`. Docker users do not need a host installation because Potrace is included in the image. |
| **CairoSVG cannot load Cairo** | The CairoSVG Python package is installed, but the native Cairo library is missing. | Install Cairo in the active Conda environment or through the operating system, then restart the terminal and application. |
| **An uploaded image cannot be decoded** | The file is corrupt, unsupported, or has an extension that does not match its real format. | Confirm that the file contains valid PNG, JPEG, BMP, or WebP data. Renaming a file extension does not convert the image. |
| **Port 8501 is already in use** | Another application or container is listening on port `8501`. | Stop the other service, or change the mapping in `docker/compose.yaml` from `"8501:8501"` to `"8502:8501"`, then open `http://localhost:8502`. |
| **Docker cannot connect to the daemon** | Docker Desktop is stopped or its Windows WSL 2 engine is unavailable. | Start Docker Desktop, confirm that WSL 2 is enabled, then run `docker compose -f docker/compose.yaml ps`. |
| **The container does not become healthy** | Streamlit failed during startup, or the Docker paths or port configuration are incorrect. | Run `docker compose -f docker/compose.yaml ps` and `docker compose -f docker/compose.yaml logs`. Look for the `0.0.0.0:8501` startup message and confirm that `build.context` remains `..` in `docker/compose.yaml`. |
| **A Render deployment fails** | The Dockerfile path, build context, port, health check, or deployed branch is incorrect. | Confirm Docker runtime, Dockerfile path `./docker/Dockerfile`, repository-root build context, `PORT=8501`, health path `/_stcore/health`, and the intended branch. Read the complete error in Render's **Events** and **Logs** before retrying. |

## Operational notes

- Generated PBM, SVG, PDF, and ZIP files are temporary or held in memory.
- The Render filesystem is treated as ephemeral; no persistent disk is needed.
- The public application has no authentication.
- Apply appropriate upload-size, memory, CPU, and request-time limits before
  accepting private files or high-volume untrusted traffic.
- No credentials or external service integrations are required by the current
  application.

## Potential improvements

- Live threshold previews before vectorization.
- Additional Potrace tracing controls.
- Automated processing and browser tests in continuous integration.
- Configurable image-dimension and batch-size limits.
- Additional vector export formats.
- Optional authentication and access control.

## Author

Colin Sleiman — Computer Science Graduate, Antonine University, Lebanon
