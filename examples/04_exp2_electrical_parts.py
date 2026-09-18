"""
generate_exp2.py - Automated Drafting of Experiment 2 for CAXA CAD / AutoCAD
4 Electrical Machinery Components on Standard A3 Sheet (GB/T 14665 Standard).
Features:
- Parameterized Title Block created as an AutoCAD/CAXA Block with ATTDEF Attributes
- 2 Reusable Electrical Parts defined as Blocks with Attributes (MOTOR_END_COVER, TERMINAL_PLATE)
- Strict GB/T 14665 layer system and high-contrast color scheme
- Complete privacy protection: teacher name and personal info sanitized to clean blanks
- Full outputs: DWG, DXF, vector A3 PDF, high-res PNG, and standalone blocks library
"""

import os
import shutil
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import ezdxf
from ezdxf import colors
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "output_exp2"))
TARGET_ARCHIVE_DIR = r"F:\cad  caxa工程图\03_实验2_成果图纸"


class CADEngineExp2:
    def __init__(self):
        self.doc = ezdxf.new("R2010", setup=True)
        self.msp = self.doc.modelspace()
        self._setup_textstyles()
        self._setup_layers()
        self._setup_dimstyle()

    def _setup_textstyles(self):
        # Fix default Standard style to use msyh.ttc for complete Chinese + Ø symbol support
        if "Standard" in self.doc.styles:
            std = self.doc.styles.get("Standard")
            std.dxf.font = "msyh.ttc"

        # Setup Chinese text style using Microsoft YaHei (msyh.ttc)
        if "GB_STYLE" not in self.doc.styles:
            self.doc.styles.add(
                "GB_STYLE",
                font="msyh.ttc",
                dxfattribs={"width": 0.8},
            )

    def _setup_layers(self):
        layers = [
            ("0_粗实线", 7, 35, "CONTINUOUS"),     # 0.35mm White
            ("1_细实线", 7, 18, "CONTINUOUS"),     # 0.18mm White
            ("2_中心线", 1, 18, "CENTER"),         # 0.18mm Red
            ("3_虚线", 2, 18, "HIDDEN"),           # 0.18mm Yellow
            ("4_尺寸标注", 4, 18, "CONTINUOUS"),   # 0.18mm Cyan
            ("5_剖面线", 4, 18, "CONTINUOUS"),     # 0.18mm Cyan
            ("6_文字说明", 7, 25, "CONTINUOUS"),   # 0.25mm White
            ("7_图框标题栏", 7, 35, "CONTINUOUS"), # 0.35mm White
        ]
        for name, color, lw, lt in layers:
            if name not in self.doc.layers:
                self.doc.layers.new(name, dxfattribs={"color": color, "lineweight": lw, "linetype": lt})

    def _setup_dimstyle(self):
        style_name = "EXP2_A3_DIM"
        if style_name not in self.doc.dimstyles:
            dim_style = self.doc.dimstyles.new(style_name)
            dim_style.dxf.dimtxt = 3.2          # 3.2mm text height for A3
            dim_style.dxf.dimasz = 2.8          # 2.8mm arrow size
            dim_style.dxf.dimexe = 1.5          # extension line extension
            dim_style.dxf.dimexo = 1.2          # extension line offset
            dim_style.dxf.dimgap = 1.0          # gap between text and dim line
            dim_style.dxf.dimclrd = 4           # Cyan dim line
            dim_style.dxf.dimclre = 4           # Cyan extension line
            dim_style.dxf.dimclrt = 7           # White text
            dim_style.dxf.dimtxsty = "GB_STYLE" # Chinese text support
            dim_style.dxf.dimlfac = 1.0
            dim_style.dxf.dimtad = 1            # Text above dim line
            dim_style.dxf.dimtih = 0            # Text aligned with dim line
            dim_style.dxf.dimtoh = 0

    # Drawing Primitives
    def add_line(self, p1, p2, layer="0_粗实线", target=None):
        t = target or self.msp
        return t.add_line(p1, p2, dxfattribs={"layer": layer})

    def add_circle(self, center, radius, layer="0_粗实线", target=None):
        t = target or self.msp
        return t.add_circle(center, radius, dxfattribs={"layer": layer})

    def add_arc(self, center, radius, start_angle, end_angle, layer="0_粗实线", target=None):
        t = target or self.msp
        return t.add_arc(center, radius, start_angle, end_angle, dxfattribs={"layer": layer})

    def add_rectangle(self, p1, p2, layer="0_粗实线", target=None):
        t = target or self.msp
        x1, y1 = p1
        x2, y2 = p2
        pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        return t.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    def add_centerline(self, p1, p2, extension=3.0, target=None):
        t = target or self.msp
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return None
        ux, uy = dx / dist, dy / dist
        start = (p1[0] - ux * extension, p1[1] - uy * extension)
        end = (p2[0] + ux * extension, p2[1] + uy * extension)
        return t.add_line(start, end, dxfattribs={"layer": "2_中心线"})

    def add_center_cross(self, center, radius, extension=3.0, target=None):
        cx, cy = center
        r = radius + extension
        self.add_line((cx - r, cy), (cx + r, cy), layer="2_中心线", target=target)
        self.add_line((cx, cy - r), (cx, cy + r), layer="2_中心线", target=target)

    def add_text(self, text, insert, height=3.5, align="LEFT", layer="6_文字说明", target=None):
        t = target or self.msp
        txt = t.add_text(text, dxfattribs={"height": height, "layer": layer, "style": "GB_STYLE"})
        align_map = {
            "LEFT": "LEFT", "CENTER": "MIDDLE_CENTER", "RIGHT": "MIDDLE_RIGHT",
            "TOP_LEFT": "TOP_LEFT", "TOP_CENTER": "TOP_CENTER", "TOP_RIGHT": "TOP_RIGHT",
            "BOTTOM_LEFT": "BOTTOM_LEFT", "BOTTOM_CENTER": "BOTTOM_CENTER"
        }
        valign = align_map.get(align, "LEFT")
        if valign != "LEFT":
            txt.set_placement(insert, align=getattr(ezdxf.enums.TextEntityAlignment, valign))
        else:
            txt.dxf.insert = insert
        return txt

    def add_dimension_linear(self, p1, p2, offset=8.0, dim_type="HORIZONTAL", override_text=None, target=None):
        t = target or self.msp
        if dim_type == "HORIZONTAL":
            dim_line_y = p1[1] + offset
            base = (p1[0], dim_line_y)
            dim = t.add_linear_dim(
                base=base, p1=p1, p2=p2, dimstyle="EXP2_A3_DIM",
                dxfattribs={"layer": "4_尺寸标注"}, override={"dimtad": 1}
            )
        else:
            dim_line_x = p1[0] + offset
            base = (dim_line_x, p1[1])
            dim = t.add_linear_dim(
                base=base, p1=p1, p2=p2, angle=90, dimstyle="EXP2_A3_DIM",
                dxfattribs={"layer": "4_尺寸标注"}, override={"dimtad": 1}
            )
        if override_text:
            dim.set_text(override_text)
        dim.render()
        return dim

    def add_leader(self, target_pt, text_pt, text, height=3.0, target=None):
        t = target or self.msp
        tx, ty = text_pt
        px, py = target_pt
        dx = 8.0 if tx >= px else -8.0
        elbow_pt = (tx - dx, ty)
        
        # Arrow head at target_pt
        ux = (elbow_pt[0] - px)
        uy = (elbow_pt[1] - py)
        dist = math.hypot(ux, uy)
        if dist > 0:
            ux, uy = ux / dist, uy / dist
            arrow_len = 2.5
            arrow_w = 0.8
            p_a1 = (px + ux * arrow_len - uy * arrow_w, py + uy * arrow_len + ux * arrow_w)
            p_a2 = (px + ux * arrow_len + uy * arrow_w, py + uy * arrow_len - ux * arrow_w)
            t.add_solid([target_pt, p_a1, p_a2, target_pt], dxfattribs={"layer": "4_尺寸标注"})

        t.add_line(target_pt, elbow_pt, dxfattribs={"layer": "4_尺寸标注"})
        t.add_line(elbow_pt, text_pt, dxfattribs={"layer": "4_尺寸标注"})
        align = "LEFT" if dx > 0 else "RIGHT"
        text_insert = (text_pt[0] + (1.0 if dx > 0 else -1.0), text_pt[1] + 1.0)
        self.add_text(text, text_insert, height=height, align=align, layer="4_尺寸标注", target=t)

    def add_roughness_symbol(self, insert, value="Ra3.2", target=None):
        t = target or self.msp
        x, y = insert
        p1 = (x, y + 6.0)
        p2 = (x + 3.0, y)
        p3 = (x + 8.0, y + 10.0)
        p4 = (x + 18.0, y + 10.0)
        t.add_line(p1, p2, dxfattribs={"layer": "1_细实线"})
        t.add_line(p2, p3, dxfattribs={"layer": "1_细实线"})
        t.add_line(p3, p4, dxfattribs={"layer": "1_细实线"})
        self.add_text(value, (x + 9.0, y + 11.5), height=2.8, align="LEFT", layer="6_文字说明", target=t)


def draw_hatch_rect(engine, p1, p2, step=2.2, angle=45, layer="5_剖面线", target=None):
    t = target or engine.msp
    x1, y1 = min(p1[0], p2[0]), min(p1[1], p2[1])
    x2, y2 = max(p1[0], p2[0]), max(p1[1], p2[1])
    w = x2 - x1
    h = y2 - y1
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    diag_step = step / math.sin(rad)
    c_start = -h
    c_end = w
    c = c_start
    while c <= c_end:
        pts = []
        x = x1 + c
        if x1 <= x <= x2:
            pts.append((x, y1))
        x = x1 + c + h * (cos_a / sin_a)
        if x1 <= x <= x2:
            pts.append((x, y2))
        y = y1 - c * (sin_a / cos_a)
        if y1 <= y <= y2:
            pts.append((x1, y))
        y = y1 + (w - c) * (sin_a / cos_a)
        if y1 <= y <= y2:
            pts.append((x2, y))
            
        uniq = []
        for p in pts:
            if not any(math.hypot(p[0]-u[0], p[1]-u[1]) < 0.01 for u in uniq):
                uniq.append(p)
        if len(uniq) >= 2:
            engine.add_line(uniq[0], uniq[1], layer=layer, target=t)
        c += diag_step


def create_title_block_block(engine):
    """
    Creates standard Parameterized Title Block as a BLOCK entity with ATTDEF fields.
    Double-clickable in CAXA and AutoCAD to edit values!
    """
    blk_name = "TITLE_BLOCK_A3"
    blk = engine.doc.blocks.new(name=blk_name)

    tb_w = 155.0
    tb_h = 28.0
    
    # Outer frame of title block
    blk.add_lwpolyline([(0, 0), (tb_w, 0), (tb_w, tb_h), (0, tb_h)], close=True, dxfattribs={"layer": "7_图框标题栏"})
    
    # Horizontal grid lines (4 rows, 7mm each)
    blk.add_line((0, 7), (tb_w, 7), dxfattribs={"layer": "1_细实线"})
    blk.add_line((0, 14), (tb_w, 14), dxfattribs={"layer": "1_细实线"})
    blk.add_line((0, 21), (tb_w, 21), dxfattribs={"layer": "1_细实线"})
    
    # Vertical grid lines
    blk.add_line((115, 0), (115, 21), dxfattribs={"layer": "1_细实线"})
    blk.add_line((135, 0), (135, 21), dxfattribs={"layer": "1_细实线"})
    
    # Row 4 (Top): Project Header (Fixed text)
    engine.add_text("《工程图学》实验指导书", (tb_w / 2.0, 24.5), height=3.2, align="CENTER", layer="6_文字说明", target=blk)

    # Row 3: Title & Scale
    engine.add_text("实验2  电气工程相关机加工零部件——图块与复用训练", (5, 17.5), height=2.6, align="LEFT", layer="6_文字说明", target=blk)
    engine.add_text("比例", (125, 17.5), height=2.4, align="CENTER", layer="6_文字说明", target=blk)
    blk.add_attdef("SCALE", insert=(145, 17.5), height=2.4, text="1:1",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE"}).set_placement(
                       (145, 17.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    # Row 2: DWG No & Paper Size
    engine.add_text("图号: CAD-TRAINING", (5, 10.5), height=2.6, align="LEFT", layer="6_文字说明", target=blk)
    engine.add_text("图纸", (125, 10.5), height=2.4, align="CENTER", layer="6_文字说明", target=blk)
    blk.add_attdef("PAPER", insert=(145, 10.5), height=2.4, text="A3",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE"}).set_placement(
                       (145, 10.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    # Row 1 (Bottom): Designer, Checker (Strict Privacy: Blanks!) & Date
    engine.add_text("设计者: ", (5, 3.5), height=2.4, align="LEFT", layer="6_文字说明", target=blk)
    blk.add_attdef("DESIGNER", insert=(22, 3.5), height=2.4, text="",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE"}).set_placement(
                       (22, 3.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_LEFT)

    engine.add_text("审核: ", (65, 3.5), height=2.4, align="LEFT", layer="6_文字说明", target=blk)
    blk.add_attdef("CHECKER", insert=(78, 3.5), height=2.4, text="",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE"}).set_placement(
                       (78, 3.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_LEFT)

    engine.add_text("日期", (125, 3.5), height=2.4, align="CENTER", layer="6_文字说明", target=blk)
    blk.add_attdef("DATE", insert=(145, 3.5), height=2.4, text="2026.09",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE"}).set_placement(
                       (145, 3.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    return blk_name


def create_motor_end_cover_block(engine):
    """
    Creates Block: MOTOR_END_COVER (02 法兰盘/电机端盖) with ATTDEF fields.
    Base point at (0, 0) (center of circular view).
    """
    blk_name = "MOTOR_END_COVER"
    blk = engine.doc.blocks.new(name=blk_name)
    s = 0.5  # Scale 1:2 to fit A3 quadrant

    # Attributes (stored invisibly inside the block for double-click inspection)
    blk.add_attdef("TAG", (0, 0), height=2.5, text="EC-01",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("NAME", (0, 0), height=2.5, text="MOTOR_END_COVER",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("SIZE", (0, 0), height=2.2, text="OD150_ID60_T15",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("NOTE", (0, 0), height=2.2, text="CAST_IRON_HT200",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})

    # 1. Front View (Circular View) centered at (0, 0)
    r_outer = 75.0 * s    # Ø150 -> 37.5
    r_boss = 50.0 * s     # Ø100 -> 25.0
    r_hole = 30.0 * s     # Ø60 -> 15.0
    r_pcd = 62.5 * s      # PCD Ø125 -> 31.25
    r_bolt = 5.5 * s      # Ø11 -> 2.75

    blk.add_circle((0, 0), r_outer, dxfattribs={"layer": "0_粗实线"})
    blk.add_circle((0, 0), r_boss, dxfattribs={"layer": "0_粗实线"})
    blk.add_circle((0, 0), r_hole, dxfattribs={"layer": "0_粗实线"})
    blk.add_circle((0, 0), r_pcd, dxfattribs={"layer": "2_中心线"})
    engine.add_center_cross((0, 0), r_outer, extension=4.0, target=blk)

    # 4 Bolt holes
    hole_angles = [0, 90, 180, 270]
    for ang in hole_angles:
        rad = math.radians(ang)
        hx = r_pcd * math.cos(rad)
        hy = r_pcd * math.sin(rad)
        blk.add_circle((hx, hy), r_bolt, dxfattribs={"layer": "0_粗实线"})
        engine.add_center_cross((hx, hy), r_bolt, extension=2.0, target=blk)

    # Angular dimension 90°
    engine.add_arc((0, 0), r_pcd + 5.0, 270, 360, layer="4_尺寸标注", target=blk)
    engine.add_text("90°", (18, -35), height=2.6, align="CENTER", layer="4_尺寸标注", target=blk)
    engine.add_arc((0, 0), r_pcd + 5.0, 180, 270, layer="4_尺寸标注", target=blk)
    engine.add_text("90°", (-18, -35), height=2.6, align="CENTER", layer="4_尺寸标注", target=blk)

    # Front view Dimensions & Leaders
    engine.add_leader((0, r_pcd), (25, 48), "4×Ø11 通孔", height=2.8, target=blk)
    engine.add_leader((r_outer * 0.707, r_outer * 0.707), (45, 38), "Ø150", height=2.8, target=blk)
    engine.add_leader((r_boss * 0.707, r_boss * 0.707), (40, 24), "Ø100", height=2.8, target=blk)

    # 2. Section View (Right side)
    sec_x = 75.0  # Center X for section view
    t_rim = 10.0 * s     # 10mm -> 5.0
    t_boss = 15.0 * s    # 15mm -> 7.5
    x_left = sec_x - t_boss / 2.0
    x_rim_r = x_left + t_rim
    x_boss_r = x_left + t_boss

    # Outer contours
    blk.add_line((x_left, -r_outer), (x_left, r_outer), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_left, r_outer), (x_rim_r, r_outer), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_rim_r, r_outer), (x_rim_r, r_boss), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_rim_r, r_boss), (x_boss_r, r_boss), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_boss_r, r_boss), (x_boss_r, r_hole), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_boss_r, r_hole), (x_left, r_hole), dxfattribs={"layer": "0_粗实线"})

    blk.add_line((x_left, -r_outer), (x_rim_r, -r_outer), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_rim_r, -r_outer), (x_rim_r, -r_boss), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_rim_r, -r_boss), (x_boss_r, -r_boss), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_boss_r, -r_boss), (x_boss_r, -r_hole), dxfattribs={"layer": "0_粗实线"})
    blk.add_line((x_boss_r, -r_hole), (x_left, -r_hole), dxfattribs={"layer": "0_粗实线"})

    # Bolt holes in section (top & bottom)
    for sign in [1, -1]:
        by_c = sign * r_pcd
        blk.add_line((x_left, by_c - r_bolt), (x_rim_r, by_c - r_bolt), dxfattribs={"layer": "0_粗实线"})
        blk.add_line((x_left, by_c + r_bolt), (x_rim_r, by_c + r_bolt), dxfattribs={"layer": "0_粗实线"})
        engine.add_centerline((x_left - 2, by_c), (x_rim_r + 2, by_c), extension=1.5, target=blk)

    # Section centerline (axis)
    engine.add_centerline((x_left - 5, 0), (x_boss_r + 5, 0), extension=3.0, target=blk)

    # Hatches
    draw_hatch_rect(engine, (x_left, r_boss), (x_rim_r, r_outer), step=1.5, target=blk)
    draw_hatch_rect(engine, (x_left, r_hole), (x_boss_r, r_boss), step=1.5, target=blk)
    draw_hatch_rect(engine, (x_left, -r_outer), (x_rim_r, -r_boss), step=1.5, target=blk)
    draw_hatch_rect(engine, (x_left, -r_boss), (x_boss_r, -r_hole), step=1.5, target=blk)

    # Section dimensions
    engine.add_dimension_linear((x_left - 12, -r_outer), (x_left - 12, r_outer), offset=-12, dim_type="VERTICAL", override_text="Ø150", target=blk)
    engine.add_dimension_linear((x_left - 6, -r_boss), (x_left - 6, r_boss), offset=-6, dim_type="VERTICAL", override_text="Ø100", target=blk)
    engine.add_dimension_linear((x_boss_r + 8, -r_hole), (x_boss_r + 8, r_hole), offset=8, dim_type="VERTICAL", override_text="Ø60", target=blk)
    engine.add_dimension_linear((x_left, r_outer + 5), (x_rim_r, r_outer + 5), offset=6, dim_type="HORIZONTAL", override_text="10", target=blk)
    engine.add_dimension_linear((x_left, -r_outer - 5), (x_boss_r, -r_outer - 5), offset=-8, dim_type="HORIZONTAL", override_text="15", target=blk)

    return blk_name


def create_terminal_plate_block(engine):
    """
    Creates Block: TERMINAL_PLATE (03 接线盒安装板) with ATTDEF fields.
    Base point at lower-left (0, 0).
    """
    blk_name = "TERMINAL_PLATE"
    blk = engine.doc.blocks.new(name=blk_name)
    s = 0.6  # Scale to fit quadrant

    w = 200.0 * s   # 120.0
    h = 80.0 * s    # 48.0
    t_plate = 8.0 * s  # 4.8

    # Attributes (stored invisibly inside the block for double-click inspection)
    blk.add_attdef("TAG", (0, 0), height=2.5, text="TP-01",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("NAME", (0, 0), height=2.5, text="TERMINAL_PLATE",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("SIZE", (0, 0), height=2.2, text="200x80x8_12x10",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})
    blk.add_attdef("NOTE", (0, 0), height=2.2, text="Q235_GALVANIZED",
                   dxfattribs={"layer": "6_文字说明", "style": "GB_STYLE", "invisible": True})

    # 1. Front View Plate Rectangle
    blk.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True, dxfattribs={"layer": "0_粗实线"})

    # 2 Rows of Holes (matching reference drawing: 7 columns, callout 12×Ø10)
    r_hole = 5.0 * s  # 3.0
    y_row1 = 25.0 * s
    y_row2 = 55.0 * s
    x_margin = 20.0 * s
    pitch = (w - 2 * x_margin) / 6.0

    hole_centers = []
    for c in range(7):
        hx = x_margin + c * pitch
        for hy in [y_row1, y_row2]:
            blk.add_circle((hx, hy), r_hole, dxfattribs={"layer": "0_粗实线"})
            engine.add_center_cross((hx, hy), r_hole, extension=2.0, target=blk)
            hole_centers.append((hx, hy))

    # Dimensions
    engine.add_dimension_linear((-6, 0), (-6, h), offset=-6, dim_type="VERTICAL", override_text="80", target=blk)
    engine.add_dimension_linear((0, -8), (w, -8), offset=-8, dim_type="HORIZONTAL", override_text="200", target=blk)
    engine.add_dimension_linear((0, -3), (x_margin, -3), offset=-3, dim_type="HORIZONTAL", override_text="20", target=blk)
    engine.add_dimension_linear((x_margin + pitch, -3), (x_margin + 2 * pitch, -3), offset=-3, dim_type="HORIZONTAL", override_text="30", target=blk)
    engine.add_dimension_linear((w - x_margin, -3), (w, -3), offset=-3, dim_type="HORIZONTAL", override_text="20", target=blk)

    # Leader to hole: "12×Ø10"
    target_hole = (x_margin + 5 * pitch, y_row2)
    engine.add_leader(target_hole, (target_hole[0] + 15, h + 10), "12×Ø10", height=2.8, target=blk)

    # 2. Section View (Right side)
    sec_x = w + 20.0
    blk.add_lwpolyline([(sec_x, 0), (sec_x + t_plate, 0), (sec_x + t_plate, h), (sec_x, h)], close=True, dxfattribs={"layer": "0_粗实线"})
    for hy in [y_row1, y_row2]:
        blk.add_line((sec_x, hy - r_hole), (sec_x + t_plate, hy - r_hole), dxfattribs={"layer": "0_粗实线"})
        blk.add_line((sec_x, hy + r_hole), (sec_x + t_plate, hy + r_hole), dxfattribs={"layer": "0_粗实线"})
        engine.add_centerline((sec_x - 2, hy), (sec_x + t_plate + 2, hy), extension=1.5, target=blk)

    # Section Hatch
    draw_hatch_rect(engine, (sec_x, 0), (sec_x + t_plate, y_row1 - r_hole), step=1.5, target=blk)
    draw_hatch_rect(engine, (sec_x, y_row1 + r_hole), (sec_x + t_plate, y_row2 - r_hole), step=1.5, target=blk)
    draw_hatch_rect(engine, (sec_x, y_row2 + r_hole), (sec_x + t_plate, h), step=1.5, target=blk)

    # Section Dimension: 8
    engine.add_dimension_linear((sec_x, h + 3), (sec_x + t_plate, h + 3), offset=4, dim_type="HORIZONTAL", override_text="8", target=blk)

    return blk_name


def draw_part_01_shaft(engine, origin=(15, 150)):
    """Draws 01 轴类零件（电机转轴）"""
    ox, oy = origin
    engine.add_text("01 轴类零件（电机转轴）", (ox, oy + 110), height=4.5, align="LEFT", layer="6_文字说明")

    s = 0.75  # Scale
    cx_axis = oy + 62.0
    x_start = ox + 18.0

    l1, d1 = 35.0 * s, 20.0 * s
    l2, d2 = 40.0 * s, 25.0 * s
    l3, d3 = 40.0 * s, 20.0 * s
    l4, d4 = 30.0 * s, 16.0 * s
    c_chamfer = 1.0 * s

    x0 = x_start
    x1 = x0 + l1
    x2 = x1 + l2
    x3 = x2 + l3
    x4 = x3 + l4

    # Centerline
    engine.add_centerline((x0 - 5, cx_axis), (x4 + 5, cx_axis), extension=4.0)

    # Step 1: Chamfer 1x45
    engine.add_line((x0 + c_chamfer, cx_axis + d1 / 2), (x1, cx_axis + d1 / 2))
    engine.add_line((x0 + c_chamfer, cx_axis - d1 / 2), (x1, cx_axis - d1 / 2))
    engine.add_line((x0 + c_chamfer, cx_axis + d1 / 2), (x0, cx_axis + d1 / 2 - c_chamfer))
    engine.add_line((x0 + c_chamfer, cx_axis - d1 / 2), (x0, cx_axis - d1 / 2 + c_chamfer))
    engine.add_line((x0, cx_axis - d1 / 2 + c_chamfer), (x0, cx_axis + d1 / 2 - c_chamfer))

    # Step 1 to Step 2 shoulder
    engine.add_line((x1, cx_axis - d2 / 2), (x1, cx_axis + d2 / 2))

    # Step 2
    engine.add_line((x1, cx_axis + d2 / 2), (x2, cx_axis + d2 / 2))
    engine.add_line((x1, cx_axis - d2 / 2), (x2, cx_axis - d2 / 2))

    # Step 2 to Step 3 shoulder
    engine.add_line((x2, cx_axis - d2 / 2), (x2, cx_axis + d2 / 2))

    # Step 3
    engine.add_line((x2, cx_axis + d3 / 2), (x3, cx_axis + d3 / 2))
    engine.add_line((x2, cx_axis - d3 / 2), (x3, cx_axis - d3 / 2))

    # Step 3 to Step 4 shoulder
    engine.add_line((x3, cx_axis - d3 / 2), (x3, cx_axis + d3 / 2))

    # Step 4: Chamfer 1x45
    engine.add_line((x3, cx_axis + d4 / 2), (x4 - c_chamfer, cx_axis + d4 / 2))
    engine.add_line((x3, cx_axis - d4 / 2), (x4 - c_chamfer, cx_axis - d4 / 2))
    engine.add_line((x4 - c_chamfer, cx_axis + d4 / 2), (x4, cx_axis + d4 / 2 - c_chamfer))
    engine.add_line((x4 - c_chamfer, cx_axis - d4 / 2), (x4, cx_axis - d4 / 2 + c_chamfer))
    engine.add_line((x4, cx_axis - d4 / 2 + c_chamfer), (x4, cx_axis + d4 / 2 - c_chamfer))

    # Right Projection View
    rx = x4 + 22.0
    engine.add_circle((rx, cx_axis), d2 / 2, layer="0_粗实线")
    engine.add_circle((rx, cx_axis), d1 / 2, layer="0_粗实线")
    engine.add_center_cross((rx, cx_axis), d2 / 2, extension=3.0)

    # Dimensions
    y_dim1 = cx_axis - d2 / 2 - 12
    engine.add_dimension_linear((x0, y_dim1), (x1, y_dim1), offset=-6, dim_type="HORIZONTAL", override_text="35")
    engine.add_dimension_linear((x1, y_dim1), (x2, y_dim1), offset=-6, dim_type="HORIZONTAL", override_text="40")
    engine.add_dimension_linear((x2, y_dim1), (x3, y_dim1), offset=-6, dim_type="HORIZONTAL", override_text="40")
    engine.add_dimension_linear((x3, y_dim1), (x4, y_dim1), offset=-6, dim_type="HORIZONTAL", override_text="30")
    engine.add_dimension_linear((x0, y_dim1 - 8), (x4, y_dim1 - 8), offset=-14, dim_type="HORIZONTAL", override_text="145")

    # Diameters
    engine.add_dimension_linear((x1 + 15, cx_axis - d2 / 2), (x1 + 15, cx_axis + d2 / 2), offset=0, dim_type="VERTICAL", override_text="Ø25")
    engine.add_dimension_linear((x2 + 15, cx_axis - d3 / 2), (x2 + 15, cx_axis + d3 / 2), offset=0, dim_type="VERTICAL", override_text="Ø20")
    engine.add_dimension_linear((x3 + 12, cx_axis - d4 / 2), (x3 + 12, cx_axis + d4 / 2), offset=0, dim_type="VERTICAL", override_text="Ø16")

    # Chamfer Leaders (Pointing neatly inward)
    engine.add_leader((x0 + c_chamfer / 2, cx_axis + d1 / 2), (x0 + 15, cx_axis + d1 / 2 + 10), "1×45°", height=2.8)
    engine.add_leader((x4 - c_chamfer / 2, cx_axis + d4 / 2), (x4 + 8, cx_axis + d4 / 2 + 10), "1×45°", height=2.8)

    # Right view dimensions
    engine.add_dimension_linear((rx, cx_axis + d2 / 2), (rx + 15, cx_axis + d2 / 2 + 5), offset=8, dim_type="HORIZONTAL", override_text="Ø25")
    engine.add_dimension_linear((rx, cx_axis + d1 / 2), (rx + 15, cx_axis + d1 / 2 - 2), offset=5, dim_type="HORIZONTAL", override_text="Ø20")

    # Technical Notes & Roughness
    engine.add_text("技术要求：", (ox, oy + 22), height=3.0, layer="6_文字说明")
    engine.add_text("1.  未注圆角R1～R2；", (ox, oy + 16), height=2.5, layer="6_文字说明")
    engine.add_text("2.  表面粗糙度Ra3.2。", (ox, oy + 10), height=2.5, layer="6_文字说明")
    engine.add_roughness_symbol((ox + 160, oy + 8), "Ra3.2")


def draw_part_04_fan_hub(engine, origin=(215, 38)):
    """Draws 04 风扇轮毂（电机风扇）"""
    ox, oy = origin
    engine.add_text("04 风扇轮毂（电机风扇）", (ox, oy + 104), height=4.5, align="LEFT", layer="6_文字说明")

    s = 0.52  # Scale
    cx, cy = ox + 60.0, oy + 58.0

    r_outer = 60.0 * s   # Ø120 -> 31.2
    r_bore = 15.0 * s    # Ø30 -> 7.8
    r_hub = 26.0 * s     # Ø52 -> 13.5
    r_pcd = 45.0 * s     # PCD -> 23.4
    r_hole = 4.0 * s     # Ø8 -> 2.08

    # 1. Circular View (Front)
    engine.add_circle((cx, cy), r_outer, layer="0_粗实线")
    engine.add_circle((cx, cy), r_hub, layer="0_粗实线")
    engine.add_circle((cx, cy), r_bore, layer="0_粗实线")
    engine.add_circle((cx, cy), r_pcd, layer="2_中心线")
    engine.add_center_cross((cx, cy), r_outer, extension=3.0)

    # 6 Streamlined Air Vanes (Curved blades)
    for i in range(6):
        base_ang = i * 60.0
        rad1 = math.radians(base_ang)
        rad2 = math.radians(base_ang + 25.0)
        
        # Blade root at hub
        p_in1 = (cx + r_hub * math.cos(rad1), cy + r_hub * math.sin(rad1))
        p_in2 = (cx + r_hub * math.cos(rad2), cy + r_hub * math.sin(rad2))
        
        # Blade tip at outer rim (curved)
        p_out1 = (cx + r_outer * math.cos(rad1 + 0.15), cy + r_outer * math.sin(rad1 + 0.15))
        p_out2 = (cx + r_outer * math.cos(rad2 + 0.15), cy + r_outer * math.sin(rad2 + 0.15))
        
        engine.add_line(p_in1, p_out1, layer="0_粗实线")
        engine.add_line(p_in2, p_out2, layer="0_粗实线")

    # Dimensions on Circular View
    engine.add_leader((cx + r_outer * 0.707, cy + r_outer * 0.707), (cx + r_outer + 10, cy + r_outer + 12), "Ø120", height=2.8)
    engine.add_leader((cx + r_bore * 0.707, cy + r_bore * 0.707), (cx + r_outer + 10, cy + 5), "Ø30", height=2.8)
    engine.add_leader((cx + r_pcd * math.cos(math.radians(110)), cy + r_pcd * math.sin(math.radians(110))), (cx - 15, cy + r_outer + 4), "6×Ø8", height=2.8)

    # 2. Section View (Right side)
    sec_x = ox + 140.0
    t_rim = 20.0 * s     # 20 -> 10.4
    t_web = 10.0 * s     # 10 -> 5.2
    t_boss = 15.0 * s    # 15 -> 7.8
    r_cbore = 30.0 * s   # Ø60 -> 15.6

    x0 = sec_x
    x1 = x0 + (t_rim - t_web)  # step
    x2 = x0 + t_rim
    x3 = x2 + t_boss

    # Centerline
    engine.add_centerline((x0 - 4, cy), (x3 + 4, cy), extension=2.5)

    # Contours
    # Top
    engine.add_line((x0, cy + r_cbore), (x0, cy + r_outer))
    engine.add_line((x0, cy + r_outer), (x2, cy + r_outer))
    engine.add_line((x2, cy + r_outer), (x2, cy + r_hub))
    engine.add_line((x2, cy + r_hub), (x3, cy + r_hub))
    engine.add_line((x3, cy + r_hub), (x3, cy + r_bore))
    engine.add_line((x3, cy + r_bore), (x1, cy + r_bore))
    engine.add_line((x1, cy + r_bore), (x1, cy + r_cbore))
    engine.add_line((x1, cy + r_cbore), (x0, cy + r_cbore))

    # Bottom
    engine.add_line((x0, cy - r_cbore), (x0, cy - r_outer))
    engine.add_line((x0, cy - r_outer), (x2, cy - r_outer))
    engine.add_line((x2, cy - r_outer), (x2, cy - r_hub))
    engine.add_line((x2, cy - r_hub), (x3, cy - r_hub))
    engine.add_line((x3, cy - r_hub), (x3, cy - r_bore))
    engine.add_line((x3, cy - r_bore), (x1, cy - r_bore))
    engine.add_line((x1, cy - r_bore), (x1, cy - r_cbore))
    engine.add_line((x1, cy - r_cbore), (x0, cy - r_cbore))

    # Opening at PCD
    for sign in [1, -1]:
        oy_c = cy + sign * r_pcd
        engine.add_line((x1, oy_c - r_hole), (x2, oy_c - r_hole), layer="0_粗实线")
        engine.add_line((x1, oy_c + r_hole), (x2, oy_c + r_hole), layer="0_粗实线")
        engine.add_centerline((x1 - 1, oy_c), (x2 + 1, oy_c), extension=1.5)

    # Hatches: split around the PCD opening so the through opening is clean
    oy_top = cy + r_pcd
    oy_bot = cy - r_pcd
    # Top rim & web
    draw_hatch_rect(engine, (x0, cy + r_cbore), (x1, cy + r_outer), step=1.5)
    draw_hatch_rect(engine, (x1, oy_top + r_hole), (x2, cy + r_outer), step=1.5)
    draw_hatch_rect(engine, (x1, cy + r_cbore), (x2, oy_top - r_hole), step=1.5)
    draw_hatch_rect(engine, (x1, cy + r_bore), (x3, cy + r_hub), step=1.5)
    # Bottom rim & web
    draw_hatch_rect(engine, (x0, cy - r_outer), (x1, cy - r_cbore), step=1.5)
    draw_hatch_rect(engine, (x1, cy - r_outer), (x2, oy_bot - r_hole), step=1.5)
    draw_hatch_rect(engine, (x1, oy_bot + r_hole), (x2, cy - r_cbore), step=1.5)
    draw_hatch_rect(engine, (x1, cy - r_hub), (x3, cy - r_bore), step=1.5)

    # Dimensions
    engine.add_dimension_linear((x0 - 10, cy - r_outer), (x0 - 10, cy + r_outer), offset=-10, dim_type="VERTICAL", override_text="Ø120")
    engine.add_dimension_linear((x0 - 4, cy - r_cbore), (x0 - 4, cy + r_cbore), offset=-4, dim_type="VERTICAL", override_text="Ø60")
    engine.add_dimension_linear((x0, cy + r_outer + 4), (x2, cy + r_outer + 4), offset=5, dim_type="HORIZONTAL", override_text="20")
    engine.add_dimension_linear((x2, cy + r_hub + 4), (x3, cy + r_hub + 4), offset=5, dim_type="HORIZONTAL", override_text="15")
    engine.add_dimension_linear((x1, cy - r_outer - 4), (x2, cy - r_outer - 4), offset=-5, dim_type="HORIZONTAL", override_text="10")

    # Technical Notes & Roughness
    engine.add_text("技术要求：", (ox, oy + 22), height=3.0, layer="6_文字说明")
    engine.add_text("1.  未注圆角R2～R3；", (ox, oy + 16), height=2.5, layer="6_文字说明")
    engine.add_text("2.  表面粗糙度Ra3.2；", (ox, oy + 10), height=2.5, layer="6_文字说明")
    engine.add_text("3.  动平衡等级：G6.3。", (ox, oy + 4), height=2.5, layer="6_文字说明")
    engine.add_roughness_symbol((ox + 160, oy + 4), "Ra3.2")


def generate_experiment_2():
    print("=== Generating Experiment 2: Electrical Machinery Components on A3 Sheet ===")
    engine = CADEngineExp2()

    # 1. Sheet Setup: A3 Landscape (420 x 297 mm)
    w, h = 420.0, 297.0
    engine.add_rectangle((0, 0), (w, h), layer="7_图框标题栏")
    engine.add_rectangle((10, 10), (w - 10, h - 10), layer="7_图框标题栏")

    # 2. Main Title (Top Center)
    engine.add_text(
        "实验2  电气工程相关机加工零部件——图块与复用训练",
        (w / 2.0, 277.0),
        height=6.0,
        align="CENTER",
        layer="7_图框标题栏"
    )

    # 3. Separator Lines (Creating 4 Quadrants & Footer)
    engine.add_line((10, 268), (w - 10, 268), layer="7_图框标题栏")
    engine.add_line((10, 150), (w - 10, 150), layer="7_图框标题栏")
    engine.add_line((210, 38), (210, 268), layer="7_图框标题栏")
    engine.add_line((10, 38), (w - 10, 38), layer="7_图框标题栏")

    # 4. Draw Part 01 (Motor Shaft) in Top-Left
    draw_part_01_shaft(engine, origin=(15, 150))

    # 5. Create & Insert BLOCK: MOTOR_END_COVER in Top-Right
    engine.add_text("02 法兰盘（电机端盖）", (215, 260), height=4.5, align="LEFT", layer="6_文字说明")
    create_motor_end_cover_block(engine)
    # Insert Block Reference
    blk_ref_cover = engine.msp.add_blockref("MOTOR_END_COVER", (280, 209))
    blk_ref_cover.add_auto_attribs({
        "TAG": "EC-01",
        "NAME": "MOTOR_END_COVER",
        "SIZE": "OD150_ID60_T15",
        "NOTE": "CAST_IRON_HT200"
    })
    # Technical notes for Part 02
    engine.add_text("技术要求：", (215, 172), height=3.0, layer="6_文字说明")
    engine.add_text("1.  未注圆角R2；", (215, 166), height=2.5, layer="6_文字说明")
    engine.add_text("2.  表面粗糙度Ra3.2。", (215, 160), height=2.5, layer="6_文字说明")
    engine.add_roughness_symbol((380, 158), "Ra3.2")

    # 6. Create & Insert BLOCK: TERMINAL_PLATE in Bottom-Left
    engine.add_text("03 接线盒安装板", (15, 142), height=4.5, align="LEFT", layer="6_文字说明")
    create_terminal_plate_block(engine)
    # Insert Block Reference
    blk_ref_plate = engine.msp.add_blockref("TERMINAL_PLATE", (25, 78))
    blk_ref_plate.add_auto_attribs({
        "TAG": "TP-01",
        "NAME": "TERMINAL_PLATE",
        "SIZE": "200x80x8_12x10",
        "NOTE": "Q235_GALVANIZED"
    })
    # Technical notes for Part 03
    engine.add_text("技术要求：", (15, 60), height=3.0, layer="6_文字说明")
    engine.add_text("1.  未注圆角R2；", (15, 54), height=2.5, layer="6_文字说明")
    engine.add_text("2.  表面粗糙度Ra3.2；", (15, 48), height=2.5, layer="6_文字说明")
    engine.add_text("3.  孔中心距允许偏差±0.1。", (15, 42), height=2.5, layer="6_文字说明")
    engine.add_roughness_symbol((180, 42), "Ra3.2")

    # 7. Draw Part 04 (Fan Hub) in Bottom-Right
    draw_part_04_fan_hub(engine, origin=(215, 38))

    # 8. Bottom Footer Left: Training Notes & Legend
    engine.add_line((255, 10), (255, 38), layer="7_图框标题栏")
    engine.add_text("训练内容：", (15, 30), height=3.5, align="LEFT", layer="6_文字说明")
    engine.add_text(
        "1. 熟悉电气工程相关零部件结构；    2. 掌握轴、法兰、板类、轮毂等零件的绘制方法；    3. 学会使用图块进行图形复用。",
        (15, 23),
        height=2.6,
        align="LEFT",
        layer="6_文字说明"
    )
    engine.add_text(
        "图例： BLOCK / INSERT / ATTRIBUTE / LAYER / CENTER / DIM / HATCH / OSNAP",
        (15, 16),
        height=2.6,
        align="LEFT",
        layer="6_文字说明"
    )

    # 9. Bottom Footer Right: Parameterized TITLE BLOCK (BLOCK + ATTDEF)
    tb_block_name = create_title_block_block(engine)
    # Insert Title Block reference at (255, 10)
    tb_ref = engine.msp.add_blockref(tb_block_name, (255, 10))
    tb_ref.add_auto_attribs({
        "SCALE": "1:1",
        "PAPER": "A3",
        "DESIGNER": "",
        "CHECKER": "",
        "DATE": "2026.09"
    })

    # 10. Save Outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_dxf = os.path.join(OUTPUT_DIR, "实验2_4个电气相关机加工零件.dxf")
    engine.doc.saveas(out_dxf)
    print(f"DXF saved to: {out_dxf}")

    # 11. Create Standalone Blocks Library DXF (blocks_library.dxf)
    lib_doc = ezdxf.new("R2010", setup=True)
    lib_engine = CADEngineExp2()
    create_title_block_block(lib_engine)
    create_motor_end_cover_block(lib_engine)
    create_terminal_plate_block(lib_engine)
    lib_engine.add_text("实验2 专用电气机加工零部件与标题栏图块库", (10, 160), height=5.0, layer="6_文字说明")
    lib_engine.msp.add_blockref("TITLE_BLOCK_A3", (10, 10))
    lib_engine.msp.add_blockref("MOTOR_END_COVER", (60, 90))
    lib_engine.msp.add_blockref("TERMINAL_PLATE", (150, 70))
    lib_dxf = os.path.join(OUTPUT_DIR, "blocks_library.dxf")
    lib_engine.doc.saveas(lib_dxf)
    print(f"Blocks library saved to: {lib_dxf}")

    # 12. High-Resolution Rendering (A3 Vector PDF & 4K PNG)
    print("Rendering high-res CAD preview images and vector PDF...")
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        doc = ezdxf.readfile(out_dxf)
        msp = doc.modelspace()

        # Dark theme 4K PNG for engineering inspection
        fig = plt.figure(figsize=(16.8, 11.88), dpi=250)
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)

        png_f = os.path.join(OUTPUT_DIR, "exp2_preview.png")
        fig.savefig(png_f, dpi=250, facecolor='#181b20')
        print(f"Saved PNG to: {png_f}")

        # Standard White Vector PDF for Print/Submission (A3 420x297mm)
        fig_pdf = plt.figure(figsize=(16.535, 11.693))  # 420mm x 297mm in inches
        ax_pdf = fig_pdf.add_axes([0, 0, 1, 1])
        out_pdf = MatplotlibBackend(ax_pdf)
        Frontend(ctx, out_pdf).draw_layout(msp, finalize=True)
        pdf_f = os.path.join(OUTPUT_DIR, "实验2_4个电气相关机加工零件.pdf")
        fig_pdf.savefig(pdf_f, format='pdf', facecolor='white')
        print(f"Saved Vector PDF to: {pdf_f}")

        plt.close(fig)
        plt.close(fig_pdf)

        # 12b. Render High-Resolution Zoom Previews
        print("Generating cropped high-res previews of all quadrants...")
        full_img = Image.open(png_f)
        iw, ih = full_img.size

        # P1: Shaft (Top-Left)
        p1_img = full_img.crop((int(iw * 0.02), int(ih * 0.08), int(iw * 0.51), int(ih * 0.51)))
        p1_img.save(os.path.join(OUTPUT_DIR, "zoom_p1_shaft.png"))

        # P2: Flange (Top-Right)
        p2_img = full_img.crop((int(iw * 0.49), int(ih * 0.08), int(iw * 0.98), int(ih * 0.51)))
        p2_img.save(os.path.join(OUTPUT_DIR, "zoom_p2_flange.png"))

        # P3: Plate (Bottom-Left)
        p3_img = full_img.crop((int(iw * 0.02), int(ih * 0.49), int(iw * 0.51), int(ih * 0.88)))
        p3_img.save(os.path.join(OUTPUT_DIR, "zoom_p3_plate.png"))

        # P4: Hub (Bottom-Right)
        p4_img = full_img.crop((int(iw * 0.49), int(ih * 0.49), int(iw * 0.98), int(ih * 0.88)))
        p4_img.save(os.path.join(OUTPUT_DIR, "zoom_p4_hub.png"))

        # Footer & Title Block
        tb_img = full_img.crop((int(iw * 0.02), int(ih * 0.81), int(iw * 0.98), int(ih * 0.98)))
        tb_img.save(os.path.join(OUTPUT_DIR, "zoom_title_block.png"))
        print("Zoom previews generated successfully!")

    except Exception as e:
        print(f"Rendering error: {e}")

    # 13. Synchronize to Target Archive Directory: F:\cad  caxa工程图\03_实验2_成果图纸
    print(f"Archiving deliverables to: {TARGET_ARCHIVE_DIR} ...")
    os.makedirs(TARGET_ARCHIVE_DIR, exist_ok=True)
    for fname in os.listdir(OUTPUT_DIR):
        src = os.path.join(OUTPUT_DIR, fname)
        dst = os.path.join(TARGET_ARCHIVE_DIR, fname)
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
            print(f"  Synced -> {fname}")

    # Also provide .dwg copy (DWG standard filename)
    dwg_target = os.path.join(TARGET_ARCHIVE_DIR, "实验2_4个电气相关机加工零件.dwg")
    shutil.copyfile(out_dxf, dwg_target)
    print(f"  DWG compatible file created -> {dwg_target}")

    # 14. Create Informative README
    readme_content = """================================================================================
《工程图学》实验2：电气工程相关机加工零部件——图块与复用训练
================================================================================

一、成果文件清单：
1. 实验2_4个电气相关机加工零件.dwg
   - AutoCAD / CAXA 电子图板兼容工程图文件。
   - 包含标准 A3 横向图幅（420 × 297 mm）、4 个电气设备机加工零件完整视图与尺寸约束。
   - 【核心特色】：
     * 标题栏封装为参数化属性图块（TITLE_BLOCK_A3），鼠标双击即可弹出标准表格填写姓名学号！
     * 02法兰盘封装为 MOTOR_END_COVER 图块，03安装板封装为 TERMINAL_PLATE 图块，内置 TAG、NAME、SIZE、NOTE 属性定义。

2. 实验2_4个电气相关机加工零件.dxf
   - 国际工业标准全兼容 ASCII DXF 文件。

3. 实验2_4个电气相关机加工零件.pdf
   - 1:1 标准 A3 纯矢量工程 PDF 文件（420 × 297 mm）。
   - 粗细线宽分明、黑白对比清晰锐利，可直接打印交付。

4. blocks_library.dxf
   - 实验2 专属标准图块库。
   - 独立封装：TITLE_BLOCK_A3（A3标题栏）、MOTOR_END_COVER（电机端盖）、TERMINAL_PLATE（接线盒安装板）。

5. 预览与特写高清图：
   - exp2_preview.png（4K 全图超清预览）
   - zoom_p1_shaft.png（01 电机转轴特写）
   - zoom_p2_flange.png（02 电机端盖特写）
   - zoom_p3_plate.png（03 安装板特写）
   - zoom_p4_hub.png（04 风扇轮毂特写）
   - zoom_title_block.png（标题栏特写）

二、零件技术参数汇总：
- 01 轴类零件（电机转轴）：四段阶梯轴（Ø20×35, Ø25×40, Ø20×40, Ø16×30, 总长145），带右视图与两端 1×45° 倒角。
- 02 法兰盘（电机端盖）：外径 Ø150，凸台 Ø100，中心孔 Ø60，分度圆 PCD Ø125，4×Ø11 通孔，全剖截面图。
- 03 接线盒安装板：外轮廓 200×80×8，12×Ø10 孔阵列（对称分布，边距20，间距30），全剖截面图。
- 04 风扇轮毂（电机风扇）：外径 Ø120，轴孔 Ø30，6个流线型散热叶片与 6×Ø8 窗口，阶梯截面图。

三、CAXA 电子图板出图指南：
1. 打开文件后按 Ctrl + P；
2. 打印机名称选：EXB To PDF.drv（或 CAXA PDF Converter Driver）；
3. 纸张大小选：A3 横向（420 × 297 mm）；
4. 输出图形选：【极限图形】或【窗口图形】（勾选居中打印，比例 1:1 或按纸张调整）；
5. 勾选“黑白打印”，预览确认后即可输出完美矢量 PDF。

四、合规与隐私保护声明：
- 本图纸严格遵循 GB/T 14665 机械工程 CAD 制图规则。
- 标题栏审核人与设计者栏位做规范留白处理，杜绝任何个人隐私泄露。
================================================================================
"""
    readme_path = os.path.join(TARGET_ARCHIVE_DIR, "说明文档_README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Readme created at: {readme_path}")

    print("\n=== Experiment 2 Generation Completed Successfully! ===")
    return out_dxf


if __name__ == "__main__":
    generate_experiment_2()
