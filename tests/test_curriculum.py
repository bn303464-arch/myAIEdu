"""curriculum/ 강의 자료의 예시 코드가 규칙대로 동작하는지 검사한다.

예시 코드는 수강생이 앱 없이 단독으로 실행하는 교육 자료이므로,
표준 라이브러리만 쓰고 앱 코드를 import하지 않아야 한다.
"""
import ast
import contextlib
import importlib.util
import io
import json
import pathlib
import re
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "curriculum"

# 예시 코드에서 import하면 안 되는 앱 모듈. 이전 구조와 마이그레이션 후 구조를 모두 막는다.
APP_MODULES = {"db", "server", "src", "models", "services", "repositories", "routers", "web", "config"}


def load_module(relpath):
    path = CURRICULUM / relpath
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    # dataclass가 모듈을 sys.modules에서 찾으므로 등록해 둔다.
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def run_main(module, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CurriculumStructureTest(unittest.TestCase):
    def test_each_week_has_lecture_guide_and_examples(self):
        for week in ("week07", "week08"):
            d = CURRICULUM / week
            self.assertTrue((d / "lecture.md").is_file(), week)
            self.assertTrue((d / "practice-guide.md").is_file(), week)
            self.assertTrue(list((d / "examples").glob("*.py")), week)
            self.assertTrue(list((d / "examples").glob("*.html")), week)

    def test_examples_use_stdlib_only(self):
        stdlib = sys.stdlib_module_names
        for path in CURRICULUM.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    self.assertNotIn(name, APP_MODULES, f"{path.name}: 앱 코드 import 금지")
                    self.assertIn(name, stdlib, f"{path.name}: 표준 라이브러리만 사용")

    def test_html_examples_do_not_use_innerhtml(self):
        # 프론트엔드 규칙: 데이터는 textContent로만 넣는다.
        # 규칙을 설명하는 주석("innerHTML 금지")은 걸리지 않도록 실제 대입·호출 형태만 찾는다.
        for path in CURRICULUM.rglob("*.html"):
            self.assertIsNone(re.search(r"\.(innerHTML|outerHTML)\s*\+?=|insertAdjacentHTML\s*\(|document\.write\s*\(",
                                        path.read_text(encoding="utf-8")), path.name)


class BrandProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module("week07/examples/brand_profile.py")

    def test_sample_runs_and_prompt_has_hallucination_guard(self):
        code, out, _ = run_main(self.m)
        self.assertEqual(code, 0)
        self.assertIn("[확인 필요]", out)
        self.assertIn("반장을 위해", out)  # 받침 있는 단어 뒤에는 '을'

    def test_josa_follows_final_consonant(self):
        self.assertEqual(self.m.josa("코치", "을", "를"), "코치를")
        self.assertEqual(self.m.josa("반장", "을", "를"), "반장을")
        self.assertEqual(self.m.instrumental("체크리스트"), "체크리스트로")
        self.assertEqual(self.m.instrumental("방법"), "방법으로")
        self.assertEqual(self.m.instrumental("교육 매뉴얼"), "교육 매뉴얼로")  # ㄹ 받침은 '로'

    def test_default_banned_words_are_merged_without_duplicates(self):
        p = self.m.Profile.parse({"job": "a", "audience": "b", "problem": "c", "method": "d", "role": "e",
                                  "banned_words": "최고, 대박"})
        words = self.m.banned_words(p)
        self.assertEqual(words.count("최고"), 1)
        self.assertIn("대박", words)

    def test_missing_fields_are_reported_in_korean(self):
        with self.assertRaisesRegex(ValueError, "채워 주세요: audience"):
            self.m.Profile.parse({"job": "a", "problem": "c", "method": "d", "role": "e"})
        with self.assertRaisesRegex(ValueError, "숫자"):
            self.m.Profile.parse({"job": "a", "audience": "b", "problem": "c", "method": "d", "role": "e",
                                  "years": "이십년"})

    def test_bad_json_file_returns_error_code(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{ 잘못된 json")
        try:
            code, _, err = run_main(self.m, "--input", f.name)
        finally:
            pathlib.Path(f.name).unlink()
        self.assertEqual(code, 1)
        self.assertIn("JSON 형식", err)


class BusinessCanvasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module("week08/examples/business_canvas.py")

    def idea(self, **overrides):
        data = {"service_name": "s", "idea": "i", "customer": "c", "price": 300000, "unit_cost": 50000,
                "monthly_fixed_cost": 200000, "target_monthly_profit": 1000000}
        data.update(overrides)
        return self.m.Idea.parse(data)

    def test_lecture_example_numbers(self):
        # 강의록 3부 예시와 같은 값이어야 한다: 남는 돈 25만, 손익분기 1회, 목표 5회.
        nums = self.m.calculate(self.idea())
        self.assertEqual((nums.margin, nums.break_even_units, nums.target_units), (250000, 1, 5))
        self.assertIsNone(nums.feasible)

    def test_feasibility_against_monthly_capacity(self):
        self.assertTrue(self.m.calculate(self.idea(max_units_per_month=5)).feasible)
        self.assertFalse(self.m.calculate(self.idea(max_units_per_month=4)).feasible)

    def test_non_positive_margin_has_no_break_even(self):
        nums = self.m.calculate(self.idea(unit_cost=300000))
        self.assertIsNone(nums.break_even_units)
        self.assertIn("손해", self.m.numbers_report(self.idea(unit_cost=300000), nums))

    def test_money_accepts_commas_and_rejects_negatives(self):
        self.assertEqual(self.idea(price="300,000원").price, 300000)
        with self.assertRaisesRegex(ValueError, "0 이상"):
            self.idea(unit_cost=-1)
        with self.assertRaisesRegex(ValueError, "0보다"):
            self.idea(price=0)

    def test_sample_runs_and_prompt_has_source_guard(self):
        code, out, _ = run_main(self.m)
        self.assertEqual(code, 0)
        self.assertIn("손익분기 건수: 한 달 1건", out)
        self.assertIn("출처", out)

    def test_sample_file_is_valid(self):
        data = json.loads((CURRICULUM / "week08/examples/sample_idea.json").read_text(encoding="utf-8"))
        self.assertEqual(self.m.Idea.parse(data).service_name, data["service_name"])


if __name__ == "__main__":
    unittest.main()
