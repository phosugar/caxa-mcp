"""Regression checks for the CAXA window workflow without a running editor."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from caxa_mcp import caxa_controller, server


class WindowWorkflowTests(TestCase):
    def test_failed_existing_window_does_not_start_another_instance(self):
        controller = caxa_controller.CAXAController()
        with TemporaryDirectory() as directory:
            drawing = Path(directory) / "图纸 sample.dxf"
            drawing.touch()
            with (
                patch.object(controller, "get_caxa_pids", return_value=[321]),
                patch.object(controller, "find_main_window", return_value=123),
                patch.object(controller, "get_status", return_value={}),
                patch.object(controller, "_owned_dialog", return_value=None),
                patch.object(caxa_controller.win32gui, "GetWindowText", return_value="CAXA - [old.dxf]"),
                patch.object(controller, "_submit_open_dialog", return_value="Open dialog unavailable"),
                patch.object(controller, "_start") as start,
            ):
                result = controller.open_drawing(str(drawing))
            self.assertFalse(result["success"])
            self.assertIsNone(result["opened_file"])
            self.assertTrue(result["reused_instance"])
            start.assert_not_called()

    def test_capture_does_not_grab_desktop_when_window_is_missing(self):
        controller = caxa_controller.CAXAController()
        with (
            patch.object(controller, "find_main_window", return_value=None),
            patch.object(caxa_controller.ImageGrab, "grab") as grab,
        ):
            self.assertIsNone(controller.capture_window())
            grab.assert_not_called()

    def test_preview_open_keeps_source_editable(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "drawing.dxf"
            source.write_bytes(b"first")
            with patch.object(server.controller, "open_drawing", return_value={"success": True}) as opened:
                server._open_generated_file(str(source))
                source.write_bytes(b"second")
                server._open_generated_file(str(source))
            first, second = (Path(call.args[0]) for call in opened.call_args_list)
            self.assertNotEqual(first, second)
            self.assertNotEqual(source, first)
            self.assertEqual(first.read_bytes(), b"first")
            self.assertEqual(second.read_bytes(), b"second")
