#!/usr/bin/env python3
"""
Завдання 2. Software Economics: фінансовий симулятор технічного боргу.

Вхід:
  * report.json - сира відповідь SonarQube Cloud (метрики sqale_index і ncloc);
  * змінні оточення:
      HOURLY_RATE    - погодинна ставка розробника, $/год (35-50), за замовчуванням 40
      OVERLOAD_COEFF - коефіцієнт накладних витрат компанії, за замовчуванням 1.3
      DISCOUNT_RATE  - щомісячний коефіцієнт знецінення грошей, за замовчуванням 0.01

Формули:
  Тіло боргу      = (sqale_index / 60) * HOURLY_RATE * OVERLOAD_COEFF
  Cost of Delay   = (ncloc / 100) * HOURLY_RATE        (1 год/міс втрат на кожні 100 рядків)
  NPV_t           = sum_{k=1..t} CoD / (1 + DISCOUNT_RATE)^k  -  Тіло боргу,   t = 1..6

Вихід: FINANCIAL_LEDGER.md у корені проєкту + підсумок у консолі.

Використання:
    HOURLY_RATE=40 OVERLOAD_COEFF=1.3 DISCOUNT_RATE=0.01 python3 tools/financial_ledger.py [report.json]
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HORIZON_MONTHS = 6          # дистанція моделювання грошових потоків
LINES_PER_LOST_HOUR = 100   # кожні 100 рядків коду = 1 втрачена інженерна година на місяць


# ----------------------------------------------------------------------------- вхідні дані

def read_env(name, default, low=None, high=None):
    """Зчитує числову змінну оточення; якщо її немає - бере значення за замовчуванням."""
    raw = os.environ.get(name)
    value = float(raw) if raw is not None else default
    source = "env" if raw is not None else "default"
    if (low is not None and value < low) or (high is not None and value > high):
        print(f"  Увага: {name}={value} поза рекомендованим діапазоном [{low}; {high}]")
    return value, source


def read_report(path):
    """Динамічно витягує sqale_index і ncloc із JSON-відповіді SonarQube Cloud."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "errors" in data:
        sys.exit(f"report.json містить помилку сервера: {data['errors']}")
    component = data["component"]
    measures = {m["metric"]: m["value"] for m in component["measures"]}
    try:
        return component["key"], int(measures["sqale_index"]), int(measures["ncloc"])
    except KeyError as missing:
        sys.exit(f"У report.json немає метрики {missing}")


# ----------------------------------------------------------------------------- розрахунок

def principal(sqale_index, hourly_rate, overload):
    """Тіло боргу: вартість повного виправлення системи прямо зараз."""
    return (sqale_index / 60) * hourly_rate * overload


def cost_of_delay(ncloc, hourly_rate):
    """Щомісячні збитки бізнесу від бездіяльності (FAIL-стан)."""
    return (ncloc / LINES_PER_LOST_HOUR) * hourly_rate


def npv_schedule(cod, debt_principal, discount_rate, months=HORIZON_MONTHS):
    """
    Кумулятивний NPV по місяцях (PASS-стан: після рефакторингу збитки CoD припиняються
    і стають щомісячним "прибутком"). Повертає рядки таблиці і місяць окупності (або None).
    """
    rows = []
    cumulative_pv = 0.0
    payback_month = None
    for t in range(1, months + 1):
        discount_factor = 1 / (1 + discount_rate) ** t
        discounted_cash_flow = cod * discount_factor
        cumulative_pv += discounted_cash_flow
        npv_t = cumulative_pv - debt_principal
        if npv_t > 0 and payback_month is None:
            payback_month = t
        rows.append({"month": t, "factor": discount_factor, "cash_flow": discounted_cash_flow,
                     "cumulative_pv": cumulative_pv, "npv": npv_t})
    return rows, payback_month


# ----------------------------------------------------------------------------- звіт

def money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}".replace(",", " ")


def build_ledger(key, ncloc, sqale_index, rate, overload, discount, debt, cod, rows, payback):
    status = "PASS" if payback is not None else "FAIL"
    lines = [
        "# SOFTWARE ECONOMICS & FINANCIAL QUALITY LEDGER",
        "",
        f"_Згенеровано автоматично: {datetime.now():%Y-%m-%d %H:%M}, `tools/financial_ledger.py`_",
        "",
        "## 1. Вхідні параметри аудиту (System Baseline)",
        "",
        "| Параметр | Значення |",
        "|---|---|",
        f"| Проєкт (key) | `{key}` |",
        f"| Масштаб системи (NCLOC) | {ncloc:,} рядків |".replace(",", " "),
        f"| Початковий технічний борг (SQALE Index) | {sqale_index:,} хв ({sqale_index / 60:,.1f} год) |".replace(",", " "),
        f"| HOURLY_RATE | ${rate:g}/год |",
        f"| OVERLOAD_COEFF | {overload:g} |",
        f"| DISCOUNT_RATE | {discount:g} ({discount * 100:g} % / міс) |",
        "",
        "## 2. Капіталізація інвестиційних маркерів",
        "",
        "| Маркер | Формула | Значення |",
        "|---|---|---|",
        f"| Тіло боргу (вартість рефакторингу) | ({sqale_index} / 60) × {rate:g} × {overload:g} | **{money(debt)}** |",
        f"| Щомісячні збитки від бездіяльності (Cost of Delay) | ({ncloc} / 100) × {rate:g} | **{money(cod)}** / міс |",
        "",
        f"## 3. Динаміка окупності інвестицій у часі ({HORIZON_MONTHS} ітерацій)",
        "",
        "| Місяць | Коефіцієнт дисконтування 1/(1+r)^t | Щомісячний прибуток (дисконтований CoD) | Кумулятивний PV | Кумулятивний NPV |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        marker = " ✅" if payback == r["month"] else ""
        lines.append(f"| {r['month']} | {r['factor']:.4f} | {money(r['cash_flow'])} | {money(r['cumulative_pv'])} | "
                     f"{money(r['npv'])}{marker} |")
    lines += ["", "## 4. Фінальний інженерно-економічний вердикт", ""]
    if payback is not None:
        lines.append(f"Точка виходу в нуль (Payback Period): окупність настане на **{payback}-му місяці** розробки. "
                     f"NPV через {HORIZON_MONTHS} міс: **{money(rows[-1]['npv'])}**.")
    else:
        lines.append(f"Інвестиції **не окупаються** за {HORIZON_MONTHS} міс: NPV на кінець горизонту "
                     f"{money(rows[-1]['npv'])}.")
        lines.append("")
        lines.append("> ⚠️ АРХІТЕКТУРНЕ ПОПЕРЕДЖЕННЯ: технічний борг занадто великий відносно масштабу системи. "
                     "Повний рефакторинг за один цикл економічно недоцільний - потрібен поетапний план "
                     "(пріоритезація модулів з найвищою щільністю боргу, Clean as You Code для нового коду).")
    lines += ["", f"## 5. СТАТУС ВОРІТ ЯКОСТІ (Quality Gate): **{status}**", ""]
    return "\n".join(lines), status


# ----------------------------------------------------------------------------- main

def main():
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "report.json"
    print("=== Software Economics simulator ===")
    rate, rate_src = read_env("HOURLY_RATE", 40.0, 35, 50)
    overload, overload_src = read_env("OVERLOAD_COEFF", 1.3)
    discount, discount_src = read_env("DISCOUNT_RATE", 0.01, 0, 1)
    print(f"HOURLY_RATE={rate:g} ({rate_src})  OVERLOAD_COEFF={overload:g} ({overload_src})  "
          f"DISCOUNT_RATE={discount:g} ({discount_src})")

    key, sqale_index, ncloc = read_report(report)
    print(f"Проєкт: {key}  |  ncloc={ncloc}  |  sqale_index={sqale_index} хв  (з {report.name})")

    debt = principal(sqale_index, rate, overload)
    cod = cost_of_delay(ncloc, rate)
    rows, payback = npv_schedule(cod, debt, discount)

    print(f"Тіло боргу: {money(debt)}   Cost of Delay: {money(cod)} / міс")
    for r in rows:
        print(f"  t={r['month']}  factor={r['factor']:.4f}  CF={money(r['cash_flow']):>14}  NPV={money(r['npv']):>16}")

    ledger, status = build_ledger(key, ncloc, sqale_index, rate, overload, discount, debt, cod, rows, payback)
    out = ROOT / "FINANCIAL_LEDGER.md"
    out.write_text(ledger, encoding="utf-8")

    if payback is not None:
        print(f"Payback Period: {payback}-й місяць")
    print(f"QUALITY GATE: {status}")
    print(f"✅ Фінансовий леджер успішно створено: {out}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
