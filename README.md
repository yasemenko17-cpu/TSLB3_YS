# Стартовий проєкт TSPP-LAB04 (лабораторна робота 3)

1. Відкрийте проєкт у GitHub Codespaces (Code → Codespaces → Create codespace) або локально: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`. Права адміністратора не потрібні.
2. Визначте свою задачу й набір за номером варіанта: задача = `(номер - 1) // 3 + 1`, набір = `(номер - 1) % 3 + 1`. Реалізуйте функцію у файлі `variants/lab_NN.py` за карткою варіанта.
3. Запускайте відкриті тести своєї задачі й свого набору: `pytest tests/test_lab_NN.py -k S2` (замініть `S2` на свій набір: `S1`, `S2` або `S3`).
4. Змінюйте лише свій файл у `variants/` (і за бажанням додавайте `tests/test_my.py`).
5. Частина Б: заповніть файли теки `artifacts/` для продукту власного диплома (`concept.json`, `board.json`, `board_export.json`, `tests.json`, `demo.md`, `prototype/`) і перевірте їх командою `pytest artifacts_check`. Для HTML-прототипу створіть `artifacts/prototype/index.html` і видаліть шаблонний `artifacts/prototype/screens.json`.
6. Експорт дошки: `gh project item-list <номер> --owner "@me" --format json --limit 100 > artifacts/board_export.json` (потрібен `gh auth login`; у Codespaces `gh` уже встановлено).
