import subprocess
from pathlib import Path
import time
import tempfile
import os
from PyPDF2 import PdfReader, PdfWriter
import uuid
import shutil
import argparse
import sys

# Constants
BATCH_MULTIPLIER = 4  # Adjust based on your VRAM capacity
MAX_PAGES = None  # Set to None to process entire documents, or specify a number
WORKERS = 1  # Since we're leveraging GPU, we'll process one file at a time
CHUNK_SIZE = 20  # Number of pages per chunk


def split_pdf(input_pdf_path, output_dir, chunk_size=CHUNK_SIZE):
    input_pdf = PdfReader(str(input_pdf_path))
    file_id = str(uuid.uuid4())
    pdf_chunks = []

    for i in range(0, len(input_pdf.pages), chunk_size):
        pdf_writer = PdfWriter()
        start_page = i + 1
        end_page = min(i + chunk_size, len(input_pdf.pages))

        for j in range(i, end_page):
            pdf_writer.add_page(input_pdf.pages[j])

        chunk_file_name = f"{file_id}_chunk_{start_page}_{end_page}.pdf"
        chunk_path = output_dir / chunk_file_name

        with open(chunk_path, "wb") as f:
            pdf_writer.write(f)

        pdf_chunks.append(
            {
                "file_id": file_id,
                "original_file": input_pdf_path.name,
                "chunk_file": chunk_path,
                "start_page": start_page,
                "end_page": end_page,
            }
        )

    return pdf_chunks


def run_marker_on_file(input_file, output_dir):
    command = f"PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 marker_single '{input_file}' '{output_dir}' --batch_multiplier {BATCH_MULTIPLIER}"
    if MAX_PAGES:
        command += f" --max_pages {MAX_PAGES}"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Marker command failed for {input_file}: {result.stderr}")

    return result.stdout


def process_chunk(chunk, output_dir):
    chunk_output_dir = output_dir / chunk["original_file"].rsplit(".", 1)[0]
    chunk_output_dir.mkdir(parents=True, exist_ok=True)
    run_marker_on_file(chunk["chunk_file"], chunk_output_dir)

    # Delete the chunk file after processing
    os.remove(chunk["chunk_file"])

    return chunk


def merge_chunk_results(chunks, output_dir):
    results = {}
    for chunk in chunks:
        file_id = chunk["file_id"]
        original_file = chunk["original_file"]
        chunk_folder = output_dir / original_file.rsplit(".", 1)[0] / chunk["chunk_file"].stem
        md_file = chunk_folder / f"{chunk['chunk_file'].stem}.md"

        if md_file.exists():
            with open(md_file, "r") as f:
                content = f.read()
                if file_id not in results:
                    results[file_id] = {"original_file": original_file, "content": []}
                results[file_id]["content"].append((chunk["start_page"], content))

    final_results = []
    for file_id, data in results.items():
        sorted_content = sorted(data["content"], key=lambda x: x[0])
        merged_content = "\n".join([content for _, content in sorted_content])
        final_results.append((data["original_file"], merged_content))

    return final_results


def process_file(input_path, output_dir):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    chunk_dir = output_dir / "chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    chunk_dir.mkdir(parents=True, exist_ok=True)

    # Split PDF into chunks
    chunks = split_pdf(input_path, chunk_dir)

    # Process chunks
    processed_chunks = []
    for chunk in chunks:
        print(f"Processing: {chunk['original_file']} (Pages {chunk['start_page']}-{chunk['end_page']})")
        processed_chunk = process_chunk(chunk, output_dir)
        processed_chunks.append(processed_chunk)

    # Merge results
    results = merge_chunk_results(processed_chunks, output_dir)

    return results[0][1] if results else ""  # Return the content string from the first result tuple

def main():
    parser = argparse.ArgumentParser(description='Process documents and extract text content.')
    parser.add_argument('input_file', help='Path to the input file')
    parser.add_argument('output_dir', help='Path to the output directory')
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        result = process_file(input_path, output_path)
        output_file = output_path / f"{input_path.stem}_extracted.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Successfully processed {input_path.name}. Output saved to {output_file}")
    except Exception as e:
        print(f"Error processing {input_path.name}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()