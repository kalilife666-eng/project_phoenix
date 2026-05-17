#!/usr/bin/env python3
"""Isolate prison scene drawing elements and build an inspection board."""

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageTk


SOURCE_FILES = {
    "prison": "prison_fire.png",
    "reaper": "reaper_face.png",
    "skull_1": "skull_1_reaper_face.png",
    "skull_2": "skull_2_lower_left.png",
    "skull_3": "skull_3_lower_center.png",
    "skull_4": "skull_4_right_mound.png",
}


def _percentile_from_hist(hist, pct):
    total = sum(hist)
    if total <= 0:
        return 0
    target = max(0, min(total - 1, int(total * pct)))
    running = 0
    for idx, value in enumerate(hist):
        running += value
        if running > target:
            return idx
    return 255


def _combined_histograms(histograms):
    out = [0] * 256
    for hist in histograms:
        for idx, value in enumerate(hist):
            out[idx] += value
    return out


def _edge_hist(gray):
    w, h = gray.size
    edge = max(2, int(min(w, h) * 0.02))
    top = gray.crop((0, 0, w, edge)).histogram()
    bottom = gray.crop((0, h - edge, w, h)).histogram()
    left = gray.crop((0, edge, edge, h - edge)).histogram()
    right = gray.crop((w - edge, edge, w, h - edge)).histogram()
    return _combined_histograms([top, bottom, left, right])


def _alpha_from_gray(gray):
    edge_hist = _edge_hist(gray)
    paper_tone = _percentile_from_hist(edge_hist, 0.72)
    smooth_radius = max(6, int(min(gray.size) * 0.025))
    smooth = gray.filter(ImageFilter.GaussianBlur(radius=smooth_radius))
    local_depth = ImageChops.subtract(smooth, gray)
    global_depth = gray.point(lambda px, bg=paper_tone: max(0, bg - px), "L")
    depth = ImageChops.lighter(local_depth, global_depth)
    depth = ImageOps.autocontrast(depth, cutoff=1)

    depth_hist = depth.histogram()
    floor = _percentile_from_hist(depth_hist, 0.68)
    floor = max(18, min(96, floor))
    alpha = depth.point(
        lambda px, base=floor: 0 if px <= base else min(255, int((px - base) * 255 / max(1, 255 - base))),
        "L",
    )
    return alpha


def _crop_to_content(rgba, alpha):
    strong = alpha.point(lambda px: 255 if px > 28 else 0, "L")
    bbox = strong.getbbox()
    if bbox is None:
        return rgba, alpha
    x0, y0, x1, y1 = bbox
    pad = max(6, int(min(rgba.size) * 0.015))
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(rgba.width, x1 + pad)
    y1 = min(rgba.height, y1 + pad)
    crop_box = (x0, y0, x1, y1)
    return rgba.crop(crop_box), alpha.crop(crop_box)


def isolate_element(source_path):
    rgb = ImageOps.exif_transpose(Image.open(source_path)).convert("RGB")
    gray = rgb.convert("L")
    alpha = _alpha_from_gray(gray)
    art = ImageOps.colorize(gray, black="#131821", white="#f0f5ff").convert("RGBA")
    art.putalpha(alpha)
    cropped_art, _ = _crop_to_content(art, alpha)
    return cropped_art


def build_board(isolated_images):
    cols = 3
    rows = (len(isolated_images) + cols - 1) // cols
    cell_w = 520
    cell_h = 360
    pad = 20
    board_w = cols * cell_w + (cols + 1) * pad
    board_h = rows * cell_h + (rows + 1) * pad + 28
    board = Image.new("RGB", (board_w, board_h), "#0d1218")
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    draw.text((pad, 8), "Prison Scene Element Isolation Preview", fill="#f2f4f8", font=font)

    for idx, (label, img) in enumerate(isolated_images.items()):
        row = idx // cols
        col = idx % cols
        x = pad + col * (cell_w + pad)
        y = 28 + pad + row * (cell_h + pad)
        draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=12, outline="#d9dee8", width=2, fill="#171d26")
        draw.text((x + 12, y + 10), label, fill="#f5f7fb", font=font)

        available_w = cell_w - 30
        available_h = cell_h - 52
        render = img.copy()
        render.thumbnail((available_w, available_h), Image.LANCZOS)
        comp = Image.new("RGBA", (available_w, available_h), (0, 0, 0, 0))
        ox = (available_w - render.width) // 2
        oy = (available_h - render.height) // 2
        comp.alpha_composite(render, (ox, oy))
        board.paste(comp.convert("RGB"), (x + 15, y + 38))
    return board


def preview_board(board):
    import tkinter as tk

    root = tk.Tk()
    root.title("Prison Scene Isolation Preview")
    photo = ImageTk.PhotoImage(board)
    label = tk.Label(root, image=photo, bd=0)
    label.image = photo
    label.pack()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Isolate reaper/prison/skull elements for inspection.")
    parser.add_argument(
        "--assets-dir",
        default="assets/reaper_elements",
        help="Path to the drawing assets directory (default: assets/reaper_elements).",
    )
    parser.add_argument(
        "--out-dir",
        default="assets/reaper_elements/isolated",
        help="Output directory for isolated files and inspection board.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open a desktop preview window after generating outputs.",
    )
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    isolated = {}
    for label, filename in SOURCE_FILES.items():
        src = assets_dir / filename
        if not src.exists():
            raise FileNotFoundError(f"Missing required source image: {src}")
        img = isolate_element(src)
        img.save(out_dir / f"{label}_isolated.png")
        isolated[label] = img

    board = build_board(isolated)
    board_path = out_dir / "scene_isolation_board.png"
    board.save(board_path)

    print(f"Isolated elements written to: {out_dir}")
    print(f"Inspection board: {board_path}")

    if args.preview:
        preview_board(board)


if __name__ == "__main__":
    main()
