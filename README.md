# Image Vectorizer

A Python-based image vectorization application built with **Streamlit** that converts raster images into scalable **SVG** and **vector PDF** formats using **OpenCV**, **Potrace**, and **CairoSVG**.

The application provides a modern graphical interface, eliminating the need to manually edit variables inside a Jupyter Notebook. Users can upload one or more images, adjust the threshold value, process the images, and download the generated vector files individually or as a ZIP archive.

---

# Features

- Upload one or multiple images.
- Adjustable threshold slider.
- Automatic image preview.
- Convert raster images to SVG.
- Convert SVG files to vector PDF.
- Download individual SVG files.
- Download individual PDF files.
- Download all generated files as a ZIP archive.
- Clean and responsive Streamlit interface.

---

# Technologies

| Technology | Purpose |
|------------|---------|
| Python 3.11 | Programming Language |
| Streamlit | User Interface |
| OpenCV | Image Processing |
| NumPy | Numerical Operations |
| Pillow | PBM Image Generation |
| Potrace | Bitmap to SVG Conversion |
| CairoSVG | SVG to PDF Conversion |
| Conda | Environment Management |

---

# Project Structure

```
ImageVectorizer/
│
├── app.py
├── image_processor.py
├── requirements.txt
└── README.md
```

| File | Description |
|------|-------------|
| `app.py` | Streamlit user interface |
| `image_processor.py` | Image processing and vectorization logic |
| `requirements.txt` | Python package dependencies |
| `README.md` | Project documentation |

---

# Solution Architecture

The application is divided into independent modules following a layered architecture.

```
                User
                  │
                  ▼
          Streamlit Interface
               (app.py)
                  │
                  ▼
      Image Processing Module
        (image_processor.py)
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
   OpenCV      Potrace    CairoSVG
      │           │           │
      ▼           ▼           ▼
  Threshold      SVG      Vector PDF
```

---

# Separation of Concerns (SoC)

The application follows the **Separation of Concerns (SoC)** software design principle.

## Presentation Layer

Implemented by:

- `app.py`

Responsibilities:

- User interface
- File uploads
- Image previews
- Threshold selection
- Download buttons
- ZIP generation

No image-processing logic is implemented in this layer.

---

## Business Logic Layer

Implemented by:

- `image_processor.py`

Responsibilities:

- Reading uploaded images
- Image preprocessing
- Thresholding
- Binary inversion
- PBM generation
- Potrace execution
- SVG generation
- PDF generation

This module has no knowledge of the user interface.

---

## Configuration Layer

Responsible for:

- Python dependencies
- Conda environment
- External libraries

Files:

- `requirements.txt`
- Conda Environment

---

## Documentation Layer

Implemented through:

- `README.md`

Provides installation instructions, architecture, usage information, and project documentation.

---

# Development Environment Setup

## 1. Clone the Repository

```bash
git clone <repository-url>
cd ImageVectorizer
```

---

## 2. Create a Conda Environment

Create an isolated Conda environment to prevent dependency conflicts with other projects.

```bash
conda create -n imagevectorizer_env python=3.11
```

Activate the environment:

```bash
conda activate imagevectorizer_env
```

---

## 3. Install Python Packages

```bash
pip install streamlit opencv-python numpy pillow cairosvg
```

---

## 4. Install Cairo

```bash
conda install -c conda-forge cairo
```

---

## 5. Configure the Cairo Library Path

Add the Anaconda Cairo library directory to the current environment.

Windows Command Prompt:

```cmd
set "PATH=C:\Users\User\anaconda3\Library\bin;%PATH%"
```

PowerShell:

```powershell
$env:PATH="C:\Users\User\anaconda3\Library\bin;$env:PATH"
```

---

## 6. Verify the Installation

Verify CairoSVG:

```bash
python -c "import cairosvg; print('CairoSVG works')"
```

Verify all installed packages:

```bash
python -c "import streamlit, cv2, numpy, PIL, cairosvg; print('All Python packages work')"
```

Verify Potrace:

```bash
potrace --version
```

---

# Running the Application

Start the Streamlit server:

```bash
python -m streamlit run app.py
```

The application will be available at:

```
http://localhost:8501
```

---

# Image Processing Workflow

The processing pipeline consists of the following steps:

1. Upload an image.
2. Convert the image to grayscale.
3. Apply binary thresholding.
4. Invert the binary image.
5. Save the image as PBM.
6. Execute Potrace.
7. Generate an SVG file.
8. Convert the SVG into a vector PDF.
9. Display download options.

---

# User Workflow

1. Launch the application.
2. Upload one or more images.
3. Adjust the threshold slider.
4. Click **Process Images**.
5. Wait for processing to complete.
6. Download:
   - SVG
   - PDF
   - ZIP archive

---

# Dependencies

```
streamlit
opencv-python
numpy
Pillow
CairoSVG
```

External dependency:

- Potrace 1.16+

---

# Design Principles

This project was developed following several software engineering principles:

- Separation of Concerns (SoC)
- Single Responsibility Principle (SRP)
- Modular Architecture
- Maintainability
- Scalability
- Reusability
- Readability

---

# Future Improvements

Potential enhancements include:

- Live threshold preview.
- Additional vectorization options.
- Adjustable Potrace parameters.
- Dark mode interface.
- Batch processing statistics.
- Drag-and-drop uploads.
- Image cropping and preprocessing.
- Export to additional vector formats.
- Docker support.
- Automatic installer.

---

# License

This project is intended for educational and research purposes.

---

# Author

**Colin Sleiman**

Computer Science Graduate  
Antonine University – Lebanon