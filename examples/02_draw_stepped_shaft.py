"""
Example 2: Parametric Stepped Shaft Generation
Demonstrates drawing a stepped transmission shaft with chamfers, centerlines,
and dimension annotations, then launching CAXA CAD 2023 to view it.
"""

import os
import sys

# Ensure package root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from caxa_mcp import CADEngine, CAXAController


def main():
    print("=== Creating Parametric Stepped Shaft ===")
    engine = CADEngine()

    # 1. Setup A3 GB Standard Drawing Sheet
    engine.add_gb_frame_and_titleblock(
        paper_size="A3",
        title="传动阶梯轴",
        part_no="SHAFT-2026-01",
        material="40Cr",
        scale_text="1:1",
        designer="AI Assistant",
        tech_notes=[
            "热处理：调质处理 220~250 HBS",
            "未注倒角 C1.0，未注圆角 R1.5",
            "表面粗糙度除特别标注外均为 Ra 3.2",
        ],
    )

    # 2. Draw Parametric Stepped Shaft
    # 4 Steps: Φ35x50 (Bearing), Φ50x70 (Gear seat), Φ42x60, Φ30x35 (Coupling)
    steps = [
        {"d": 35.0, "l": 50.0},
        {"d": 50.0, "l": 70.0},
        {"d": 42.0, "l": 60.0},
        {"d": 30.0, "l": 35.0},
    ]

    shaft_info = engine.generate_stepped_shaft(
        origin=(70.0, 150.0),
        steps=steps,
        chamfer_left=1.5,
        chamfer_right=1.0,
        add_centerline=True,
        add_dimensions=True,
    )
    print(f"Shaft generated: total length = {shaft_info['total_length']} mm")

    # 3. Save to DXF
    output_dxf = os.path.join(CURRENT_DIR, "output_stepped_shaft.dxf")
    saved_path = engine.save(output_dxf)
    print(f"Saved drawing to: {saved_path}")

    # 4. Open in CAXA CAD 2023
    controller = CAXAController()
    if controller.is_installed:
        print("Opening drawing in CAXA CAD 2023...")
        controller.open_drawing(saved_path)
        controller.zoom_extents()
        print("Opened successfully!")
    else:
        print("Notice: CAXA CAD not found on this machine. DXF file is ready for any CAD viewer.")


if __name__ == "__main__":
    main()
