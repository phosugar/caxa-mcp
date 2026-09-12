"""
Example 3: Parametric Flange Generation
Demonstrates drawing a pipe flange with bolt circle (PCD), bolt holes,
hub, cross-section view, and engineering dimensions.
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from caxa_mcp import CADEngine, CAXAController


def main():
    print("=== Creating Parametric Flange ===")
    engine = CADEngine()

    # 1. Setup A3 GB Drawing Sheet
    engine.add_gb_frame_and_titleblock(
        paper_size="A3",
        title="管路法兰盘",
        part_no="FLANGE-DN50-PN16",
        material="Q235-A",
        scale_text="1:1",
        designer="AI Assistant",
        tech_notes=[
            "法兰密封面为突面 (RF)",
            "螺栓孔按 GB/T 9119 标准均布",
            "未注尺寸公差按 GB/T 1804-m 级执行",
        ],
    )

    # 2. Draw Parametric Flange
    # Outer D=165, Inner d=50, PCD=125, 4xΦ18 holes, Thickness=18, Hub D=75, Total Thickness=38
    flange_info = engine.generate_flange(
        center=(140.0, 150.0),
        outer_diameter=165.0,
        inner_diameter=50.0,
        pcd=125.0,
        hole_count=4,
        hole_diameter=18.0,
        thickness=18.0,
        hub_diameter=75.0,
        hub_length=20.0,
        add_side_view=True,
        side_view_x=310.0,
    )
    print(f"Flange generated: OD = {flange_info['outer_diameter']} mm, Holes = {flange_info['hole_count']}")

    # 3. Save to DXF
    output_dxf = os.path.join(CURRENT_DIR, "output_flange.dxf")
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
