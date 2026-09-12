"""
Test script for CAXA-MCP
Verifies CAD engine generation, DXF integrity, and tool functionality.
"""

import os
import sys
import ezdxf

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from cad_engine import CADEngine
from caxa_controller import CAXAController


def test_cad_engine():
    print("=== Testing CAD Engine ===")
    engine = CADEngine()

    # 1. Add GB frame and title block
    frame = engine.add_gb_frame_and_titleblock(
        paper_size="A3",
        title="传动阶梯轴",
        part_no="SHAFT-2026-01",
        material="45号钢",
        scale_text="1:1",
        designer="AI Assistant",
        checker="Senior Engineer",
        weight="3.2kg",
        tech_notes=[
            "调质处理，硬度 220-250 HBW",
            "未注倒角均为 C1",
            "未注圆角 R2",
            "各轴段径向圆跳动不大于 0.02mm",
        ],
    )
    print("  [OK] GB Frame and Title block added:", frame["paper_size"])

    # 2. Add stepped shaft
    steps = [
        {"d": 25.0, "l": 35.0},
        {"d": 35.0, "l": 50.0},
        {"d": 45.0, "l": 60.0},
        {"d": 35.0, "l": 40.0},
        {"d": 28.0, "l": 30.0},
    ]
    shaft = engine.generate_stepped_shaft(
        origin=(70.0, 150.0),
        steps=steps,
        chamfer_left=1.5,
        chamfer_right=1.5,
        add_centerline=True,
        add_dimensions=True,
    )
    print("  [OK] Parametric Stepped Shaft generated, total length:", shaft["total_length"])

    # 3. Save to DXF
    out_path = os.path.join(CURRENT_DIR, "test_output_shaft.dxf")
    saved = engine.save(out_path)
    print("  [OK] Saved to:", saved)

    # 4. Verify DXF integrity
    doc = ezdxf.readfile(saved)
    entities = list(doc.modelspace())
    print(f"  [OK] Verified DXF validity. Total entities in modelspace: {len(entities)}")
    assert len(entities) > 20, "Expected at least 20 entities in drawing"
    print("CAD Engine Test PASSED!\n")


def test_caxa_controller():
    print("=== Testing CAXA Controller ===")
    ctrl = CAXAController()
    status = ctrl.get_status()
    print("  CAXA Path:", status["caxa_path"])
    print("  CAXA Installed:", status["installed"])
    print("  CAXA Running:", status["is_running"])
    print("  CAXA Window Title:", status["window_title"])
    assert status["installed"], f"CAXA must be installed at {status['caxa_path']}"
    print("CAXA Controller Test PASSED!\n")


if __name__ == "__main__":
    test_cad_engine()
    test_caxa_controller()
    print("ALL TESTS PASSED SUCCESSFULLY!")
