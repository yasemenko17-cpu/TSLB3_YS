"""Відкриті тести задачі 4: Досяжність і глухі кути навігації.

Запуск: pytest tests/test_lab_04.py
Тут лише приклади з карток варіантів; повний набір перевірок є у викладача.
"""
import copy
import signal

import pytest
from conftest import load


def _same(a, b):
    """Рівність; список і кортеж вважаються однаковими послідовностями."""
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-9
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def run(task, fn, args, expected):
    """Викликає функцію задачі на копії аргументів і порівнює результат; вхідні дані змінювати не можна."""
    func = getattr(load(task), fn)
    given = copy.deepcopy(args)
    if isinstance(expected, ValueError):
        with pytest.raises(ValueError) as info:
            func(*given)
        assert str(info.value) == str(expected)
    else:
        got = func(*given)
        assert _same(got, expected), f"отримано {got!r}, очікувалось {expected!r}"
    assert given == args, "функція не повинна змінювати вхідні дані"


def _ids(cases, prefix):
    return [f"{prefix}-{c[0]}-{i}" for i, c in enumerate(cases)]


@pytest.fixture(autouse=True)
def _watchdog():
    """Тест, що завис (нескінченний цикл), завершується за 10 с."""
    def boom(signum, frame):
        raise TimeoutError("тест завис довше 10 с: перевірте умови завершення циклів")
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)




T04 = [('S1',
  'navigation_audit',
  ({'Головна': ['Каталог', 'Видача'],
    'Каталог': ['Картка', 'Головна'],
    'Картка': ['Видача', 'Нема'],
    'Видача': ['Підтвердження'],
    'Підтвердження': [],
    'Журнал': ['Головна'],
    'Довідка': []},
   'Головна',
   ['Підтвердження']),
  {'reachable': ['Головна', 'Каталог', 'Картка', 'Видача', 'Підтвердження'],
   'unreachable': ['Журнал', 'Довідка'],
   'depth': {'Головна': 0, 'Каталог': 1, 'Картка': 2, 'Видача': 1, 'Підтвердження': 2},
   'max_depth': 2,
   'broken': [('Картка', 'Нема')],
   'dead_ends': [],
   'no_exit': []}),
 ('S2',
  'navigation_audit',
  ({'Вхід': ['Розклад'],
    'Розклад': ['Слот', 'Помилка'],
    'Слот': ['Форма'],
    'Форма': ['Готово', 'Слот'],
    'Готово': [],
    'Помилка': ['Помилка', 'Повтор'],
    'Повтор': ['Помилка']},
   'Вхід',
   ['Готово']),
  {'reachable': ['Вхід', 'Розклад', 'Слот', 'Форма', 'Готово', 'Помилка', 'Повтор'],
   'unreachable': [],
   'depth': {'Вхід': 0, 'Розклад': 1, 'Слот': 2, 'Форма': 3, 'Готово': 4, 'Помилка': 2, 'Повтор': 3},
   'max_depth': 4,
   'broken': [],
   'dead_ends': [],
   'no_exit': ['Помилка', 'Повтор']}),
 ('S3',
  'navigation_audit',
  ({'Старт': ['Список', 'Довідка'],
    'Список': ['Книга'],
    'Книга': ['Список'],
    'Довідка': [],
    'Окремо': ['Старт']},
   'Старт',
   ['Книга']),
  {'reachable': ['Старт', 'Список', 'Книга', 'Довідка'],
   'unreachable': ['Окремо'],
   'depth': {'Старт': 0, 'Список': 1, 'Книга': 2, 'Довідка': 1},
   'max_depth': 2,
   'broken': [],
   'dead_ends': ['Довідка'],
   'no_exit': []})]


@pytest.mark.parametrize("case", T04, ids=_ids(T04, "T04"))
def test_task_04(case):
    _, fn, args, expected = case
    run(4, fn, args, expected)
