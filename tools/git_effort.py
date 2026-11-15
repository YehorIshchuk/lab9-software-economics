#!/usr/bin/env python3
"""
Ретроспективна оцінка трудовитрат (людино-годин) підмодуля з історії Git.

Методика (евристика git-hours):
  * беремо всі коміти, що змінювали файли підмодуля;
  * для кожного автора сортуємо коміти за часом;
  * якщо між сусідніми комітами автора < MAX_GAP хвилин, вважаємо, що він працював
    весь цей проміжок (одна робоча сесія);
  * якщо перерва більша, починається нова сесія, і до неї додаємо FIRST_COMMIT
    хвилин (робота перед першим комітом сесії).

Використання:
    python3 tools/git_effort.py <шлях до репозиторію> <файл1> [<файл2> ...]
"""
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

MAX_GAP_MIN = 120       # максимальна перерва всередині однієї сесії, хв
FIRST_COMMIT_MIN = 120  # час "до першого коміту" нової сесії, хв


def commits(repo, paths):
    """Унікальні коміти по всіх файлах; --follow враховує перейменування/переміщення файлів."""
    seen = {}
    for path in paths:
        out = subprocess.run(
            ["git", "-C", repo, "log", "--follow", "--no-merges", "--format=%H|%an|%at", "--", path],
            capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            sha, author, ts = line.split("|")
            seen[sha] = (author, int(ts))
    for sha, (author, ts) in seen.items():
        yield sha, author, ts


def effort(repo, paths):
    by_author = defaultdict(list)
    for sha, author, ts in commits(repo, paths):
        by_author[author].append(ts)
    rows = []
    for author, stamps in by_author.items():
        stamps.sort()
        minutes = FIRST_COMMIT_MIN
        sessions = 1
        for prev, cur in zip(stamps, stamps[1:]):
            gap = (cur - prev) / 60
            if gap < MAX_GAP_MIN:
                minutes += gap
            else:
                minutes += FIRST_COMMIT_MIN
                sessions += 1
        rows.append((author, len(stamps), sessions, minutes / 60,
                     datetime.fromtimestamp(stamps[0]).date(), datetime.fromtimestamp(stamps[-1]).date()))
    rows.sort(key=lambda r: -r[3])
    return rows


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    repo, paths = sys.argv[1], sys.argv[2:]
    rows = effort(repo, paths)
    total_commits = sum(r[1] for r in rows)
    total_hours = sum(r[3] for r in rows)
    print("| Автор | Комітів | Сесій | Людино-годин | Перший коміт | Останній коміт |")
    print("|---|---|---|---|---|---|")
    for a, c, s, h, first, last in rows:
        print(f"| {a} | {c} | {s} | {h:.1f} | {first} | {last} |")
    print(f"| **Разом ({len(rows)} авторів)** | **{total_commits}** | | **{total_hours:.1f}** | | |")


if __name__ == "__main__":
    main()
