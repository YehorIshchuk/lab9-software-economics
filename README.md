# Lab 9 — SQALE, Software Economics, FPA & UCP

Об'єкт аудиту: **Apache OFBiz** (ERP на Java) — SonarQube Cloud key `apache_ofbiz-framework`,
репозиторій https://github.com/apache/ofbiz-framework.

| Завдання | Як запустити | Результат |
|---|---|---|
| 1. SQALE-аудит через Cloud API | `./scripts/fetch_sonarcloud.sh` → `python3 tools/sqale_audit.py` | `report.json`, `data/api-call.log`, `SQALE_AUDIT.md` |
| 2. Фінансовий симулятор NPV | `HOURLY_RATE=40 OVERLOAD_COEFF=1.3 DISCOUNT_RATE=0.01 python3 tools/financial_ledger.py` | `FINANCIAL_LEDGER.md` |
| 3. FPA / UCP / калібрування | `fpa-ucp/FPA_UCP_Calculator.xlsx`, `python3 tools/git_effort.py <ofbiz> <файли>` | FP, UCP, PF |

Тести симулятора: `python3 -m unittest discover -s tests -v`.
Звіт: [docs/LAB9_REPORT.md](docs/LAB9_REPORT.md) · покрокова інструкція: [docs/DEMO_LAB9.md](docs/DEMO_LAB9.md).
Потрібен лише Python 3.9+ (без сторонніх бібліотек) і curl.
