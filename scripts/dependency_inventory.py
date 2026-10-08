"""Installed-package license metadata only; no credentials or environment read."""

import importlib.metadata
import json
from collections import Counter
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    frontend = root / "frontend"
    manifest = json.loads((frontend / "package.json").read_text(encoding="utf-8"))
    direct = set(manifest["dependencies"]) | set(manifest["devDependencies"])
    packages = {}
    graph = json.loads((root / "docs/frontend_resolved_graph.json").read_text(encoding="utf-8-sig"))
    resolved_paths = set()

    def visit(node):
        for group in ("dependencies", "devDependencies", "optionalDependencies"):
            for dependency in node.get(group, {}).values():
                if dependency.get("path"):
                    resolved_paths.add(Path(dependency["path"]) / "package.json")
                visit(dependency)

    for project in graph:
        visit(project)
    for package_file in sorted(resolved_paths):
        try:
            metadata = json.loads(package_file.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        name, version = metadata.get("name"), metadata.get("version")
        if not name or not version or "node_modules" not in package_file.parent.parts:
            continue
        license_value = metadata.get("license") or metadata.get("licenses") or "UNVERIFIED"
        if not isinstance(license_value, str):
            license_value = json.dumps(license_value, ensure_ascii=False)
        packages[(name, version)] = {"name": name, "version": version, "license": license_value, "direct": name in direct, "metadata_path": str(package_file.relative_to(root))}
    python = []
    for distribution in importlib.metadata.distributions():
        metadata = distribution.metadata
        classifiers = [value for value in metadata.get_all("Classifier", []) if value.startswith("License ::")]
        license_value = metadata.get("License-Expression") or metadata.get("License") or "; ".join(classifiers) or "UNVERIFIED"
        python.append({"name": metadata["Name"], "version": distribution.version, "license": license_value, "license_files": metadata.get_all("License-File", [])})
    result = {"scope": "installed frontend and independent backend; upstream Python/Rust not installed", "frontend": sorted(packages.values(), key=lambda item: (item["name"], item["version"])), "backend": sorted(python, key=lambda item: item["name"])}
    (root / "docs/dependency_licenses.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"frontend_packages": len(packages), "frontend_licenses": dict(Counter(item["license"] for item in packages.values())), "backend_packages": len(python), "backend_unverified": [item["name"] for item in python if item["license"] == "UNVERIFIED"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
