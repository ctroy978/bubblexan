#!/usr/bin/env python3
"""
Command-line Bubble Sheet Generator.

Creates a printable PDF answer sheet and a JSON layout description that can be
consumed by the scanning/analysis stage of an OMR pipeline.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from reportlab.lib import colors
from reportlab.pdfgen import canvas

MM_TO_POINTS = 72.0 / 25.4
QUESTIONS_RANGE = (1, 50)
ID_LENGTH_RANGE = (4, 10)
DEFAULT_ID_LENGTH = 6
OPTIONS = ["A", "B", "C", "D", "E"]

PAPER_SIZES: Dict[str, Tuple[int, int]] = {
    "A4": (595, 842),
    "LETTER": (612, 792),
}


def mm_to_points(value: float) -> float:
    return value * MM_TO_POINTS


@dataclass(frozen=True)
class LayoutSettings:
    margin: float
    bubble_radius: float
    question_label_width: float
    question_row_height: float
    question_column_spacing: float
    question_column_spacing_min: float
    option_step: float
    option_label_gap: float
    id_column_step: float
    id_vertical_step: float
    section_gap: float
    title_block: float
    student_id_header_gap: float
    digit_label_gap: float


def build_layout_settings() -> LayoutSettings:
    bubble_diameter = mm_to_points(5.0)
    return LayoutSettings(
        margin=36.0,
        bubble_radius=bubble_diameter / 2,
        question_label_width=mm_to_points(12.0),
        question_row_height=bubble_diameter + mm_to_points(4.0),
        question_column_spacing=mm_to_points(14.0),
        question_column_spacing_min=mm_to_points(6.0),
        option_step=bubble_diameter + mm_to_points(4.0),
        option_label_gap=mm_to_points(2.5),
        id_column_step=bubble_diameter + mm_to_points(6.0),
        id_vertical_step=bubble_diameter + mm_to_points(3.0),
        section_gap=mm_to_points(14.0),
        title_block=mm_to_points(18.0),
        student_id_header_gap=mm_to_points(8.0),
        digit_label_gap=mm_to_points(2.5),
    )


def validate_inputs(questions: int, id_length: int) -> None:
    if not (QUESTIONS_RANGE[0] <= questions <= QUESTIONS_RANGE[1]):
        raise ValueError(f"questions must be between {QUESTIONS_RANGE[0]} and {QUESTIONS_RANGE[1]}")
    if not (ID_LENGTH_RANGE[0] <= id_length <= ID_LENGTH_RANGE[1]):
        raise ValueError(f"id-length must be between {ID_LENGTH_RANGE[0]} and {ID_LENGTH_RANGE[1]}")


def generate_layout(
    questions: int, id_length: int, paper_key: str, settings: LayoutSettings
) -> Dict[str, object]:
    paper_name = paper_key.upper()
    if paper_name not in PAPER_SIZES:
        allowed = ", ".join(PAPER_SIZES.keys())
        raise ValueError(f"paper-size must be one of: {allowed}")

    width, height = PAPER_SIZES[paper_name]
    id_top_y = height - settings.margin - settings.title_block

    student_id_label_y = id_top_y + settings.bubble_radius + settings.student_id_header_gap

    student_id_layout, id_bottom_center_y = build_student_id_layout(
        id_length=id_length,
        start_x=settings.margin,
        top_center_y=id_top_y,
        settings=settings,
        page_width=width,
    )

    question_area_top = id_bottom_center_y - settings.bubble_radius - settings.section_gap

    question_layout, question_layout_meta = build_question_layout(
        questions=questions,
        area_top=question_area_top,
        page_width=width,
        settings=settings,
    )

    markers = build_alignment_markers(width, height, settings)

    return {
        "paper_size": paper_name,
        "dimensions": {"width": width, "height": height},
        "questions": question_layout,
        "student_id": student_id_layout,
        "alignment_markers": markers,
        "metadata": {
            "num_questions": questions,
            "id_length": id_length,
            "bubble_radius": settings.bubble_radius,
            "bubble_diameter": settings.bubble_radius * 2,
            "question_row_height": settings.question_row_height,
            "option_step": settings.option_step,
            "option_label_gap": settings.option_label_gap,
            "id_vertical_step": settings.id_vertical_step,
            "id_column_step": settings.id_column_step,
            "question_column_spacing": question_layout_meta["column_spacing"],
            "question_columns": question_layout_meta["columns"],
            "question_rows": question_layout_meta["rows"],
            "student_id_header_gap": settings.student_id_header_gap,
            "digit_label_gap": settings.digit_label_gap,
            "margin": settings.margin,
            "question_area_top": question_area_top,
            "student_id_label_y": student_id_label_y,
        },
    }


def build_student_id_layout(
    id_length: int,
    start_x: float,
    top_center_y: float,
    settings: LayoutSettings,
    page_width: float,
) -> Tuple[List[Dict[str, object]], float]:
    columns: List[Dict[str, object]] = []
    available_width = page_width - (2 * settings.margin)
    required_width = (id_length - 1) * settings.id_column_step
    if required_width + settings.bubble_radius * 2 > available_width:
        raise ValueError("Student ID section does not fit horizontally. Reduce id-length.")

    for digit_index in range(id_length):
        column_center_x = start_x + digit_index * settings.id_column_step
        label_y = top_center_y + settings.bubble_radius + settings.digit_label_gap
        column = {
            "digit_index": digit_index + 1,
            "label_position": {"x": column_center_x - settings.bubble_radius, "y": label_y},
            "bubbles": [],
        }
        for value in range(10):
            center_y = top_center_y - (value * settings.id_vertical_step)
            column["bubbles"].append(
                {"value": str(value), "x": column_center_x, "y": center_y, "radius": settings.bubble_radius}
            )
        columns.append(column)

    bottom_center_y = top_center_y - (9 * settings.id_vertical_step)
    return columns, bottom_center_y


def build_question_layout(
    questions: int,
    area_top: float,
    page_width: float,
    settings: LayoutSettings,
) -> Tuple[List[Dict[str, object]], Dict[str, float | int]]:
    question_block_width = settings.question_label_width + (2 * settings.bubble_radius) + settings.option_step * (
        len(OPTIONS) - 1
    )
    available_width = page_width - (2 * settings.margin)
    available_height = area_top - (settings.margin + settings.bubble_radius)
    if available_height <= settings.question_row_height:
        raise ValueError("Not enough vertical space for the questions section. Try reducing id-length.")

    max_rows_by_height = max(1, int(available_height // settings.question_row_height))

    def spacing_for_columns(column_count: int) -> float | None:
        if column_count == 1:
            return 0.0 if question_block_width <= available_width else None
        total_block_width = column_count * question_block_width
        if total_block_width > available_width:
            return None
        max_spacing_allowed = (available_width - total_block_width) / (column_count - 1)
        if max_spacing_allowed < settings.question_column_spacing_min:
            return None
        return min(settings.question_column_spacing, max_spacing_allowed)

    max_columns_by_width = int(
        (available_width + settings.question_column_spacing_min)
        // (question_block_width + settings.question_column_spacing_min)
    )
    max_columns_by_width = max(1, max_columns_by_width)
    max_columns = min(questions, max_columns_by_width)

    chosen_columns = None
    chosen_rows = None
    column_spacing = None
    for column_count in range(max_columns, 0, -1):
        rows_needed = math.ceil(questions / column_count)
        spacing = spacing_for_columns(column_count)
        if spacing is None:
            continue
        if rows_needed <= max_rows_by_height:
            chosen_columns = column_count
            chosen_rows = rows_needed
            column_spacing = spacing
            break

    if chosen_columns is None or chosen_rows is None or column_spacing is None:
        raise ValueError(
            "Question grid cannot fit on the selected paper size with the current parameters. "
            "Try reducing questions or student ID length."
        )

    layout: List[Dict[str, object]] = []
    question_number = 1

    for column_index in range(chosen_columns):
        column_x = settings.margin + column_index * (question_block_width + column_spacing)
        for row_index in range(chosen_rows):
            if question_number > questions:
                break
            center_y = area_top - row_index * settings.question_row_height
            label_position = {"x": column_x, "y": center_y}
            first_bubble_x = column_x + settings.question_label_width + settings.bubble_radius
            bubbles = []
            for option_index, option in enumerate(OPTIONS):
                bubble_x = first_bubble_x + option_index * settings.option_step
                bubbles.append({"option": option, "x": bubble_x, "y": center_y, "radius": settings.bubble_radius})

            layout.append({"number": question_number, "label_position": label_position, "bubbles": bubbles})
            question_number += 1

    return layout, {"columns": chosen_columns, "rows": chosen_rows, "column_spacing": column_spacing}


def build_alignment_markers(width: float, height: float, settings: LayoutSettings) -> List[Dict[str, float]]:
    size = mm_to_points(8.0)
    offset = settings.margin / 2
    return [
        {"type": "square", "x": offset, "y": offset, "size": size},
        {"type": "square", "x": width - offset - size, "y": offset, "size": size},
        {"type": "square", "x": offset, "y": height - offset - size, "size": size},
        {"type": "square", "x": width - offset - size, "y": height - offset - size, "size": size},
    ]


def render_pdf(layout: Dict[str, object], pdf_path: Path) -> None:
    width = layout["dimensions"]["width"]
    height = layout["dimensions"]["height"]
    metadata = layout["metadata"]
    c = canvas.Canvas(str(pdf_path), pagesize=(width, height))
    margin = metadata["margin"]
    bubble_radius = metadata["bubble_radius"]
    option_label_gap = metadata.get("option_label_gap", mm_to_points(2.5))

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, metadata["student_id_label_y"], "Student ID")

    c.setFont("Helvetica", 10)

    for column in layout["student_id"]:
        label = f"ID {column['digit_index']}"
        label_pos = column["label_position"]
        c.drawString(label_pos["x"], label_pos["y"], label)
        for bubble in column["bubbles"]:
            c.circle(bubble["x"], bubble["y"], bubble_radius)
            c.drawString(bubble["x"] + bubble_radius + 2, bubble["y"] - 3, bubble["value"])

    for question in layout["questions"]:
        label_text = f"Q{question['number']:02d}"
        label_pos = question["label_position"]
        c.drawString(label_pos["x"], label_pos["y"], label_text)
        for bubble in question["bubbles"]:
            c.circle(bubble["x"], bubble["y"], bubble_radius)
            c.setFont("Helvetica", 8)
            c.drawCentredString(bubble["x"], bubble["y"] - bubble_radius - option_label_gap, bubble["option"])
            c.setFont("Helvetica", 10)

    for marker in layout["alignment_markers"]:
        c.setStrokeColor(colors.black)
        c.rect(marker["x"], marker["y"], marker["size"], marker["size"], stroke=1, fill=0)

    c.showPage()
    c.save()


def write_layout_json(layout: Dict[str, object], json_path: Path) -> None:
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(layout, fp, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a printable bubble sheet PDF and companion JSON layout.", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--questions", type=int, required=True, help="Number of questions to include (1-50).")
    parser.add_argument(
        "--id-length",
        type=int,
        default=DEFAULT_ID_LENGTH,
        help=f"Number of digits in the student ID ({ID_LENGTH_RANGE[0]}-{ID_LENGTH_RANGE[1]}).",
    )
    parser.add_argument("--output", required=True, help="Output filename prefix (without extension).")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where generated files will be written (created if missing).",
    )
    parser.add_argument(
        "--paper-size",
        default="A4",
        choices=sorted(PAPER_SIZES.keys()),
        help="Paper size for the PDF.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = build_layout_settings()
    validate_inputs(args.questions, args.id_length)

    layout = generate_layout(args.questions, args.id_length, args.paper_size, settings)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix_path = Path(args.output)
    if prefix_path.is_absolute():
        base_prefix = prefix_path
    else:
        base_prefix = output_dir / prefix_path

    pdf_path = base_prefix.with_suffix(".pdf")
    json_path = base_prefix.with_name(f"{base_prefix.name}_layout.json")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    render_pdf(layout, pdf_path)
    write_layout_json(layout, json_path)

    print(f"Created {pdf_path} and {json_path}")


if __name__ == "__main__":
    main()
