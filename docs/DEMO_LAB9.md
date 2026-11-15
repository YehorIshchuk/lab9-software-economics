# ЛР9 — покрокова інструкція (macOS)

Потрібно лише: Термінал, `python3` (у тебе 3.14), `curl`, `git`. Docker і SonarQube на комп'ютері **не потрібні** —
дані беруться з хмарного SonarQube Cloud.

## 0. Підготовка
```bash
cd ~/Desktop
unzip ~/Downloads/lab9-software-economics.zip
cd lab9-software-economics
chmod +x scripts/*.sh tools/*.py
git log --oneline
```
Скріншоти зберігай файлами (**Cmd + Shift + 4**) і клади в `docs/img/`.

## 1. Завдання 1 — SQALE через Cloud API
```bash
./scripts/fetch_sonarcloud.sh
```
Очікувано: `GET https://sonarcloud.io/api/measures/component?...`, `HTTP 200`, відформатований JSON з `ncloc`,
`sqale_index`, `sqale_rating`. Перевір, що `ncloc` ≥ 50000.
📸 `docs/img/01-api-call.png`

```bash
python3 tools/sqale_audit.py
cat SQALE_AUDIT.md
```
Скрипт рахує людино-години/дні, TDD і порівнює рейтинг із хмарним.

## 2. Завдання 2 — фінансовий симулятор
```bash
python3 -m unittest discover -s tests -v
HOURLY_RATE=40 OVERLOAD_COEFF=1.3 DISCOUNT_RATE=0.01 python3 tools/financial_ledger.py
cat FINANCIAL_LEDGER.md
```
Очікувано: таблиця з 6 місяців, `Payback Period: N-й місяць`, `QUALITY GATE: PASS`,
`✅ Фінансовий леджер успішно створено`.
📸 `docs/img/02-financial-run.png`

Для Live Demo можна показати, що ставка не впливає на місяць окупності:
```bash
HOURLY_RATE=50 python3 tools/financial_ledger.py | tail -3
```

## 3. Завдання 3 — FPA / UCP
- Відкрий `fpa-ucp/FPA_UCP_Calculator.xlsx` у Google Таблицях (**Файл → Імпортувати → Завантажити**) або в Numbers/Excel.
  Аркуші: **FPA (IFPUG)** → 76 FP, **UCP (Karner)** → 90 UCP, **Calibration** → PF ≈ 4,17, **Sources** — сигнатури коду.
  Сині комірки — вхідні дані; зміни будь-яку, і підсумки перерахуються.
- Діаграма: `docs/usecase-users.png`; редагування — відкрий `docs/usecase-users.drawio` на https://app.diagrams.net.
- (Необов'язково, для демонстрації методу) перерахунок трудовитрат з Git:
  ```bash
  git clone --filter=blob:none https://github.com/apache/fineract.git fineract
  P=fineract-provider/src/main/java/org/apache/fineract/useradministration
  C=fineract-core/src/main/java/org/apache/fineract/useradministration
  python3 tools/git_effort.py fineract $P/api/UsersApiResource.java \
    $P/service/AppUserWritePlatformServiceJpaRepositoryImpl.java $P/service/AppUserReadPlatformServiceImpl.java \
    $C/domain/AppUser.java $P/domain/AppUserPreviousPassword.java
  ```
  (папка `fineract/` у `.gitignore`; числа можуть трохи зрости, якщо у Fineract з'явилися нові коміти).

## 4. Звіт
1. Obsidian → **Open folder as vault** → вибери **корінь** `lab9-software-economics` (не `docs`).
2. Відкрий `docs/LAB9_REPORT.md`, режим читання **Cmd + E**: розділи 1.3 і 2.3 автоматично покажуть
   `SQALE_AUDIT.md` і `FINANCIAL_LEDGER.md`.
3. Заповни поля `⟨…⟩`: вміст `report.json` (§1.2) і лог ШІ. Якщо числа в `report.json` відрізняються від звіту
   (SonarQube Cloud міг переаналізувати проєкт), онови таблиці §1.3 і §2.3 за `SQALE_AUDIT.md` / `FINANCIAL_LEDGER.md`.

## 5. Коміт і GitHub
```bash
git add report.json data/ SQALE_AUDIT.md FINANCIAL_LEDGER.md docs/
git commit -m "audit(sqale): SonarQube Cloud snapshot of apache_fineract, generated SQALE and financial ledgers"
```
Створи на https://github.com/new репозиторій `lab9-software-economics` (без README), потім:
```bash
git remote add origin https://github.com/YehorIshchuk/lab9-software-economics.git
git push -u origin main
```
(логін `YehorIshchuk`, пароль — токен `ghp_…`; macOS міг запам'ятати його з минулого разу).

## Шпаргалка до захисту
- **Cost of Delay** — скільки бізнес втрачає щомісяця, поки борг не виправлено (тут: 1 інженерна година на 100 рядків
  на боротьбу з регресіями). Це «відсотки» за технічним боргом; рефакторинг їх припиняє, тому після нього CoD стає
  щомісячним прибутком, а NPV показує, коли цей прибуток перекриє вартість рефакторингу (тіло боргу).
- **FPA vs UCP**: FPA (IFPUG) міряє функціональність через **дані та транзакції** (ILF/EIF/EI/EO/EQ) — незалежно від
  мови та дизайну; UCP (Карнер) міряє через **акторів і прецеденти** (UAW + UUCW) з поправками TCF/ECF — ближче до
  вимог і ООП-аналізу. Обидва дають розмір у «точках», але різних одиницях: 76 FP ≠ 90 UCP.
- **PF** = людино-години / UCP: скільки годин команда в середньому витрачає на одну точку прецедентів;
  множиш на розмір нового Change Request → прогноз трудовитрат і бюджету до написання коду.
