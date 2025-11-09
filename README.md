# Bubblexan

## Bubble Sheet Generator

Create a printable bubble sheet PDF and matching JSON guide rail.

```bash
python generate_bubblesheet.py \
  --questions 25 \
  --id-length 6 \
  --output exam1 \
  [--paper-size A4] \
  [--output-dir output]
```

- Produces `output/exam1.pdf` and `output/exam1_layout.json` (unless an absolute `--output` path is supplied).
- Questions can range from 1–50, student ID length 4–10 digits.

## Bubble Sheet Scanner

Process scanned bubble sheets (single image, directory, or .zip) using the generator’s layout JSON and emit a CSV plus optional log.

```bash
python scan_bubblesheet.py \
  --image scan1.png | --folder scans/ \
  --json output/exam1_layout.json \
  --output results.csv \
  [--threshold 0.5] \
  [--output-dir output] \
  [--log custom.log]
```

- Use `--image` for one file or `--folder` (directory or .zip) for batches.
- Results land in `output/results.csv` and a log file (defaults to the same prefix with `.log`).

## PDF → PNG Converter

Render generator PDFs into raster images for the scanner or other tools. Requires a Poppler installation accessible on your PATH.

```bash
python convert_pdf_to_png.py \
  --pdf output/exam1.pdf | --folder pdfs/ \
  --output-dir output/png \
  [--dpi 300] \
  [--fmt png|jpg] \
  [--prefix exam1]
```

- Handles single PDFs, folders, or zipped collections.
- Saves numbered images such as `output/png/exam1_page01.png`, ready for OpenCV processing.
