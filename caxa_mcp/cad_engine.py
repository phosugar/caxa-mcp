"""
CAD Engine for CAXA MCP
Provides high-precision CAD drawing generation conforming to Chinese National Standards (GB/T 14665 / GB/T 4458).
Supports layers, linestyles, standard A0-A4 frames, GB title blocks, dimensions, and parametric mechanical parts.
"""

import math
import os
from typing import List, Tuple, Dict, Any, Optional
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment


class CADEngine:
    """High-precision CAD drafting engine producing DXF files optimized for CAXA Draft."""

    # Standard layers for Chinese mechanical drawings (GB/T 14665)
    DEFAULT_LAYERS = {
        "0_粗实线": {"color": colors.WHITE, "linetype": "Continuous", "lineweight": 35},
        "1_细实线": {"color": colors.WHITE, "linetype": "Continuous", "lineweight": 18},
        "2_中心线": {"color": colors.RED, "linetype": "CENTER", "lineweight": 18},
        "3_虚线": {"color": colors.YELLOW, "linetype": "HIDDEN", "lineweight": 18},
        "4_尺寸标注": {"color": colors.CYAN, "linetype": "Continuous", "lineweight": 18},
        "5_剖面线": {"color": colors.CYAN, "linetype": "Continuous", "lineweight": 18},
        "6_文字说明": {"color": colors.WHITE, "linetype": "Continuous", "lineweight": 25},
        "7_图框标题栏": {"color": colors.WHITE, "linetype": "Continuous", "lineweight": 35},
    }

    # Standard paper dimensions (width, height, left_margin, other_margin)
    PAPER_SIZES = {
        "A4": {"w": 297.0, "h": 210.0, "margin_left": 25.0, "margin_other": 5.0},
        "A4_V": {"w": 210.0, "h": 297.0, "margin_left": 25.0, "margin_other": 5.0},
        "A3": {"w": 420.0, "h": 297.0, "margin_left": 25.0, "margin_other": 5.0},
        "A2": {"w": 594.0, "h": 420.0, "margin_left": 25.0, "margin_other": 10.0},
        "A1": {"w": 841.0, "h": 594.0, "margin_left": 25.0, "margin_other": 10.0},
        "A0": {"w": 1189.0, "h": 841.0, "margin_left": 25.0, "margin_other": 10.0},
    }

    def __init__(self, dxf_version: str = "R2010"):
        self.doc = ezdxf.new(dxf_version, setup=True)
        self.msp = self.doc.modelspace()
        self._setup_styles_and_layers()
        self.paper_size = "A3"
        self.scale = 1.0

    def _setup_styles_and_layers(self):
        """Set up standard text styles, dimension styles and layers."""
        # Fix default Standard style to use CAXA's built-in font ACADTXT.SHX to avoid font prompt
        if "Standard" in self.doc.styles:
            std = self.doc.styles.get("Standard")
            std.dxf.font = "ACADTXT.SHX"

        # Setup Chinese text style using SimHei
        if "GB_STYLE" not in self.doc.styles:
            self.doc.styles.add(
                "GB_STYLE",
                font="simhei.ttf",
                dxfattribs={"width": 0.8},
            )

        # Setup Dimension Style for clear visibility (dimtxt=5.0, dimasz=4.0)
        if "GB_DIMSTYLE" not in self.doc.dimstyles:
            ds = self.doc.dimstyles.new("GB_DIMSTYLE")
            ds.dxf.dimtxt = 5.0
            ds.dxf.dimasz = 4.0
            ds.dxf.dimexe = 2.5
            ds.dxf.dimexo = 1.5
            ds.dxf.dimgap = 1.5
            ds.dxf.dimclrd = colors.CYAN
            ds.dxf.dimclre = colors.CYAN
            ds.dxf.dimclrt = colors.WHITE
            ds.dxf.dimtxsty = "GB_STYLE"

        # Load linetypes
        for lt_name in ["CENTER", "HIDDEN", "DASHED", "PHANTOM"]:
            if lt_name not in self.doc.linetypes:
                try:
                    self.doc.linetypes.load(lt_name)
                except Exception:
                    pass

        # Create standard layers
        for layer_name, props in self.DEFAULT_LAYERS.items():
            if layer_name not in self.doc.layers:
                self.doc.layers.add(
                    name=layer_name,
                    color=props["color"],
                    linetype=props["linetype"],
                    lineweight=props["lineweight"],
                )

    # -------------------------------------------------------------
    # Basic Drawing Primitives
    # -------------------------------------------------------------

    def add_line(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        layer: str = "0_粗实线",
    ):
        """Draw a straight line."""
        return self.msp.add_line(start, end, dxfattribs={"layer": layer})

    def add_circle(
        self,
        center: Tuple[float, float],
        radius: float,
        layer: str = "0_粗实线",
        add_centerline: bool = False,
        centerline_extension: float = 3.0,
    ):
        """Draw a circle with optional centerlines."""
        circle = self.msp.add_circle(center, radius, dxfattribs={"layer": layer})
        if add_centerline:
            self.add_cross_centerlines(center, radius, extension=centerline_extension)
        return circle

    def add_arc(
        self,
        center: Tuple[float, float],
        radius: float,
        start_angle: float,
        end_angle: float,
        layer: str = "0_粗实线",
    ):
        """Draw a circular arc in degrees."""
        return self.msp.add_arc(
            center,
            radius,
            start_angle,
            end_angle,
            dxfattribs={"layer": layer},
        )

    def add_rectangle(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        layer: str = "0_粗实线",
    ):
        """Draw a rectangle between two opposite corners."""
        x1, y1 = p1
        x2, y2 = p2
        pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        return self.add_polyline(pts, is_closed=True, layer=layer)

    def add_polyline(
        self,
        points: List[Tuple[float, float]],
        is_closed: bool = False,
        layer: str = "0_粗实线",
    ):
        """Draw a lightweight polyline (LWPOLYLINE)."""
        return self.msp.add_lwpolyline(
            points,
            close=is_closed,
            dxfattribs={"layer": layer},
        )

    def add_centerline(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        extension: float = 5.0,
        layer: str = "2_中心线",
    ):
        """Draw a centerline extended beyond endpoints."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length > 0:
            ux = dx / length
            uy = dy / length
            ep1 = (p1[0] - ux * extension, p1[1] - uy * extension)
            ep2 = (p2[0] + ux * extension, p2[1] + uy * extension)
        else:
            ep1, ep2 = p1, p2
        return self.msp.add_line(ep1, ep2, dxfattribs={"layer": layer})

    def add_cross_centerlines(
        self,
        center: Tuple[float, float],
        radius: float,
        extension: float = 4.0,
        layer: str = "2_中心线",
    ):
        """Draw standard cross centerlines for a circle or hole."""
        ext_r = radius + extension
        cx, cy = center
        h_line = self.msp.add_line(
            (cx - ext_r, cy),
            (cx + ext_r, cy),
            dxfattribs={"layer": layer},
        )
        v_line = self.msp.add_line(
            (cx, cy - ext_r),
            (cx, cy + ext_r),
            dxfattribs={"layer": layer},
        )
        return [h_line, v_line]

    def add_text(
        self,
        text: str,
        insert: Tuple[float, float],
        height: float = 3.5,
        layer: str = "6_文字说明",
        rotation: float = 0.0,
        align: str = "LEFT",
    ):
        """Add single-line text with GB standard font."""
        txt = self.msp.add_text(
            text,
            dxfattribs={
                "layer": layer,
                "height": height,
                "style": "GB_STYLE",
                "rotation": rotation,
            },
        )
        alignment_map = {
            "LEFT": TextEntityAlignment.LEFT,
            "CENTER": TextEntityAlignment.MIDDLE_CENTER,
            "RIGHT": TextEntityAlignment.RIGHT,
            "TOP_LEFT": TextEntityAlignment.TOP_LEFT,
            "BOTTOM_LEFT": TextEntityAlignment.BOTTOM_LEFT,
        }
        txt.set_placement(insert, align=alignment_map.get(align, TextEntityAlignment.LEFT))
        return txt

    # -------------------------------------------------------------
    # Dimensioning (尺寸标注)
    # -------------------------------------------------------------

    def add_dimension_linear(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        offset: float = 10.0,
        dim_type: str = "HORIZONTAL",
        override_text: Optional[str] = None,
        layer: str = "4_尺寸标注",
    ):
        """
        Add horizontal or vertical linear dimension.
        dim_type: 'HORIZONTAL', 'VERTICAL', or 'ALIGNED'
        offset: distance of dimension line from the measured points (positive or negative)
        """
        if dim_type == "HORIZONTAL":
            y_base = max(p1[1], p2[1]) + offset if offset >= 0 else min(p1[1], p2[1]) + offset
            base = ((p1[0] + p2[0]) / 2, y_base)
            dim = self.msp.add_linear_dim(
                base=base,
                p1=p1,
                p2=p2,
                angle=0,
                text=override_text,
                dimstyle="GB_DIMSTYLE",
                dxfattribs={"layer": layer},
            )
        elif dim_type == "VERTICAL":
            x_base = max(p1[0], p2[0]) + offset if offset >= 0 else min(p1[0], p2[0]) + offset
            base = (x_base, (p1[1] + p2[1]) / 2)
            dim = self.msp.add_linear_dim(
                base=base,
                p1=p1,
                p2=p2,
                angle=90,
                text=override_text,
                dimstyle="GB_DIMSTYLE",
                dxfattribs={"layer": layer},
            )
        else:  # ALIGNED
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length > 0:
                nx = -dy / length * offset
                ny = dx / length * offset
            else:
                nx, ny = 0, offset
            base = ((p1[0] + p2[0]) / 2 + nx, (p1[1] + p2[1]) / 2 + ny)
            dim = self.msp.add_aligned_dim(
                p1=p1,
                p2=p2,
                distance=offset,
                text=override_text,
                dimstyle="GB_DIMSTYLE",
                dxfattribs={"layer": layer},
            )
        dim.render()
        return dim

    def add_dimension_diameter(
        self,
        center: Tuple[float, float],
        radius: float,
        angle_deg: float = 45.0,
        override_text: Optional[str] = None,
        layer: str = "4_尺寸标注",
    ):
        """Add diameter dimension line for a circle (e.g. Φ50)."""
        text = override_text if override_text else f"Φ{radius * 2:.1f}".rstrip('0').rstrip('.')
        dim = self.msp.add_diameter_dim(
            center=center,
            radius=radius,
            angle=angle_deg,
            text=text,
            dimstyle="GB_DIMSTYLE",
            dxfattribs={"layer": layer},
        )
        dim.render()
        return dim

    def add_dimension_radius(
        self,
        center: Tuple[float, float],
        radius: float,
        angle_deg: float = 45.0,
        override_text: Optional[str] = None,
        layer: str = "4_尺寸标注",
    ):
        """Add radius dimension line (e.g. R15)."""
        text = override_text if override_text else f"R{radius:.1f}".rstrip('0').rstrip('.')
        dim = self.msp.add_radius_dim(
            center=center,
            radius=radius,
            angle=angle_deg,
            text=text,
            dimstyle="GB_DIMSTYLE",
            dxfattribs={"layer": layer},
        )
        dim.render()
        return dim

    # -------------------------------------------------------------
    # Chinese National Standard Frame & Title Block (GB/T 14665)
    # -------------------------------------------------------------

    def add_gb_frame_and_titleblock(
        self,
        paper_size: str = "A3",
        title: str = "零件图",
        part_no: str = "PART-001",
        material: str = "45",
        scale_text: str = "1:1",
        designer: str = "AI Designer",
        checker: str = "",
        weight: str = "",
        tech_notes: Optional[List[str]] = None,
    ):
        """
        Draw standard GB drawing frame and standard title block (GB/T 10609.1).
        Title block dimensions: 180mm (width) x 56mm (height) located at the bottom-right corner.
        """
        if paper_size not in self.PAPER_SIZES:
            paper_size = "A3"
        self.paper_size = paper_size
        cfg = self.PAPER_SIZES[paper_size]
        w, h = cfg["w"], cfg["h"]
        ml, mo = cfg["margin_left"], cfg["margin_other"]

        # Outer paper border
        self.add_rectangle((0, 0), (w, h), layer="1_细实线")

        # Inner drawing area border (thick line according to GB)
        x_min, y_min = ml, mo
        x_max, y_max = w - mo, h - mo
        self.add_rectangle((x_min, y_min), (x_max, y_max), layer="7_图框标题栏")

        # Standard Title Block (180mm x 56mm at bottom-right corner)
        tb_w = 180.0
        tb_h = 56.0
        tb_x = x_max - tb_w
        tb_y = y_min

        # Title block outer border
        self.add_rectangle((tb_x, tb_y), (x_max, tb_y + tb_h), layer="7_图框标题栏")

        # Horizontal partition lines
        y_lines = [7, 14, 21, 28, 44]
        for y_off in y_lines:
            self.add_line((tb_x, tb_y + y_off), (x_max, tb_y + y_off), layer="1_细实线")

        # Vertical partition lines
        self.add_line((tb_x + 65, tb_y), (tb_x + 65, tb_y + 44), layer="1_细实线")
        self.add_line((tb_x + 15, tb_y), (tb_x + 15, tb_y + 44), layer="1_细实线")
        self.add_line((tb_x + 35, tb_y), (tb_x + 35, tb_y + 44), layer="1_细实线")
        self.add_line((tb_x + 50, tb_y), (tb_x + 50, tb_y + 44), layer="1_细实线")

        self.add_line((tb_x + 115, tb_y), (tb_x + 115, tb_y + 56), layer="1_细实线")
        self.add_line((tb_x + 130, tb_y), (tb_x + 130, tb_y + 44), layer="1_细实线")
        self.add_line((tb_x + 150, tb_y), (tb_x + 150, tb_y + 44), layer="1_细实线")
        self.add_line((tb_x + 165, tb_y), (tb_x + 165, tb_y + 44), layer="1_细实线")

        # Signatures
        self.add_text("设计", (tb_x + 2, tb_y + 37), height=2.5, align="LEFT")
        self.add_text(designer, (tb_x + 17, tb_y + 37), height=2.5, align="LEFT")
        self.add_text("校核", (tb_x + 2, tb_y + 30), height=2.5, align="LEFT")
        self.add_text(checker, (tb_x + 17, tb_y + 30), height=2.5, align="LEFT")
        self.add_text("标准化", (tb_x + 2, tb_y + 23), height=2.5, align="LEFT")
        self.add_text("审定", (tb_x + 2, tb_y + 16), height=2.5, align="LEFT")
        self.add_text("批准", (tb_x + 2, tb_y + 9), height=2.5, align="LEFT")

        # Part Title
        self.add_text(title, (tb_x + 57, tb_y + 47), height=5.0, align="CENTER")

        # Drawing Number / Part Number
        self.add_text(part_no, (tb_x + 147, tb_y + 48), height=3.5, align="CENTER")

        # Material & Scale
        self.add_text("材料", (tb_x + 67, tb_y + 16), height=2.5, align="LEFT")
        self.add_text(material, (tb_x + 85, tb_y + 16), height=3.0, align="LEFT")

        self.add_text("比例", (tb_x + 117, tb_y + 16), height=2.5, align="LEFT")
        self.add_text(scale_text, (tb_x + 135, tb_y + 16), height=3.0, align="LEFT")

        self.add_text("重量", (tb_x + 117, tb_y + 9), height=2.5, align="LEFT")
        self.add_text(weight if weight else "-", (tb_x + 135, tb_y + 9), height=3.0, align="LEFT")

        # Technical Requirements
        if tech_notes:
            note_x = tb_x - 10.0
            note_y = tb_y + tb_h + 15.0
            self.add_text("技术要求：", (note_x, note_y), height=4.0, align="RIGHT")
            cur_y = note_y - 6.0
            for i, note in enumerate(tech_notes, 1):
                self.add_text(f"{i}. {note}", (note_x, cur_y), height=3.0, align="RIGHT")
                cur_y -= 5.5

        return {
            "paper_size": paper_size,
            "drawing_area": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
            "title_block": {"x": tb_x, "y": tb_y, "width": tb_w, "height": tb_h},
        }

    # -------------------------------------------------------------
    # Parametric Mechanical Parts Generation
    # -------------------------------------------------------------

    def generate_stepped_shaft(
        self,
        origin: Tuple[float, float],
        steps: List[Dict[str, float]],
        chamfer_left: float = 1.0,
        chamfer_right: float = 1.0,
        add_centerline: bool = True,
        add_dimensions: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a multi-stepped shaft (阶梯轴).
        steps: list of dicts: [{'d': diameter, 'l': length}]
        e.g. [{'d': 30, 'l': 40}, {'d': 45, 'l': 60}, {'d': 40, 'l': 50}]
        """
        ox, oy = origin
        total_length = sum(s["l"] for s in steps)
        max_d = max(s["d"] for s in steps)

        # Draw Centerline
        if add_centerline:
            self.add_centerline(
                (ox, oy),
                (ox + total_length, oy),
                extension=10.0,
            )

        cur_x = ox
        prev_r = 0.0

        for i, s in enumerate(steps):
            d, l = s["d"], s["l"]
            r = d / 2.0
            next_x = cur_x + l

            top_y = oy + r
            bot_y = oy - r

            start_x = cur_x
            end_x = next_x
            c_left = chamfer_left if i == 0 else 0.0
            c_right = chamfer_right if i == len(steps) - 1 else 0.0

            if c_left > 0:
                self.add_line((start_x + c_left, top_y), (start_x, top_y - c_left))
                self.add_line((start_x + c_left, bot_y), (start_x, bot_y + c_left))
                self.add_line((start_x, top_y - c_left), (start_x, bot_y + c_left))
                start_x += c_left

            if c_right > 0:
                self.add_line((end_x - c_right, top_y), (end_x, top_y - c_right))
                self.add_line((end_x - c_right, bot_y), (end_x, bot_y + c_right))
                self.add_line((end_x, top_y - c_right), (end_x, bot_y + c_right))
                end_x -= c_right

            self.add_line((start_x, top_y), (end_x, top_y))
            self.add_line((start_x, bot_y), (end_x, bot_y))

            if i > 0:
                self.add_line((cur_x, oy + prev_r), (cur_x, top_y))
                self.add_line((cur_x, oy - prev_r), (cur_x, bot_y))

            if add_dimensions:
                dim_offset = 12.0 + (i % 2) * 8.0
                self.add_dimension_linear(
                    (cur_x, bot_y),
                    (cur_x, top_y),
                    offset=-dim_offset,
                    dim_type="VERTICAL",
                    override_text=f"%%c{d:.1f}".rstrip('0').rstrip('.'),
                )
                self.add_dimension_linear(
                    (cur_x, top_y),
                    (next_x, top_y),
                    offset=12.0 + (i % 2) * 8.0,
                    dim_type="HORIZONTAL",
                    override_text=f"{l:.1f}".rstrip('0').rstrip('.'),
                )

            prev_r = r
            cur_x = next_x

        if add_dimensions and len(steps) > 1:
            self.add_dimension_linear(
                (ox, oy + max_d / 2),
                (ox + total_length, oy + max_d / 2),
                offset=30.0,
                dim_type="HORIZONTAL",
                override_text=f"{total_length:.1f}".rstrip('0').rstrip('.'),
            )

        return {
            "part_type": "stepped_shaft",
            "total_length": total_length,
            "max_diameter": max_d,
            "bbox": (ox, oy - max_d / 2, ox + total_length, oy + max_d / 2),
        }

    def generate_flange(
        self,
        origin: Tuple[float, float],
        outer_d: float,
        inner_d: float,
        pcd: float,
        bolt_d: float,
        bolt_num: int = 4,
        flange_thickness: float = 20.0,
        hub_d: float = 0.0,
        hub_h: float = 0.0,
        add_dimensions: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate standard Flange (法兰盘):
        Left: Sectional Front View (剖视主视图)
        Right: Top View with Bolt Circle (俯视图含螺栓孔分布)
        """
        ox, oy = origin
        gap = 40.0
        # 1. Front View (Left)
        fv_cx = ox + outer_d / 2.0
        fv_cy = oy
        self.add_centerline((fv_cx, fv_cy - outer_d / 2 - 10), (fv_cx, fv_cy + outer_d / 2 + 10))

        f_left = fv_cx - flange_thickness / 2.0
        f_right = fv_cx + flange_thickness / 2.0
        self.add_rectangle((f_left, fv_cy + inner_d / 2), (f_right, fv_cy + outer_d / 2))
        self.add_rectangle((f_left, fv_cy - outer_d / 2), (f_right, fv_cy - inner_d / 2))

        for sign in [1, -1]:
            b_cy = fv_cy + sign * (pcd / 2.0)
            self.add_line((f_left, b_cy + bolt_d / 2), (f_right, b_cy + bolt_d / 2), layer="3_虚线")
            self.add_line((f_left, b_cy - bolt_d / 2), (f_right, b_cy - bolt_d / 2), layer="3_虚线")
            self.add_centerline((f_left - 3, b_cy), (f_right + 3, b_cy))

        # 2. Top View (Right)
        tv_cx = ox + outer_d + gap + outer_d / 2.0
        tv_cy = oy
        self.add_cross_centerlines((tv_cx, tv_cy), outer_d / 2.0, extension=8.0)
        self.add_circle((tv_cx, tv_cy), outer_d / 2.0)
        self.add_circle((tv_cx, tv_cy), inner_d / 2.0)
        self.add_circle((tv_cx, tv_cy), pcd / 2.0, layer="2_中心线")

        for i in range(bolt_num):
            angle = (360.0 / bolt_num) * i
            rad = math.radians(angle)
            bx = tv_cx + (pcd / 2.0) * math.cos(rad)
            by = tv_cy + (pcd / 2.0) * math.sin(rad)
            self.add_circle((bx, by), bolt_d / 2.0, add_centerline=True)

        if add_dimensions:
            self.add_dimension_diameter((tv_cx, tv_cy), outer_d / 2.0, angle_deg=45)
            self.add_dimension_diameter((tv_cx, tv_cy), inner_d / 2.0, angle_deg=135)
            self.add_dimension_linear((f_left, fv_cy + outer_d / 2), (f_right, fv_cy + outer_d / 2), offset=10)

        return {
            "part_type": "flange",
            "outer_diameter": outer_d,
            "inner_diameter": inner_d,
            "pcd": pcd,
            "bolt_count": bolt_num,
        }

    def generate_mounting_plate(
        self,
        origin: Tuple[float, float],
        length: float,
        width: float,
        thickness: float,
        corner_radius: float = 5.0,
        corner_holes_d: float = 9.0,
        hole_margin: float = 15.0,
        center_hole_d: float = 30.0,
        add_dimensions: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate rectangular mounting plate with corner bolt holes and center bore.
        """
        ox, oy = origin
        p1 = (ox, oy)
        p2 = (ox + length, oy + width)
        self.add_rectangle(p1, p2)

        cx = ox + length / 2.0
        cy = oy + width / 2.0
        self.add_centerline((ox - 5, cy), (ox + length + 5, cy))
        self.add_centerline((cx, oy - 5), (cx, oy + width + 5))

        if center_hole_d > 0:
            self.add_circle((cx, cy), center_hole_d / 2.0, add_centerline=True)

        if corner_holes_d > 0:
            holes = [
                (ox + hole_margin, oy + hole_margin),
                (ox + length - hole_margin, oy + hole_margin),
                (ox + length - hole_margin, oy + width - hole_margin),
                (ox + hole_margin, oy + width - hole_margin),
            ]
            for hx, hy in holes:
                self.add_circle((hx, hy), corner_holes_d / 2.0, add_centerline=True)

        if add_dimensions:
            self.add_dimension_linear((ox, oy), (ox + length, oy), offset=-12.0)
            self.add_dimension_linear((ox, oy), (ox, oy + width), offset=-12.0, dim_type="VERTICAL")
            self.add_dimension_linear((ox, oy), (ox + hole_margin, oy), offset=-20.0)
            if center_hole_d > 0:
                self.add_dimension_diameter((cx, cy), center_hole_d / 2.0, angle_deg=45)

        return {
            "part_type": "mounting_plate",
            "length": length,
            "width": width,
            "thickness": thickness,
            "center_hole": center_hole_d,
        }

    # -------------------------------------------------------------
    # Output and Save
    # -------------------------------------------------------------

    def save(self, filepath: str) -> str:
        """Save DXF drawing to specified file path."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        self.doc.saveas(filepath)
        return os.path.abspath(filepath)
