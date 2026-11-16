#!/usr/bin/env python3
"""
Завдання 1. Математична паспортизація технічного боргу за стандартом SQALE.

Зчитує report.json (сиру відповідь SonarQube Cloud api/measures/component) і рахує:
  * борг у людино-годинах і людино-днях (sqale_index / 60 / 8);
  * повний час розробки системи з нуля (ncloc * 30 хв / 60 = ncloc * 0.5 год);
  * індекс щільності боргу TDD = борг_год / (ncloc * 0.5) * 100 %;
  * літерний рейтинг за шкалою SQALE і порівняння з sqale_rating від сервера.

Використання:  python3 tools/sqale_audit.py [report.json]
Результат:     SQALE_AUDIT.md у корені проєкту.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MINUTES_PER_LINE = 30          # стандартна вартість розробки 1 рядка за SQALE
HOURS_PER_DAY = 8
# Шкала SQALE (як у SonarQube): верхня межа TDD у % для кожної літери
RATING_SCALE = [("A", 5), ("B", 10), ("C", 20), ("D", 50), ("E", float("inf"))]
NUMERIC_TO_LETTER = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}


def load_measures(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "errors" in data:
        sys.exit(f"У report.json помилка сервера: {data['errors']}")
    component = data["component"]
    measures = {m["metric"]: m["value"] for m in component["measures"]}
    return component["key"], measures


def rating_for(tdd_percent):
    for letter, upper in RATING_SCALE:
        if tdd_percent <= upper:
            return letter
    return "E"


def main():
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "report.json"
    key, m = load_measures(report)

    ncloc = int(m["ncloc"])
    sqale_index = int(m["sqale_index"])                 # хвилини
    cloud_rating = NUMERIC_TO_LETTER[round(float(m["sqale_rating"]))]

    debt_hours = sqale_index / 60
    debt_days = debt_hours / HOURS_PER_DAY
    dev_hours = ncloc * MINUTES_PER_LINE / 60           # = ncloc * 0.5
    tdd = debt_hours / dev_hours * 100
    computed_rating = rating_for(tdd)
    verdict = "ЗБІГАЄТЬСЯ" if computed_rating == cloud_rating else "НЕ ЗБІГАЄТЬСЯ"

    lines = [
        "# SQALE AUDIT LEDGER",
        "",
        f"Проєкт: `{key}`  ",
        f"Джерело: `{report.name}` (SonarQube Cloud, api/measures/component)",
        "",
        "## Вхідні дані (сира відповідь сервера)",
        "",
        "| Метрика | Значення |",
        "|---|---|",
        f"| ncloc | {ncloc:,} рядків |".replace(",", " "),
        f"| sqale_index | {sqale_index:,} хв |".replace(",", " "),
        f"| sqale_rating | {m['sqale_rating']} ({cloud_rating}) |",
        "",
        "## Розрахунок",
        "",
        f"1. Борг у годинах: {sqale_index} / 60 = **{debt_hours:,.1f} люд.-год**".replace(",", " "),
        f"2. Борг у робочих днях: {debt_hours:.1f} / 8 = **{debt_days:,.1f} люд.-днів**".replace(",", " "),
        f"3. Час розробки з нуля: {ncloc} × 30 / 60 = **{dev_hours:,.1f} год**".replace(",", " "),
        f"4. TDD = {debt_hours:.1f} / {dev_hours:.1f} × 100 % = **{tdd:.2f} %**",
        "",
        "## SQALE Audit Ledger",
        "",
        "| Масштаб (ncloc) | Обсяг боргу (люд.-год / роб. днів) | TDD (%) | Рейтинг за TDD | Хмарний рейтинг | Верифікація |",
        "|---|---|---|---|---|---|",
        f"| {ncloc:,} | {debt_hours:,.1f} / {debt_days:,.1f} | {tdd:.2f} | {computed_rating} | {cloud_rating} | {verdict} |".replace(",", " "),
        "",
        "Шкала SQALE: A ≤ 5 %, B 5–10 %, C 10–20 %, D 20–50 %, E > 50 %.",
        "",
    ]
    out = ROOT / "SQALE_AUDIT.md"
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"Проєкт: {key}")
    print(f"ncloc = {ncloc}, sqale_index = {sqale_index} хв, sqale_rating = {m['sqale_rating']} ({cloud_rating})")
    print(f"Борг: {debt_hours:.1f} люд.-год = {debt_days:.1f} люд.-днів")
    print(f"TDD = {tdd:.2f} % -> рейтинг {computed_rating}; хмарний рейтинг {cloud_rating}: {verdict}")
    print(f"Звіт збережено: {out.name}")


if __name__ == "__main__":
    main()
