"""
Generator for Experiment 1 Drawing (12 Basic Mechanical Parts on A1 Sheet)
Based on: 《工程图学实验指导书》 实验1 AutoCAD基本绘图专训 12个基本零件图

Optimized for:
1. Standard GB/T Chinese Mechanical Engineering Drawing aesthetics (Clean White, Cyan, Red, Yellow - No harsh magenta/green).
2. Prominent, high-legibility dimension texts (dimtxt=5.0, dimasz=4.0) and leader annotations (height=4.5).
3. Professional title block, technical notes, and dual-output DXF, high-res PNG, and PDF.
"""

import math
import os
import shutil
import sys
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from cad_engine import CADEngine
from caxa_controller import CAXAController
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend


def draw_hatch_rect(engine: CADEngine, p1, p2, spacing=2.5, angle_deg=45.0, layer="5_剖面线"):
    """Draw clean 45-degree section hatch lines inside a rectangle."""
    x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
    x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return

    c_min = x1 - y2
    c_max = x2 - y1
    diag_step = spacing * math.sqrt(2)

    c = c_min + diag_step / 2.0
    while c < c_max:
        pts = []
        y = x1 - c
        if y1 <= y <= y2:
            pts.append((x1, y))
        y = x2 - c
        if y1 <= y <= y2:
            pts.append((x2, y))
        x = y1 + c
        if x1 <= x <= x2:
            pts.append((x, y1))
        x = y2 + c
        if x1 <= x <= x2:
            pts.append((x, y2))

        uniq = []
        for p in pts:
            if not any(math.isclose(p[0], u[0], abs_tol=1e-3) and math.isclose(p[1], u[1], abs_tol=1e-3) for u in uniq):
                uniq.append(p)

        if len(uniq) >= 2:
            engine.add_line(uniq[0], uniq[1], layer=layer)

        c += diag_step


def generate_experiment_1():
    print("=== Generating Experiment 1: 12 Basic Mechanical Parts on A1 Sheet ===")
    engine = CADEngine()

    # 1. A1 Sheet setup (841 x 594 mm)
    w, h = 841.0, 594.0
    ml, mo = 25.0, 10.0
    x_min, y_min = ml, mo
    x_max, y_max = w - mo, h - mo

    # Sheet borders (Standard GB White/High Contrast)
    engine.add_rectangle((0, 0), (w, h), layer="7_图框标题栏")
    engine.add_rectangle((x_min, y_min), (x_max, y_max), layer="7_图框标题栏")

    # 2. Main Sheet Title (Centered at top)
    header_y = y_max - 20.0
    engine.add_text(
        "实验1 AutoCAD基本绘图专训   12个基本零件图",
        (w / 2.0, header_y),
        height=10.0,
        align="CENTER",
        layer="7_图框标题栏",
    )

    # 3. Bottom Block: Technical Requirements & Title Block
    footer_h = 42.0
    footer_top_y = y_min + footer_h
    engine.add_line((x_min, footer_top_y), (x_max, footer_top_y), layer="7_图框标题栏")

    # Divider between Technical Requirements and Title Block
    tb_w = 260.0
    tb_left_x = x_max - tb_w
    engine.add_line((tb_left_x, y_min), (tb_left_x, footer_top_y), layer="7_图框标题栏")

    # Technical Requirements (Left footer)
    engine.add_text("技术要求：", (x_min + 10, footer_top_y - 12), height=4.5, align="LEFT", layer="6_文字说明")
    req_text = "1. 未注尺寸公差按GB/T 1804-c执行；    2. 未注倒角C0.5，未注圆角R0.5；    3. 图中尺寸单位为mm。"
    engine.add_text(req_text, (x_min + 15, footer_top_y - 25), height=4.0, align="LEFT", layer="6_文字说明")

    # Title Block (Right footer: 260mm x 42mm)
    row_h = footer_h / 3.0  # 14mm per row
    y1 = y_min + row_h
    y2 = y_min + row_h * 2
    engine.add_line((tb_left_x, y1), (x_max, y1), layer="1_细实线")
    engine.add_line((tb_left_x, y2), (x_max, y2), layer="1_细实线")

    col_splits = [28.0, 95.0, 140.0, 200.0, 235.0]
    for cs in col_splits:
        engine.add_line((tb_left_x + cs, y_min), (tb_left_x + cs, footer_top_y), layer="1_细实线")

    # Title block texts (Clear White)
    # Row 3 (top row in footer)
    engine.add_text("班级", (tb_left_x + 14, y2 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("设计者", (tb_left_x + 117.5, y2 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("图纸比例", (tb_left_x + 217.5, y2 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("1:1", (tb_left_x + 247.5, y2 + 7), height=4.0, align="CENTER", layer="6_文字说明")

    # Row 2 (middle row)
    engine.add_text("姓名", (tb_left_x + 14, y1 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("审 核", (tb_left_x + 117.5, y1 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("图纸编号", (tb_left_x + 217.5, y1 + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("1-1", (tb_left_x + 247.5, y1 + 7), height=4.0, align="CENTER", layer="6_文字说明")

    # Row 1 (bottom row)
    engine.add_text("日期", (tb_left_x + 14, y_min + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("文件名称", (tb_left_x + 117.5, y_min + 7), height=4.0, align="CENTER", layer="6_文字说明")
    engine.add_text("实验1", (tb_left_x + 170, y_min + 7), height=4.0, align="CENTER", layer="6_文字说明")

    # 4. Grid Setup: 4 Rows x 3 Columns
    grid_top_y = header_y - 12.0  # ~562
    grid_bot_y = footer_top_y     # ~52
    grid_w = x_max - x_min        # 806.0
    grid_h = grid_top_y - grid_bot_y  # 510.0

    col_w = grid_w / 3.0          # 268.67
    row_h = grid_h / 4.0          # 127.5

    # Draw grid lines (White)
    for c in range(1, 3):
        gx = x_min + c * col_w
        engine.add_line((gx, grid_bot_y), (gx, grid_top_y), layer="7_图框标题栏")
    for r in range(1, 4):
        gy = grid_bot_y + r * row_h
        engine.add_line((x_min, gy), (x_max, gy), layer="7_图框标题栏")
    engine.add_line((x_min, grid_top_y), (x_max, grid_top_y), layer="7_图框标题栏")

    def get_cell(row_idx, col_idx):
        left_x = x_min + col_idx * col_w
        right_x = left_x + col_w
        top_y = grid_top_y - row_idx * row_h
        bot_y = top_y - row_h
        center_x = (left_x + right_x) / 2.0
        center_y = (top_y + bot_y) / 2.0
        return {
            "left": left_x,
            "right": right_x,
            "top": top_y,
            "bot": bot_y,
            "cx": center_x,
            "cy": center_y,
        }

    # =============================================================
    # PART 01: 01 垫板 (Row 0, Col 0)
    # =============================================================
    c01 = get_cell(0, 0)
    engine.add_text("01  垫板", (c01["left"] + 8, c01["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p1_cx = c01["cx"] - 35.0
    p1_cy = c01["cy"] - 5.0
    # Left View: 80 x 50 Plate with 4-Φ10 holes (center distance 50 x 30)
    engine.add_rectangle((p1_cx - 40, p1_cy - 25), (p1_cx + 40, p1_cy + 25), layer="0_粗实线")
    engine.add_centerline((p1_cx - 46, p1_cy), (p1_cx + 46, p1_cy))
    engine.add_centerline((p1_cx, p1_cy - 31), (p1_cx, p1_cy + 31))
    for hx, hy in [(-25, 15), (25, 15), (-25, -15), (25, -15)]:
        engine.add_circle((p1_cx + hx, p1_cy + hy), 5.0, add_centerline=True)
    # Dimensions for Left View
    engine.add_dimension_linear((p1_cx - 25, p1_cy - 25), (p1_cx + 25, p1_cy - 25), offset=-14, dim_type="HORIZONTAL", override_text="50")
    engine.add_dimension_linear((p1_cx - 40, p1_cy - 25), (p1_cx + 40, p1_cy - 25), offset=-24, dim_type="HORIZONTAL", override_text="80")
    engine.add_dimension_linear((p1_cx - 40, p1_cy - 15), (p1_cx - 40, p1_cy + 15), offset=-14, dim_type="VERTICAL", override_text="30")
    engine.add_dimension_linear((p1_cx - 40, p1_cy - 25), (p1_cx - 40, p1_cy + 25), offset=-24, dim_type="VERTICAL", override_text="50")
    # Leader for 4xΦ10
    engine.add_line((p1_cx + 25, p1_cy + 15), (p1_cx + 42, p1_cy + 32), layer="4_尺寸标注")
    engine.add_line((p1_cx + 42, p1_cy + 32), (p1_cx + 65, p1_cy + 32), layer="4_尺寸标注")
    engine.add_text("4×Φ10", (p1_cx + 43, p1_cy + 33), height=4.5, layer="6_文字说明")

    # Right Section View: 10 x 50
    p1_rx = c01["cx"] + 65.0
    p1_ry = p1_cy
    engine.add_rectangle((p1_rx - 5, p1_ry - 25), (p1_rx + 5, p1_ry + 25), layer="0_粗实线")
    for hy in [15, -15]:
        engine.add_line((p1_rx - 5, p1_ry + hy - 5), (p1_rx + 5, p1_ry + hy - 5), layer="0_粗实线")
        engine.add_line((p1_rx - 5, p1_ry + hy + 5), (p1_rx + 5, p1_ry + hy + 5), layer="0_粗实线")
        engine.add_centerline((p1_rx - 8, p1_ry + hy), (p1_rx + 8, p1_ry + hy))
    draw_hatch_rect(engine, (p1_rx - 5, p1_ry + 20), (p1_rx + 5, p1_ry + 25))
    draw_hatch_rect(engine, (p1_rx - 5, p1_ry - 10), (p1_rx + 5, p1_ry + 10))
    draw_hatch_rect(engine, (p1_rx - 5, p1_ry - 25), (p1_rx + 5, p1_ry - 20))
    engine.add_dimension_linear((p1_rx - 5, p1_ry - 25), (p1_rx + 5, p1_ry - 25), offset=-14, dim_type="HORIZONTAL", override_text="10")

    # =============================================================
    # PART 02: 02 阶梯轴 (Row 0, Col 1)
    # =============================================================
    c02 = get_cell(0, 1)
    engine.add_text("02  阶梯轴", (c02["left"] + 8, c02["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p2_ox = c02["cx"] - 65.0
    p2_oy = c02["cy"] - 5.0
    engine.add_centerline((p2_ox - 10, p2_oy), (p2_ox + 100, p2_oy))
    engine.add_rectangle((p2_ox, p2_oy - 20), (p2_ox + 40, p2_oy + 20))
    engine.add_rectangle((p2_ox + 40, p2_oy - 15), (p2_ox + 70, p2_oy + 15))
    engine.add_line((p2_ox + 70, p2_oy + 10), (p2_ox + 88, p2_oy + 10))
    engine.add_line((p2_ox + 88, p2_oy + 10), (p2_ox + 90, p2_oy + 8))
    engine.add_line((p2_ox + 90, p2_oy + 8), (p2_ox + 90, p2_oy - 8))
    engine.add_line((p2_ox + 90, p2_oy - 8), (p2_ox + 88, p2_oy - 10))
    engine.add_line((p2_ox + 88, p2_oy - 10), (p2_ox + 70, p2_oy - 10))
    engine.add_line((p2_ox + 88, p2_oy + 10), (p2_ox + 88, p2_oy - 10), layer="1_细实线")

    engine.add_dimension_linear((p2_ox, p2_oy - 20), (p2_ox, p2_oy + 20), offset=-16, dim_type="VERTICAL", override_text="Φ40")
    engine.add_dimension_linear((p2_ox + 70, p2_oy - 15), (p2_ox + 70, p2_oy + 15), offset=-10, dim_type="VERTICAL", override_text="Φ30")
    engine.add_dimension_linear((p2_ox, p2_oy - 20), (p2_ox + 40, p2_oy - 20), offset=-12, dim_type="HORIZONTAL", override_text="40")
    engine.add_dimension_linear((p2_ox + 40, p2_oy - 20), (p2_ox + 70, p2_oy - 20), offset=-12, dim_type="HORIZONTAL", override_text="30")
    engine.add_dimension_linear((p2_ox + 70, p2_oy - 20), (p2_ox + 90, p2_oy - 20), offset=-12, dim_type="HORIZONTAL", override_text="20")
    engine.add_dimension_linear((p2_ox, p2_oy - 20), (p2_ox + 90, p2_oy - 20), offset=-24, dim_type="HORIZONTAL", override_text="90")
    # Chamfer leader
    engine.add_line((p2_ox + 89, p2_oy + 9), (p2_ox + 100, p2_oy + 24), layer="4_尺寸标注")
    engine.add_line((p2_ox + 100, p2_oy + 24), (p2_ox + 122, p2_oy + 24), layer="4_尺寸标注")
    engine.add_text("2×45°", (p2_ox + 101, p2_oy + 25), height=4.5, layer="6_文字说明")

    # =============================================================
    # PART 03: 03 角支架 (Row 0, Col 2)
    # =============================================================
    c03 = get_cell(0, 2)
    engine.add_text("03  角支架", (c03["left"] + 8, c03["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p3_ox = c03["cx"] - 45.0
    p3_oy = c03["cy"] - 25.0
    pts = [
        (p3_ox, p3_oy + 5),
        (p3_ox, p3_oy + 60),
        (p3_ox + 30, p3_oy + 60),
        (p3_ox + 30, p3_oy + 20),
        (p3_ox + 60, p3_oy + 20),
        (p3_ox + 60, p3_oy + 5),
        (p3_ox + 55, p3_oy),
        (p3_ox + 5, p3_oy),
    ]
    engine.add_polyline(pts, is_closed=True)
    engine.add_arc((p3_ox + 5, p3_oy + 5), 5.0, 180, 270)
    engine.add_arc((p3_ox + 55, p3_oy + 5), 5.0, 270, 360)
    engine.add_circle((p3_ox + 10, p3_oy + 50), 5.0, add_centerline=True)
    engine.add_circle((p3_ox + 20, p3_oy + 50), 5.0, add_centerline=True)
    engine.add_centerline((p3_ox + 2, p3_oy + 50), (p3_ox + 28, p3_oy + 50))
    engine.add_cross_centerlines((p3_ox + 50, p3_oy + 10), 5.0)

    engine.add_dimension_linear((p3_ox, p3_oy), (p3_ox, p3_oy + 60), offset=-15, dim_type="VERTICAL", override_text="60")
    engine.add_dimension_linear((p3_ox, p3_oy), (p3_ox + 60, p3_oy), offset=-14, dim_type="HORIZONTAL", override_text="60")
    engine.add_dimension_linear((p3_ox + 60, p3_oy), (p3_ox + 60, p3_oy + 20), offset=14, dim_type="VERTICAL", override_text="20")
    # Leader for 2xΦ10
    engine.add_line((p3_ox + 20, p3_oy + 50), (p3_ox + 35, p3_oy + 67), layer="4_尺寸标注")
    engine.add_line((p3_ox + 35, p3_oy + 67), (p3_ox + 60, p3_oy + 67), layer="4_尺寸标注")
    engine.add_text("2×Φ10", (p3_ox + 36, p3_oy + 68), height=4.5, layer="6_文字说明")

    # Side view: 10 x 60
    p3_rx = c03["cx"] + 60.0
    engine.add_rectangle((p3_rx - 5, p3_oy), (p3_rx + 5, p3_oy + 60))
    engine.add_line((p3_rx - 5, p3_oy + 45), (p3_rx + 5, p3_oy + 45))
    engine.add_line((p3_rx - 5, p3_oy + 55), (p3_rx + 5, p3_oy + 55))
    engine.add_centerline((p3_rx - 8, p3_oy + 50), (p3_rx + 8, p3_oy + 50))
    engine.add_line((p3_rx - 5, p3_oy + 5), (p3_rx + 5, p3_oy + 5))
    engine.add_line((p3_rx - 5, p3_oy + 15), (p3_rx + 5, p3_oy + 15))
    engine.add_centerline((p3_rx - 8, p3_oy + 10), (p3_rx + 8, p3_oy + 10))
    draw_hatch_rect(engine, (p3_rx - 5, p3_oy + 15), (p3_rx + 5, p3_oy + 45))
    draw_hatch_rect(engine, (p3_rx - 5, p3_oy + 55), (p3_rx + 5, p3_oy + 60))
    draw_hatch_rect(engine, (p3_rx - 5, p3_oy), (p3_rx + 5, p3_oy + 5))
    engine.add_dimension_linear((p3_rx - 5, p3_oy), (p3_rx + 5, p3_oy), offset=-14, dim_type="HORIZONTAL", override_text="10")

    # =============================================================
    # PART 04: 04 台阶块 (Row 1, Col 0)
    # =============================================================
    c04 = get_cell(1, 0)
    engine.add_text("04  台阶块", (c04["left"] + 8, c04["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p4_ox = c04["cx"] - 60.0
    p4_oy = c04["cy"] - 20.0
    step_pts = [
        (p4_ox, p4_oy),
        (p4_ox + 100, p4_oy),
        (p4_ox + 100, p4_oy + 30),
        (p4_ox + 60, p4_oy + 30),
        (p4_ox + 60, p4_oy + 50),
        (p4_ox, p4_oy + 50),
    ]
    engine.add_polyline(step_pts, is_closed=True)
    engine.add_rectangle((p4_ox + 15, p4_oy + 22), (p4_ox + 50, p4_oy + 37), layer="3_虚线")
    engine.add_centerline((p4_ox + 10, p4_oy + 29.5), (p4_ox + 55, p4_oy + 29.5))

    engine.add_dimension_linear((p4_ox, p4_oy), (p4_ox, p4_oy + 50), offset=-15, dim_type="VERTICAL", override_text="50")
    engine.add_dimension_linear((p4_ox + 100, p4_oy), (p4_ox + 100, p4_oy + 30), offset=10, dim_type="VERTICAL", override_text="30")
    engine.add_dimension_linear((p4_ox, p4_oy), (p4_ox + 100, p4_oy), offset=-14, dim_type="HORIZONTAL", override_text="100")

    # Side view: 20 x 50
    p4_rx = c04["cx"] + 80.0
    engine.add_rectangle((p4_rx - 10, p4_oy), (p4_rx + 10, p4_oy + 50))
    engine.add_line((p4_rx - 10, p4_oy + 22), (p4_rx, p4_oy + 22), layer="3_虚线")
    engine.add_line((p4_rx - 10, p4_oy + 37), (p4_rx, p4_oy + 37), layer="3_虚线")
    engine.add_line((p4_rx, p4_oy + 22), (p4_rx, p4_oy + 37), layer="3_虚线")
    draw_hatch_rect(engine, (p4_rx - 10, p4_oy + 37), (p4_rx + 10, p4_oy + 50))
    draw_hatch_rect(engine, (p4_rx - 10, p4_oy), (p4_rx + 10, p4_oy + 22))
    draw_hatch_rect(engine, (p4_rx, p4_oy + 22), (p4_rx + 10, p4_oy + 37))
    engine.add_dimension_linear((p4_rx - 10, p4_oy), (p4_rx + 10, p4_oy), offset=-14, dim_type="HORIZONTAL", override_text="20")

    # =============================================================
    # PART 05: 05 法兰盘 (Row 1, Col 1)
    # =============================================================
    c05 = get_cell(1, 1)
    engine.add_text("05  法兰盘", (c05["left"] + 8, c05["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p5_cx = c05["cx"] - 35.0
    p5_cy = c05["cy"] - 5.0
    engine.add_circle((p5_cx, p5_cy), 40.0)
    engine.add_circle((p5_cx, p5_cy), 15.0)
    engine.add_circle((p5_cx, p5_cy), 28.0, layer="2_中心线")
    engine.add_cross_centerlines((p5_cx, p5_cy), 45.0)
    for ang in [0, 90, 180, 270]:
        rad = math.radians(ang)
        bx = p5_cx + 28.0 * math.cos(rad)
        by = p5_cy + 28.0 * math.sin(rad)
        engine.add_circle((bx, by), 5.0, add_centerline=True)

    engine.add_dimension_diameter((p5_cx, p5_cy), 40.0, angle_deg=45, override_text="Φ80")
    engine.add_line((p5_cx + 28 * math.cos(math.radians(45)), p5_cy + 28 * math.sin(math.radians(45))), (p5_cx + 46, p5_cy + 46), layer="4_尺寸标注")
    engine.add_line((p5_cx + 46, p5_cy + 46), (p5_cx + 70, p5_cy + 46), layer="4_尺寸标注")
    engine.add_text("4×Φ10", (p5_cx + 47, p5_cy + 47), height=4.5, layer="6_文字说明")

    # Side view
    p5_rx = c05["cx"] + 65.0
    engine.add_rectangle((p5_rx - 10, p5_cy - 40), (p5_rx, p5_cy + 40))
    engine.add_rectangle((p5_rx, p5_cy - 25), (p5_rx + 10, p5_cy + 25))
    engine.add_centerline((p5_rx - 15, p5_cy), (p5_rx + 15, p5_cy))
    engine.add_line((p5_rx - 10, p5_cy - 15), (p5_rx + 10, p5_cy - 15), layer="3_虚线")
    engine.add_line((p5_rx - 10, p5_cy + 15), (p5_rx + 10, p5_cy + 15), layer="3_虚线")
    engine.add_dimension_linear((p5_rx - 10, p5_cy + 40), (p5_rx + 10, p5_cy + 40), offset=14, dim_type="HORIZONTAL", override_text="20")
    engine.add_dimension_linear((p5_rx - 10, p5_cy - 40), (p5_rx, p5_cy - 40), offset=-14, dim_type="HORIZONTAL", override_text="10")
    engine.add_dimension_linear((p5_rx - 10, p5_cy - 15), (p5_rx - 10, p5_cy + 15), offset=-14, dim_type="VERTICAL", override_text="Φ30")

    # =============================================================
    # PART 06: 06 带轮 (Row 1, Col 2)
    # =============================================================
    c06 = get_cell(1, 2)
    engine.add_text("06  带轮", (c06["left"] + 8, c06["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p6_cx = c06["cx"] - 35.0
    p6_cy = c06["cy"] - 8.0
    engine.add_circle((p6_cx, p6_cy), 40.0)
    engine.add_circle((p6_cx, p6_cy), 25.0)
    engine.add_circle((p6_cx, p6_cy), 10.0)
    engine.add_cross_centerlines((p6_cx, p6_cy), 45.0)
    engine.add_dimension_diameter((p6_cx, p6_cy), 40.0, angle_deg=45, override_text="Φ80")
    engine.add_dimension_diameter((p6_cx, p6_cy), 25.0, angle_deg=30, override_text="Φ50")
    engine.add_dimension_diameter((p6_cx, p6_cy), 10.0, angle_deg=345, override_text="Φ20")

    # Side view
    p6_rx = c06["cx"] + 65.0
    engine.add_line((p6_rx - 15, p6_cy - 40), (p6_rx + 15, p6_cy - 40))
    engine.add_line((p6_rx - 15, p6_cy + 40), (p6_rx + 15, p6_cy + 40))
    engine.add_line((p6_rx - 15, p6_cy - 40), (p6_rx - 15, p6_cy + 40))
    engine.add_line((p6_rx + 15, p6_cy - 40), (p6_rx + 15, p6_cy + 40))
    engine.add_arc((p6_rx, p6_cy + 40), 5.0, 180, 360)
    engine.add_arc((p6_rx, p6_cy - 40), 5.0, 0, 180)
    engine.add_centerline((p6_rx - 20, p6_cy), (p6_rx + 20, p6_cy))
    engine.add_centerline((p6_rx, p6_cy - 45), (p6_rx, p6_cy + 45))
    engine.add_dimension_linear((p6_rx - 15, p6_cy + 40), (p6_rx + 15, p6_cy + 40), offset=12, dim_type="HORIZONTAL", override_text="30")
    engine.add_dimension_linear((p6_rx - 5, p6_cy + 40), (p6_rx + 5, p6_cy + 40), offset=6, dim_type="HORIZONTAL", override_text="10")
    engine.add_dimension_linear((p6_rx + 15, p6_cy - 40), (p6_rx + 15, p6_cy + 40), offset=14, dim_type="VERTICAL", override_text="Φ80")

    # =============================================================
    # PART 07: 07 平键 (Row 2, Col 0)
    # =============================================================
    c07 = get_cell(2, 0)
    engine.add_text("07  平键", (c07["left"] + 8, c07["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p7_ox = c07["cx"] - 60.0
    p7_oy = c07["cy"] - 5.0
    engine.add_line((p7_ox, p7_oy - 8), (p7_ox, p7_oy + 8))
    engine.add_line((p7_ox, p7_oy + 8), (p7_ox + 56, p7_oy + 8))
    engine.add_line((p7_ox, p7_oy - 8), (p7_ox + 56, p7_oy - 8))
    engine.add_arc((p7_ox + 56, p7_oy + 4), 4.0, 0, 90)
    engine.add_arc((p7_ox + 56, p7_oy - 4), 4.0, 270, 360)
    engine.add_line((p7_ox + 60, p7_oy + 4), (p7_ox + 60, p7_oy - 4))
    engine.add_centerline((p7_ox - 5, p7_oy), (p7_ox + 65, p7_oy))
    engine.add_dimension_linear((p7_ox, p7_oy - 8), (p7_ox, p7_oy + 8), offset=-15, dim_type="VERTICAL", override_text="16")
    engine.add_dimension_linear((p7_ox, p7_oy - 8), (p7_ox + 60, p7_oy - 8), offset=-14, dim_type="HORIZONTAL", override_text="60")
    engine.add_line((p7_ox + 58, p7_oy + 7), (p7_ox + 67, p7_oy + 20), layer="4_尺寸标注")
    engine.add_line((p7_ox + 67, p7_oy + 20), (p7_ox + 82, p7_oy + 20), layer="4_尺寸标注")
    engine.add_text("R4", (p7_ox + 68, p7_oy + 21), height=4.5, layer="6_文字说明")

    # Right cross section
    p7_rx = c07["cx"] + 65.0
    engine.add_line((p7_rx - 8, p7_oy - 8), (p7_rx + 8, p7_oy - 8))
    engine.add_line((p7_rx + 8, p7_oy - 8), (p7_rx + 8, p7_oy + 8))
    engine.add_line((p7_rx + 8, p7_oy + 8), (p7_rx - 4, p7_oy + 8))
    engine.add_line((p7_rx - 8, p7_oy + 4), (p7_rx - 8, p7_oy - 8))
    engine.add_arc((p7_rx - 4, p7_oy + 4), 4.0, 90, 180)
    draw_hatch_rect(engine, (p7_rx - 8, p7_oy - 8), (p7_rx + 8, p7_oy + 8))
    engine.add_dimension_linear((p7_rx - 8, p7_oy - 8), (p7_rx + 8, p7_oy - 8), offset=-14, dim_type="HORIZONTAL", override_text="16")
    engine.add_dimension_linear((p7_rx + 8, p7_oy - 8), (p7_rx + 8, p7_oy + 8), offset=14, dim_type="VERTICAL", override_text="16")

    # =============================================================
    # PART 08: 08 六角螺栓 (Row 2, Col 1)
    # =============================================================
    c08 = get_cell(2, 1)
    engine.add_text("08  六角螺栓", (c08["left"] + 8, c08["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p8_ox = c08["cx"] - 70.0
    p8_oy = c08["cy"] - 5.0
    engine.add_centerline((p8_ox - 5, p8_oy), (p8_ox + 95, p8_oy))
    engine.add_rectangle((p8_ox, p8_oy - 12), (p8_ox + 10, p8_oy + 12))
    engine.add_rectangle((p8_ox + 10, p8_oy - 8), (p8_ox + 90, p8_oy + 8))
    engine.add_line((p8_ox + 88, p8_oy - 8), (p8_ox + 88, p8_oy + 8), layer="1_细实线")
    engine.add_line((p8_ox + 15, p8_oy - 6.5), (p8_ox + 88, p8_oy - 6.5), layer="1_细实线")
    engine.add_line((p8_ox + 15, p8_oy + 6.5), (p8_ox + 88, p8_oy + 6.5), layer="1_细实线")

    engine.add_dimension_linear((p8_ox, p8_oy - 12), (p8_ox + 10, p8_oy - 12), offset=-14, dim_type="HORIZONTAL", override_text="10")
    engine.add_dimension_linear((p8_ox + 10, p8_oy - 12), (p8_ox + 90, p8_oy - 12), offset=-14, dim_type="HORIZONTAL", override_text="80")
    engine.add_dimension_linear((p8_ox + 90, p8_oy - 8), (p8_ox + 90, p8_oy + 8), offset=14, dim_type="VERTICAL", override_text="M16")

    # Right Hexagon view
    p8_rx = c08["cx"] + 65.0
    r_hex = 12.0 / math.cos(math.radians(30))
    hex_pts = [(p8_rx + r_hex * math.cos(math.radians(60 * i + 30)), p8_oy + r_hex * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    engine.add_polyline(hex_pts, is_closed=True)
    engine.add_circle((p8_rx, p8_oy), 12.0, layer="1_细实线")
    engine.add_cross_centerlines((p8_rx, p8_oy), 16.0)
    engine.add_dimension_linear((p8_rx - 12, p8_oy - 12), (p8_rx + 12, p8_oy - 12), offset=-14, dim_type="HORIZONTAL", override_text="24")

    # =============================================================
    # PART 09: 09 六角螺母 (Row 2, Col 2)
    # =============================================================
    c09 = get_cell(2, 2)
    engine.add_text("09  六角螺母", (c09["left"] + 8, c09["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p9_ox = c09["cx"] - 45.0
    p9_oy = c09["cy"] - 10.0
    engine.add_rectangle((p9_ox - 6, p9_oy - 12), (p9_ox + 6, p9_oy + 12))
    engine.add_centerline((p9_ox - 10, p9_oy), (p9_ox + 10, p9_oy))
    engine.add_line((p9_ox - 6, p9_oy - 8), (p9_ox + 6, p9_oy - 8), layer="3_虚线")
    engine.add_line((p9_ox - 6, p9_oy + 8), (p9_ox + 6, p9_oy + 8), layer="3_虚线")
    engine.add_dimension_linear((p9_ox - 6, p9_oy - 12), (p9_ox + 6, p9_oy - 12), offset=-14, dim_type="HORIZONTAL", override_text="12")
    engine.add_dimension_linear((p9_ox + 6, p9_oy - 8), (p9_ox + 6, p9_oy + 8), offset=14, dim_type="VERTICAL", override_text="M16")

    # Right Hexagon view
    p9_rx = c09["cx"] + 45.0
    hex_pts9 = [(p9_rx + r_hex * math.cos(math.radians(60 * i + 30)), p9_oy + r_hex * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    engine.add_polyline(hex_pts9, is_closed=True)
    engine.add_circle((p9_rx, p9_oy), 8.0)
    engine.add_arc((p9_rx, p9_oy), 6.5, 30, 330, layer="1_细实线")
    engine.add_cross_centerlines((p9_rx, p9_oy), 16.0)
    engine.add_dimension_linear((p9_rx - 12, p9_oy - 12), (p9_rx + 12, p9_oy - 12), offset=-14, dim_type="HORIZONTAL", override_text="24")

    # =============================================================
    # PART 10: 10 隔套 (Row 3, Col 0)
    # =============================================================
    c10 = get_cell(3, 0)
    engine.add_text("10  隔套", (c10["left"] + 8, c10["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p10_ox = c10["cx"] - 50.0
    p10_oy = c10["cy"] - 5.0
    engine.add_centerline((p10_ox - 8, p10_oy), (p10_ox + 68, p10_oy))
    engine.add_line((p10_ox, p10_oy - 20), (p10_ox, p10_oy + 20))
    engine.add_line((p10_ox, p10_oy + 20), (p10_ox + 59, p10_oy + 20))
    engine.add_line((p10_ox + 59, p10_oy + 20), (p10_ox + 60, p10_oy + 19))
    engine.add_line((p10_ox + 60, p10_oy + 19), (p10_ox + 60, p10_oy - 19))
    engine.add_line((p10_ox + 60, p10_oy - 19), (p10_ox + 59, p10_oy - 20))
    engine.add_line((p10_ox + 59, p10_oy - 20), (p10_ox, p10_oy - 20))
    engine.add_line((p10_ox, p10_oy + 14), (p10_ox + 60, p10_oy + 14))
    engine.add_line((p10_ox, p10_oy - 14), (p10_ox + 60, p10_oy - 14))
    draw_hatch_rect(engine, (p10_ox, p10_oy + 14), (p10_ox + 59, p10_oy + 20))
    draw_hatch_rect(engine, (p10_ox, p10_oy - 20), (p10_ox + 59, p10_oy - 14))

    engine.add_dimension_linear((p10_ox, p10_oy - 20), (p10_ox, p10_oy + 20), offset=-18, dim_type="VERTICAL", override_text="Φ40")
    engine.add_dimension_linear((p10_ox, p10_oy - 14), (p10_ox, p10_oy + 14), offset=-10, dim_type="VERTICAL", override_text="Φ28")
    engine.add_dimension_linear((p10_ox, p10_oy - 20), (p10_ox + 60, p10_oy - 20), offset=-14, dim_type="HORIZONTAL", override_text="60")
    # Chamfer leader
    engine.add_line((p10_ox + 59.5, p10_oy + 19.5), (p10_ox + 69, p10_oy + 30), layer="4_尺寸标注")
    engine.add_line((p10_ox + 69, p10_oy + 30), (p10_ox + 90, p10_oy + 30), layer="4_尺寸标注")
    engine.add_text("1×45°", (p10_ox + 70, p10_oy + 31), height=4.5, layer="6_文字说明")

    # Right View
    p10_rx = c10["cx"] + 60.0
    engine.add_circle((p10_rx, p10_oy), 20.0)
    engine.add_circle((p10_rx, p10_oy), 14.0)
    engine.add_cross_centerlines((p10_rx, p10_oy), 24.0)

    # =============================================================
    # PART 11: 11 轴承座 (Row 3, Col 1)
    # =============================================================
    c11 = get_cell(3, 1)
    engine.add_text("11  轴承座", (c11["left"] + 8, c11["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p11_ox = c11["cx"] - 35.0
    p11_oy = c11["cy"] - 25.0
    engine.add_rectangle((p11_ox - 60, p11_oy), (p11_ox + 60, p11_oy + 15))
    for hx in [-50, 50]:
        engine.add_line((p11_ox + hx - 5.5, p11_oy), (p11_ox + hx - 5.5, p11_oy + 15), layer="3_虚线")
        engine.add_line((p11_ox + hx + 5.5, p11_oy), (p11_ox + hx + 5.5, p11_oy + 15), layer="3_虚线")
        engine.add_centerline((p11_ox + hx, p11_oy - 4), (p11_ox + hx, p11_oy + 19))
    hc_y = p11_oy + 35.0
    engine.add_arc((p11_ox, hc_y), 20.0, 0, 180)
    engine.add_circle((p11_ox, hc_y), 10.0)
    engine.add_cross_centerlines((p11_ox, hc_y), 25.0)
    engine.add_line((p11_ox - 20, hc_y), (p11_ox - 35, p11_oy + 15))
    engine.add_line((p11_ox + 20, hc_y), (p11_ox + 35, p11_oy + 15))

    engine.add_dimension_linear((p11_ox - 50, p11_oy), (p11_ox + 50, p11_oy), offset=-14, dim_type="HORIZONTAL", override_text="100")
    engine.add_dimension_linear((p11_ox - 60, p11_oy), (p11_ox + 60, p11_oy), offset=-24, dim_type="HORIZONTAL", override_text="120")
    engine.add_dimension_linear((p11_ox + 60, p11_oy), (p11_ox + 60, hc_y + 20), offset=14, dim_type="VERTICAL", override_text="70")
    engine.add_dimension_diameter((p11_ox, hc_y), 20.0, angle_deg=45, override_text="Φ40")
    engine.add_dimension_diameter((p11_ox, hc_y), 10.0, angle_deg=135, override_text="Φ20")

    # Side view
    p11_rx = c11["cx"] + 65.0
    engine.add_rectangle((p11_rx - 15, p11_oy), (p11_rx + 15, p11_oy + 15))
    engine.add_rectangle((p11_rx - 7.5, p11_oy + 15), (p11_rx + 7.5, hc_y + 20))
    engine.add_centerline((p11_rx - 12, hc_y), (p11_rx + 12, hc_y))
    engine.add_line((p11_rx - 7.5, hc_y - 10), (p11_rx + 7.5, hc_y - 10), layer="3_虚线")
    engine.add_line((p11_rx - 7.5, hc_y + 10), (p11_rx + 7.5, hc_y + 10), layer="3_虚线")
    engine.add_dimension_linear((p11_rx - 15, p11_oy), (p11_rx + 15, p11_oy), offset=-14, dim_type="HORIZONTAL", override_text="30")
    engine.add_dimension_linear((p11_rx - 7.5, hc_y + 20), (p11_rx + 7.5, hc_y + 20), offset=12, dim_type="HORIZONTAL", override_text="15")
    engine.add_dimension_linear((p11_rx + 15, p11_oy), (p11_rx + 15, hc_y), offset=14, dim_type="VERTICAL", override_text="35")

    # =============================================================
    # PART 12: 12 端盖 (Row 3, Col 2)
    # =============================================================
    c12 = get_cell(3, 2)
    engine.add_text("12  端盖", (c12["left"] + 8, c12["top"] - 14), height=6.5, align="LEFT", layer="7_图框标题栏")
    p12_cx = c12["cx"] - 35.0
    p12_cy = c12["cy"] - 10.0
    engine.add_circle((p12_cx, p12_cy), 50.0)
    engine.add_circle((p12_cx, p12_cy), 22.5)
    engine.add_circle((p12_cx, p12_cy), 37.5, layer="2_中心线")
    engine.add_cross_centerlines((p12_cx, p12_cy), 55.0)
    for i in range(8):
        ang = 45.0 * i
        rad = math.radians(ang)
        bx = p12_cx + 37.5 * math.cos(rad)
        by = p12_cy + 37.5 * math.sin(rad)
        engine.add_circle((bx, by), 4.0, add_centerline=True)
    engine.add_dimension_diameter((p12_cx, p12_cy), 50.0, angle_deg=35, override_text="Φ100")
    # Leader for 8xΦ10 (standard 8 holes on PCD 75)
    engine.add_line((p12_cx + 37.5 * math.cos(math.radians(45)), p12_cy + 37.5 * math.sin(math.radians(45))), (p12_cx + 46, p12_cy + 46), layer="4_尺寸标注")
    engine.add_line((p12_cx + 46, p12_cy + 46), (p12_cx + 72, p12_cy + 46), layer="4_尺寸标注")
    engine.add_text("8×Φ10", (p12_cx + 47, p12_cy + 47), height=4.5, layer="6_文字说明")

    # Side Section View
    p12_rx = c12["cx"] + 65.0
    engine.add_rectangle((p12_rx - 7.5, p12_cy - 50), (p12_rx + 7.5, p12_cy + 50))
    engine.add_line((p12_rx - 7.5, p12_cy - 22.5), (p12_rx + 7.5, p12_cy - 22.5))
    engine.add_line((p12_rx - 7.5, p12_cy + 22.5), (p12_rx + 7.5, p12_cy + 22.5))
    engine.add_centerline((p12_rx - 12, p12_cy), (p12_rx + 12, p12_cy))
    for hy in [-37.5, 37.5]:
        engine.add_line((p12_rx - 7.5, p12_cy + hy - 4), (p12_rx + 7.5, p12_cy + hy - 4))
        engine.add_line((p12_rx - 7.5, p12_cy + hy + 4), (p12_rx + 7.5, p12_cy + hy + 4))
        engine.add_centerline((p12_rx - 10, p12_cy + hy), (p12_rx + 10, p12_cy + hy))
    draw_hatch_rect(engine, (p12_rx - 7.5, p12_cy + 41.5), (p12_rx + 7.5, p12_cy + 50))
    draw_hatch_rect(engine, (p12_rx - 7.5, p12_cy + 22.5), (p12_rx + 7.5, p12_cy + 33.5))
    draw_hatch_rect(engine, (p12_rx - 7.5, p12_cy - 33.5), (p12_rx + 7.5, p12_cy - 22.5))
    draw_hatch_rect(engine, (p12_rx - 7.5, p12_cy - 50), (p12_rx + 7.5, p12_cy - 41.5))
    engine.add_dimension_linear((p12_rx - 7.5, p12_cy + 50), (p12_rx + 7.5, p12_cy + 50), offset=8, dim_type="HORIZONTAL", override_text="15")

    # 5. Save Drawing Files
    out_dir = os.path.abspath(os.path.join(CURRENT_DIR, "output"))
    os.makedirs(out_dir, exist_ok=True)
    out_dxf = os.path.join(out_dir, "实验1_AutoCAD基本绘图专训_12个基本零件图.dxf")
    saved_path = engine.save(out_dxf)
    print(f"Drawing saved to: {saved_path}")

    # Optional local copy
    try:
        shutil.copyfile(saved_path, os.path.join(CURRENT_DIR, "exp1.dxf"))
    except Exception:
        pass

    # Optional custom directory if provided via environment variable
    custom_target_dir = os.environ.get("CAXA_OUTPUT_DIR")
    if custom_target_dir and os.path.isdir(custom_target_dir):
        try:
            shutil.copyfile(saved_path, os.path.join(custom_target_dir, "实验1_AutoCAD基本绘图专训_12个基本零件图.dxf"))
        except Exception:
            pass

    # 6. High-Res Rendering (PNG & PDF)
    print("Rendering high-res CAD preview images and PDF...")
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        doc = ezdxf.readfile(saved_path)
        msp = doc.modelspace()

        # Render High-Res PNG (Dark CAD background #181b20 for optimum contrast)
        fig = plt.figure(figsize=(28, 19.8), dpi=200)
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)

        png_f = os.path.join(out_dir, "实验1_12个基本零件图_高清效果图.png")
        fig.savefig(png_f, dpi=200, facecolor='#181b20')
        print(f"Saved PNG to: {png_f}")

        # Also save A1 PDF
        pdf_f = os.path.join(out_dir, "实验1_12个基本零件图.pdf")
        fig.savefig(pdf_f, format='pdf', facecolor='#181b20')
        print(f"Saved PDF to: {pdf_f}")
        plt.close(fig)
    except Exception as e:
        print(f"Rendering error: {e}")

    # 7. Open in CAXA CAD
    try:
        controller = CAXAController()
        if controller.is_installed:
            print("Opening in CAXA CAD 2023...")
            controller.open_drawing(saved_path)
            controller.zoom_extents()
            print("Opened in CAXA CAD successfully!")
    except Exception as e:
        print(f"CAXA open notice: {e}")

    return saved_path


if __name__ == "__main__":
    generate_experiment_1()
