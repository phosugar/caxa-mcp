"""
CAXA MCP Server
Model Context Protocol (MCP) server providing AI agents with the ability to:
1. Parse drawing requirements and generate high-precision GB-compliant CAD drawings.
2. Control local CAXA CAD 2023 (launch, open drawings, send commands, screenshot).
"""

import os
import sys
import tempfile
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from .cad_engine import CADEngine
    from .caxa_controller import CAXAController
except ImportError:
    from cad_engine import CADEngine
    from caxa_controller import CAXAController

# Initialize FastMCP Server
mcp = FastMCP("caxa-cad-server")

# Global session state
DEFAULT_DRAWING_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "caxa_active_drawing.dxf"))
current_engine: Optional[CADEngine] = None
active_dxf_path: str = DEFAULT_DRAWING_PATH
controller = CAXAController()


def _get_or_create_engine() -> CADEngine:
    global current_engine
    if current_engine is None:
        current_engine = CADEngine()
        current_engine.add_gb_frame_and_titleblock(paper_size="A3", title="零件图")
        current_engine.save(active_dxf_path)
    return current_engine


@mcp.tool()
def caxa_status() -> Dict[str, Any]:
    """
    Check CAXA CAD installation and process status on the host machine.
    Returns executable path, whether running, active window title, and process IDs.
    """
    return controller.get_status()


@mcp.tool()
def caxa_launch() -> Dict[str, Any]:
    """
    Launch CAXA CAD 2023 if not running, or bring its window to the foreground.
    """
    return controller.launch()


@mcp.tool()
def caxa_create_drawing(
    paper_size: str = "A3",
    title: str = "零件图",
    part_no: str = "PART-001",
    material: str = "45",
    scale: str = "1:1",
    designer: str = "AI Designer",
    checker: str = "",
    weight: str = "",
    tech_notes: Optional[List[str]] = None,
    save_path: Optional[str] = None,
    auto_open: bool = True,
) -> Dict[str, Any]:
    """
    Initialize a brand new engineering drawing with Chinese National Standard (GB/T 14665)
    frame, layers (粗实线/细实线/中心线/虚线/尺寸标注/文字), and standard title block.

    Parameters:
    - paper_size: "A4", "A4_V", "A3", "A2", "A1", "A0"
    - title: Part name displayed in title block (e.g. "阶梯轴", "法兰盘", "箱体盖")
    - part_no: Drawing number (e.g. "PART-001")
    - material: Part material (e.g. "45", "HT200", "Q235", "6061-T6")
    - scale: Drawing scale (e.g. "1:1", "1:2", "2:1")
    - tech_notes: List of technical requirements (技术要求) lines
    - save_path: Custom file path for the .dxf file
    - auto_open: If True, opens/updates this drawing immediately in CAXA CAD
    """
    global current_engine, active_dxf_path

    current_engine = CADEngine()
    frame_info = current_engine.add_gb_frame_and_titleblock(
        paper_size=paper_size,
        title=title,
        part_no=part_no,
        material=material,
        scale_text=scale,
        designer=designer,
        checker=checker,
        weight=weight,
        tech_notes=tech_notes,
    )

    if save_path:
        active_dxf_path = os.path.abspath(save_path)
    else:
        active_dxf_path = DEFAULT_DRAWING_PATH

    saved_file = current_engine.save(active_dxf_path)

    open_result = None
    if auto_open:
        open_result = controller.open_drawing(saved_file)
        controller.zoom_extents()

    return {
        "status": "success",
        "file_path": saved_file,
        "paper_size": paper_size,
        "drawing_area": frame_info["drawing_area"],
        "opened_in_caxa": auto_open,
        "open_result": open_result,
    }


@mcp.tool()
def caxa_draw_primitives(
    entities: List[Dict[str, Any]],
    auto_save_and_open: bool = True,
) -> Dict[str, Any]:
    """
    Batch draw precision geometric primitives into the active CAD drawing.

    Supported entity types in `entities`:
    - Line: {"type": "line", "start": [x1, y1], "end": [x2, y2], "layer": "0_粗实线"}
    - Circle: {"type": "circle", "center": [cx, cy], "radius": r, "layer": "0_粗实线", "add_centerline": true}
    - Arc: {"type": "arc", "center": [cx, cy], "radius": r, "start_angle": deg1, "end_angle": deg2}
    - Rectangle: {"type": "rectangle", "p1": [x1, y1], "p2": [x2, y2], "layer": "0_粗实线"}
    - Polyline: {"type": "polyline", "points": [[x1, y1], [x2, y2], ...], "is_closed": true}
    - Centerline: {"type": "centerline", "p1": [x1, y1], "p2": [x2, y2], "extension": 5.0}
    - Text: {"type": "text", "text": "string", "insert": [x, y], "height": 3.5, "layer": "6_文字说明"}

    Standard layers:
    "0_粗实线" (0.35/0.5mm), "1_细实线" (0.18mm), "2_中心线" (红色点划线),
    "3_虚线" (黄色虚线), "4_尺寸标注", "5_剖面线", "6_文字说明"
    """
    global current_engine, active_dxf_path
    engine = _get_or_create_engine()

    drawn_count = 0
    errors = []

    for idx, ent in enumerate(entities):
        etype = ent.get("type", "").lower()
        layer = ent.get("layer", "0_粗实线")

        try:
            if etype == "line":
                engine.add_line(tuple(ent["start"]), tuple(ent["end"]), layer=layer)
                drawn_count += 1
            elif etype == "circle":
                engine.add_circle(
                    tuple(ent["center"]),
                    float(ent["radius"]),
                    layer=layer,
                    add_centerline=ent.get("add_centerline", False),
                )
                drawn_count += 1
            elif etype == "arc":
                engine.add_arc(
                    tuple(ent["center"]),
                    float(ent["radius"]),
                    float(ent["start_angle"]),
                    float(ent["end_angle"]),
                    layer=layer,
                )
                drawn_count += 1
            elif etype == "rectangle":
                engine.add_rectangle(tuple(ent["p1"]), tuple(ent["p2"]), layer=layer)
                drawn_count += 1
            elif etype == "polyline":
                pts = [tuple(p) for p in ent["points"]]
                engine.add_polyline(pts, is_closed=ent.get("is_closed", False), layer=layer)
                drawn_count += 1
            elif etype == "centerline":
                engine.add_centerline(
                    tuple(ent["p1"]),
                    tuple(ent["p2"]),
                    extension=float(ent.get("extension", 5.0)),
                )
                drawn_count += 1
            elif etype == "text":
                engine.add_text(
                    ent["text"],
                    tuple(ent["insert"]),
                    height=float(ent.get("height", 3.5)),
                    layer=ent.get("layer", "6_文字说明"),
                )
                drawn_count += 1
            else:
                errors.append(f"Unknown entity type: '{etype}' at index {idx}")
        except Exception as e:
            errors.append(f"Error drawing entity {idx} ({etype}): {str(e)}")

    saved_file = engine.save(active_dxf_path)

    open_res = None
    if auto_save_and_open:
        open_res = controller.open_drawing(saved_file)
        controller.zoom_extents()

    return {
        "status": "success",
        "entities_drawn": drawn_count,
        "errors": errors,
        "saved_path": saved_file,
        "opened_in_caxa": auto_save_and_open,
    }


@mcp.tool()
def caxa_draw_dimension(
    p1: List[float],
    p2: List[float],
    offset: float = 10.0,
    dim_type: str = "HORIZONTAL",
    override_text: Optional[str] = None,
    auto_save_and_open: bool = True,
) -> Dict[str, Any]:
    """
    Add engineering dimension to the active CAD drawing.

    Parameters:
    - p1, p2: [x, y] coordinates of points being dimensioned
    - offset: Perpendicular distance from measurement to dimension line (positive or negative)
    - dim_type: 'HORIZONTAL', 'VERTICAL', or 'ALIGNED'
    - override_text: Custom dimension text (e.g. "%%c50H7", "60±0.02", "4xM8")
    """
    engine = _get_or_create_engine()
    engine.add_dimension_linear(
        tuple(p1),
        tuple(p2),
        offset=offset,
        dim_type=dim_type.upper(),
        override_text=override_text,
    )
    saved_file = engine.save(active_dxf_path)
    if auto_save_and_open:
        controller.open_drawing(saved_file)
        controller.zoom_extents()

    return {
        "status": "success",
        "dim_type": dim_type,
        "p1": p1,
        "p2": p2,
        "saved_path": saved_file,
    }


@mcp.tool()
def caxa_draw_parametric_part(
    part_type: str,
    params: Dict[str, Any],
    origin: List[float] = [120.0, 150.0],
    auto_open: bool = True,
) -> Dict[str, Any]:
    """
    Instantly generate standard parametric mechanical components with dimensions and centerlines.

    Supported `part_type`:
    1. "stepped_shaft" (阶梯轴):
       params: {
         "steps": [{"d": 30, "l": 40}, {"d": 45, "l": 60}, {"d": 35, "l": 40}],
         "chamfer_left": 1.0,
         "chamfer_right": 1.0,
         "add_dimensions": True
       }
    2. "flange" (法兰盘):
       params: {
         "outer_d": 160.0,
         "inner_d": 50.0,
         "pcd": 120.0,
         "bolt_d": 14.0,
         "bolt_num": 4,
         "flange_thickness": 20.0,
         "add_dimensions": True
       }
    3. "mounting_plate" (安装底板):
       params: {
         "length": 200.0,
         "width": 120.0,
         "thickness": 15.0,
         "corner_radius": 5.0,
         "corner_holes_d": 11.0,
         "hole_margin": 15.0,
         "center_hole_d": 50.0,
         "add_dimensions": True
       }
    """
    engine = _get_or_create_engine()
    ox, oy = origin[0], origin[1]

    pt = part_type.lower()
    if pt in ["shaft", "stepped_shaft", "阶梯轴"]:
        res = engine.generate_stepped_shaft(
            origin=(ox, oy),
            steps=params.get("steps", [{"d": 30, "l": 40}, {"d": 45, "l": 60}]),
            chamfer_left=float(params.get("chamfer_left", 1.0)),
            chamfer_right=float(params.get("chamfer_right", 1.0)),
            add_dimensions=params.get("add_dimensions", True),
        )
    elif pt in ["flange", "法兰", "法兰盘"]:
        res = engine.generate_flange(
            origin=(ox, oy),
            outer_d=float(params.get("outer_d", 160.0)),
            inner_d=float(params.get("inner_d", 50.0)),
            pcd=float(params.get("pcd", 120.0)),
            bolt_d=float(params.get("bolt_d", 14.0)),
            bolt_num=int(params.get("bolt_num", 4)),
            flange_thickness=float(params.get("flange_thickness", 20.0)),
            add_dimensions=params.get("add_dimensions", True),
        )
    elif pt in ["plate", "mounting_plate", "底板", "盖板"]:
        res = engine.generate_mounting_plate(
            origin=(ox, oy),
            length=float(params.get("length", 180.0)),
            width=float(params.get("width", 120.0)),
            thickness=float(params.get("thickness", 15.0)),
            corner_radius=float(params.get("corner_radius", 5.0)),
            corner_holes_d=float(params.get("corner_holes_d", 9.0)),
            hole_margin=float(params.get("hole_margin", 15.0)),
            center_hole_d=float(params.get("center_hole_d", 40.0)),
            add_dimensions=params.get("add_dimensions", True),
        )
    else:
        raise ValueError(f"Unsupported part_type: {part_type}. Supported: 'stepped_shaft', 'flange', 'mounting_plate'")

    saved_file = engine.save(active_dxf_path)
    if auto_open:
        controller.open_drawing(saved_file)
        controller.zoom_extents()

    return {
        "status": "success",
        "part_type": pt,
        "details": res,
        "saved_path": saved_file,
    }


@mcp.tool()
def caxa_open_drawing(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Open any CAD drawing (.dxf, .dwg, .exb) inside CAXA CAD 2023.
    If file_path is omitted, opens the currently active drawing.
    """
    target = file_path if file_path else active_dxf_path
    res = controller.open_drawing(target)
    controller.zoom_extents()
    return res


@mcp.tool()
def caxa_send_command(command: str) -> Dict[str, Any]:
    """
    Send CAD command or keyboard shortcut directly to CAXA CAD's command line.
    (e.g. 'LINE', 'CIRCLE', 'ZOOM E', 'REGEN')
    """
    success = controller.send_command(command, press_enter=True)
    return {
        "command": command,
        "success": success,
    }


@mcp.tool()
def caxa_capture_screen(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Capture a screenshot of CAXA CAD's drawing canvas for AI visual inspection.
    """
    if not output_path:
        out = os.path.join(tempfile.gettempdir(), "caxa_viewport.png")
    else:
        out = output_path

    cap = controller.capture_screenshot(out)
    return {
        "success": cap is not None,
        "screenshot_path": cap,
    }


@mcp.tool()
def caxa_export_drawing(output_path: str) -> Dict[str, Any]:
    """
    Save or export the current drawing to a specific destination path.
    """
    engine = _get_or_create_engine()
    abs_out = os.path.abspath(output_path)
    engine.save(abs_out)
    return {
        "status": "success",
        "output_path": abs_out,
    }


def main():
    """Entry point for the CAXA MCP Server."""
    mcp.run()


if __name__ == "__main__":
    main()
