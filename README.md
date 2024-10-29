# Convert 2 Markdown

## Features

- Convert PDF, JPG, PNG, CSV, XLSX files to markdown
- Process PDFs and images using the marker-pdf library (extracting images)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/mrwinton/convert2markdown.git
   cd convert2markdown
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Install PyTorch and related packages:

   For CPU:
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

   For GPU (CUDA 11.8):
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

## Usage

1. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

2. Run the script:
   ```
   python app.py <input_file> <output_dir>
   ```

## Troubleshooting

- For dependency errors on MacOS, try
  ```
  pip install transformers==4.45.2 surya-ocr==0.4.14 pdftext==0.3.7 marker_pdf==0.2.6
  ```
