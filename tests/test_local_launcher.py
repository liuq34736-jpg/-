import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_service", ROOT / "scripts/local-service.py")
local_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_service)


class LocalLauncherTests(unittest.TestCase):
    def test_backend_loopback_fixed_port(self):
        command, working_dir = local_service.service_command(ROOT, "backend", "node.exe")
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "8765")
        self.assertIn("backend.app.main:app", command)
        self.assertEqual(working_dir, ROOT)

    def test_frontend_loopback_strict_port(self):
        command, working_dir = local_service.service_command(ROOT, "frontend", r"C:\fake\node.exe")
        self.assertEqual(command[0], r"C:\fake\node.exe")
        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "5173")
        self.assertIn("--strictPort", command)
        self.assertEqual(working_dir, ROOT / "frontend")

    def test_invalid_service_rejected(self):
        with self.assertRaises(ValueError):
            local_service.service_command(ROOT, "unknown", "node.exe")

    def test_commands_do_not_start_legacy_app(self):
        for service in ("backend", "frontend"):
            command, _ = local_service.service_command(ROOT, service, "node.exe")
            self.assertNotIn("main.py", command)
            self.assertNotIn("0.0.0.0", command)
            self.assertNotIn("streamlit_mvp", " ".join(command))


if __name__ == "__main__":
    unittest.main()
