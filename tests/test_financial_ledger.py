"""
Юніт-тести фінансового симулятора на синтетичних даних (НЕ реальний проєкт).
Очікувані числа пораховано вручну:
  synthetic_pass: ncloc=100000, sqale_index=120000 хв (2000 год), rate=40, overload=1.3, r=0.01
    Тіло боргу = 2000 * 40 * 1.3 = 104000
    CoD        = 100000/100 * 40 = 40000 / міс
    NPV_1 = 40000/1.01 - 104000            = -64396.04
    NPV_2 = NPV_1 + 40000/1.01^2           = -25184.20
    NPV_3 = NPV_2 + 40000/1.01^3           =  13639.41  -> окупність на 3-му місяці
Запуск:  python3 -m unittest discover -s tests -v
"""
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("fl", ROOT / "tools" / "financial_ledger.py")
fl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fl)


class FormulaTest(unittest.TestCase):
    def test_principal(self):
        self.assertAlmostEqual(fl.principal(120000, 40, 1.3), 104000.0)

    def test_cost_of_delay(self):
        self.assertAlmostEqual(fl.cost_of_delay(100000, 40), 40000.0)

    def test_npv_and_payback(self):
        rows, payback = fl.npv_schedule(40000.0, 104000.0, 0.01)
        self.assertEqual(len(rows), 6)
        self.assertAlmostEqual(rows[0]["npv"], -64396.04, places=2)
        self.assertAlmostEqual(rows[1]["npv"], -25184.20, places=2)
        self.assertAlmostEqual(rows[2]["npv"], 13639.41, places=2)
        self.assertAlmostEqual(rows[2]["factor"], 1 / 1.01 ** 3)
        self.assertEqual(payback, 3)

    def test_no_payback(self):
        # ncloc=10000, 1000 год боргу: CoD=4000/міс, тіло=52000 -> за 6 міс не окупається
        rows, payback = fl.npv_schedule(fl.cost_of_delay(10000, 40), fl.principal(60000, 40, 1.3), 0.01)
        self.assertIsNone(payback)
        self.assertLess(rows[-1]["npv"], 0)


class CliTest(unittest.TestCase):
    def run_cli(self, fixture, tmp_root):
        env = dict(os.environ, HOURLY_RATE="40", OVERLOAD_COEFF="1.3", DISCOUNT_RATE="0.01")
        return subprocess.run([sys.executable, str(ROOT / "tools" / "financial_ledger.py"),
                               str(ROOT / "tests" / "fixtures" / fixture)],
                              capture_output=True, text=True, env=env)

    def test_cli_pass_reads_json_dynamically(self):
        ledger = ROOT / "FINANCIAL_LEDGER.md"
        backup = ledger.read_text(encoding="utf-8") if ledger.exists() else None
        try:
            res = self.run_cli("synthetic-pass.json", ROOT)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            text = ledger.read_text(encoding="utf-8")
            self.assertIn("synthetic_pass", text)
            self.assertIn("**3-му місяці**", text)
            self.assertIn("**PASS**", text)
            res = self.run_cli("synthetic-fail.json", ROOT)
            self.assertEqual(res.returncode, 1)
            self.assertIn("**FAIL**", ledger.read_text(encoding="utf-8"))
        finally:
            if backup is None:
                ledger.unlink(missing_ok=True)
            else:
                ledger.write_text(backup, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
