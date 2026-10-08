"""Public brand, built assets and preview isolation regressions (no AI calls)."""

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


class BrandUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brand = json.loads((FRONTEND / "src/config/brand.json").read_text(encoding="utf-8"))

    def test_brand_identity(self):
        self.assertEqual(self.brand["name"], "问象纪")
        self.assertEqual(self.brand["englishName"], "WEN XIANG JI")
        self.assertEqual(self.brand["tagline"], "一事一问，观象明理")

    def test_three_brand_colors(self):
        self.assertEqual(self.brand["colors"], {
            "primary": "#253934", "background": "#F5F1E9", "accent": "#A34F41",
        })

    def test_config_only_has_public_brand_fields(self):
        self.assertEqual(set(self.brand), {"name", "englishName", "tagline", "description", "colors", "assets"})
        self.assertTrue(all(value.startswith("/brand/") for value in self.brand["assets"].values()))

    def test_title_is_built_from_brand_config(self):
        html = (FRONTEND / "dist/index.html").read_text(encoding="utf-8")
        self.assertIn(f'<title>{self.brand["name"]} · {self.brand["tagline"]}</title>', html)
        self.assertNotIn("__BRAND_", html)
        self.assertIn(f'content="{self.brand["colors"]["primary"]}"', html)

    def test_vector_assets_are_local_and_in_build(self):
        for asset in self.brand["assets"].values():
            relative = asset.lstrip("/")
            source = FRONTEND / "public" / relative
            self.assertEqual(source.read_bytes(), (FRONTEND / "dist" / relative).read_bytes())
            svg = ET.fromstring(source.read_bytes())
            self.assertEqual(svg.attrib["viewBox"], "0 0 64 64")
            self.assertFalse(any(node.tag.rsplit("}", 1)[-1] in {"script", "image", "foreignObject"} for node in svg.iter()))

    def test_favicon_has_no_external_dependency(self):
        html = (FRONTEND / "dist/index.html").read_text(encoding="utf-8")
        self.assertIn('type="image/svg+xml"', html)
        self.assertIn(f'href="{self.brand["assets"]["favicon"]}"', html)

    def test_csp_and_private_environment_prefix_retained(self):
        html = (FRONTEND / "dist/index.html").read_text(encoding="utf-8")
        self.assertIn("object-src 'none'", html)
        self.assertNotIn('__LOCAL_INLINE_SCRIPT_HASHES__', html)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", html)
        self.assertIn("connect-src 'self' ws://127.0.0.1:5173 ws://localhost:5173", html)
        vite = (FRONTEND / "vite.config.ts").read_text(encoding="utf-8")
        self.assertIn("envPrefix: 'LOCAL_PREVIEW_PUBLIC_'", vite)
        self.assertIn("strictPort: true", vite)
        self.assertIn("host: '127.0.0.1'", vite)
        self.assertNotIn("0.0.0.0", vite)

    def test_only_independent_preview_is_mounted(self):
        app = (FRONTEND / "src/App.tsx").read_text(encoding="utf-8")
        self.assertIn("return <PlatformPreview />", app)
        self.assertNotIn("DivinationForm", app)

    def test_liuyao_is_ui_placeholder_not_backend_feature(self):
        registry = (FRONTEND / "src/config/modules.ts").read_text(encoding="utf-8")
        self.assertIn("id: 'liuyao', name: '六爻'", registry)
        backend = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
        self.assertNotIn('"liuyao"', backend)

    def test_upstream_license_retained(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2023 dreamhunter2333", license_text)
        self.assertIn("Permission is hereby granted", license_text)


if __name__ == "__main__":
    unittest.main()
