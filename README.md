# Bubblexan

## Bubble Sheet Generator

Create a printable bubble sheet PDF and matching JSON guide rail.

```bash
python generate_bubblesheet.py \
  --questions 25 \
  --id-length 6 \
  [--id-orientation vertical|horizontal] \
  [--border] \
  --output exam1 \
  [--paper-size A4] \
  [--output-dir output]
```

- Produces `output/exam1.pdf` and `output/exam1_layout.json` (unless an absolute `--output` path is supplied).
- Questions can range from 1–50, student ID length 4–10 digits.
- `--id-orientation horizontal` arranges each ID digit as a row of bubbles (0–9 left to right) instead of stacked columns.
- Pass `--border` if you specifically need the thick outer frame drawn; it is disabled by default for better alignment detection.
- The PDF automatically prints the output name (e.g., `exam1`) as a centered title near the top margin.

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

### Visualization Helper

Use `testvision.py` to overlay bubble locations/scores on top of a scanned image when you need to debug alignment or thresholding:

```bash
python testvision.py \
  --image output/png/exam1_page01.png \
  --json output/exam1_layout.json \
  --output output/annotated.png \
  [--threshold 0.35] [--relative-threshold 0.6] [--alpha 0.6]
```

The script emits a blended PNG showing each bubble’s measured fill ratio (color-coded and labeled) plus any transform warnings when `--show-warnings` is passed.

## Question Miss Analyzer

Compare the scanner’s CSV against an answer key to spot questions most students missed (and summarize partial credit on select-all prompts):

```bash
python analyze_misses.py \
  --results output/results.csv \
  --key answer_key.csv \
  --output output/miss_report.csv \
  [--miss-threshold 50] \
  [--partial-threshold 1.0] \
  [--log miss_report.log]
```

- Pass the scanner CSV via `--results` and an answer-key CSV (`Question,Answer`) via `--key`.
- Multi-answer keys can use bracket or comma syntax (e.g., `[A,B,E]`); set `--partial-threshold` < 1.0 to award credit for subsets.
- The tool writes a per-question CSV detailing percent missed, counts, and partial-credit notes, and highlights questions above the miss threshold in the console.

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
