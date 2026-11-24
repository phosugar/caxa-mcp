"""Checks that client snippets preserve executable and CAXA paths."""

import json
from unittest import TestCase

from caxa_mcp.cli import _configuration


class ConfigurationTests(TestCase):
    def test_clients_can_use_the_same_executable(self):
        command = ["C:/工具 folder/caxa-mcp.exe"]
        caxa_path = "D:/中文 CAXA/CDRAFT_M.exe"

        generic = json.loads(_configuration("generic", command, caxa_path))
        vscode = json.loads(_configuration("vscode", command, caxa_path))
        opencode = json.loads(_configuration("opencode", command, caxa_path))
        codex = _configuration("codex", command, caxa_path)

        self.assertEqual(generic["mcpServers"]["caxa"]["command"], command[0])
        self.assertEqual(vscode["servers"]["caxa"]["command"], command[0])
        self.assertEqual(opencode["mcp"]["servers"]["caxa"]["command"], command)
        self.assertIn(f'command = "{command[0]}"', codex)
        self.assertIn(f'CAXA_PATH = "{caxa_path}"', codex)

    def test_module_launch_arguments_survive_in_the_snippet(self):
        command = ["C:/Python/python.exe", "-m", "caxa_mcp.server"]
        result = json.loads(_configuration("generic", command, None))
        self.assertEqual(result["mcpServers"]["caxa"], {"command": command[0], "args": command[1:]})
