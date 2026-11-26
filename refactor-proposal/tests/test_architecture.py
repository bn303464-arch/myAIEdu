"""계층 의존 방향이 지켜지는지 import 문으로 검사한다."""
import ast
import pathlib
import unittest

BACK = pathlib.Path(__file__).resolve().parent.parent / "src" / "back"

# 계층: import하면 안 되는 최상위 모듈
FORBIDDEN = {
    "models": {"services", "repositories", "routers", "web", "config", "server", "sqlite3", "http", "json"},
    "services": {"repositories", "routers", "web", "config", "server", "sqlite3", "http", "json"},
    "repositories": {"services", "routers", "web", "server", "http"},
    "routers": {"repositories", "server", "sqlite3", "http"},
    "web": {"services", "repositories", "routers", "server", "sqlite3"},
}


def imported_modules(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split(".")[0]


def child_names(directory, pattern="*"):
    return {p.name for p in directory.glob(pattern) if p.name != "__pycache__"}


class StructureTest(unittest.TestCase):
    def test_code_lives_only_in_src(self):
        root = BACK.parent.parent
        self.assertEqual(child_names(root, "*.py"), set(), "루트에 파이썬 파일 금지")
        self.assertFalse((root / "static").exists(), "프론트 파일은 src/front에 둔다")
        self.assertEqual(child_names(BACK.parent), {"back", "front"})

    def test_backend_has_only_known_layers(self):
        self.assertEqual(child_names(BACK, "*.py"), {"server.py", "config.py"})
        self.assertEqual({p.name for p in BACK.iterdir() if p.is_dir()} - {"__pycache__"},
                         set(FORBIDDEN))


class DependencyTest(unittest.TestCase):
    def test_layers_depend_inward_only(self):
        for layer, banned in FORBIDDEN.items():
            files = list((BACK / layer).glob("*.py"))
            self.assertTrue(files, layer)
            for path in files:
                bad = banned & set(imported_modules(path))
                self.assertFalse(bad, f"{layer}/{path.name} → {sorted(bad)}")


if __name__ == "__main__":
    unittest.main()
