"""Відкриті тести задачі 3: Сценарії на графі екранів.

Запуск: pytest tests/test_lab_03.py
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




T03 = [('S1',
  'scenario_paths',
  ({'Головна': ['Каталог', 'Видача'],
    'Каталог': ['Картка', 'Головна'],
    'Картка': ['Видача', 'Каталог'],
    'Видача': ['Підтвердження', 'Головна'],
    'Підтвердження': ['Головна'],
    'Журнал': ['Головна']},
   [{'id': 'find', 'start': 'Головна', 'goal': 'Картка', 'max_steps': 3, 'via': []},
    {'id': 'issue', 'start': 'Головна', 'goal': 'Підтвердження', 'max_steps': 3, 'via': ['Каталог']},
    {'id': 'log', 'start': 'Головна', 'goal': 'Журнал', 'max_steps': 2},
    {'id': 'x', 'start': 'Головна', 'goal': 'Звіт', 'max_steps': 2}]),
  {'scenarios': [{'id': 'find', 'steps': 2, 'path': ['Головна', 'Каталог', 'Картка'], 'status': 'ok'},
                 {'id': 'issue',
                  'steps': 4,
                  'path': ['Головна', 'Каталог', 'Картка', 'Видача', 'Підтвердження'],
                  'status': 'довгий'},
                 {'id': 'log', 'steps': None, 'path': [], 'status': 'недосяжний'},
                 {'id': 'x', 'steps': None, 'path': [], 'status': 'невідомий екран'}],
   'coverage': 25,
   'unused_screens': ['Журнал']}),
 ('S2',
  'scenario_paths',
  ({'Вхід': ['Розклад'],
    'Розклад': ['Слот', 'Вхід'],
    'Слот': ['Форма'],
    'Форма': ['Готово', 'Слот'],
    'Готово': [],
    'Профіль': ['Вхід']},
   [{'id': 'book', 'start': 'Вхід', 'goal': 'Готово', 'max_steps': 4, 'via': ['Слот']},
    {'id': 'stay', 'start': 'Розклад', 'goal': 'Розклад', 'max_steps': 0},
    {'id': 'profile', 'start': 'Вхід', 'goal': 'Профіль', 'max_steps': 2}]),
  {'scenarios': [{'id': 'book',
                  'steps': 4,
                  'path': ['Вхід', 'Розклад', 'Слот', 'Форма', 'Готово'],
                  'status': 'ok'},
                 {'id': 'stay', 'steps': 0, 'path': ['Розклад'], 'status': 'ok'},
                 {'id': 'profile', 'steps': None, 'path': [], 'status': 'недосяжний'}],
   'coverage': 66,
   'unused_screens': ['Профіль']}),
 ('S3',
  'scenario_paths',
  ({'Старт': ['Пошук', 'Нове', 'Зникле'],
    'Пошук': ['Картка'],
    'Нове': ['Картка'],
    'Картка': ['Резерв', 'Старт'],
    'Резерв': []},
   [{'id': 'reserve', 'start': 'Старт', 'goal': 'Резерв', 'max_steps': 3}]),
  {'scenarios': [{'id': 'reserve',
                  'steps': 3,
                  'path': ['Старт', 'Пошук', 'Картка', 'Резерв'],
                  'status': 'ok'}],
   'coverage': 100,
   'unused_screens': ['Нове']})]


@pytest.mark.parametrize("case", T03, ids=_ids(T03, "T03"))
def test_task_03(case):
    _, fn, args, expected = case
    run(3, fn, args, expected)
