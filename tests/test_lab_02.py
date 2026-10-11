"""Відкриті тести задачі 2: Зріз MVP з карти історій.

Запуск: pytest tests/test_lab_02.py
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




T02 = [('S1',
  'mvp_slice',
  ({'steps': ['Внести', 'Знайти', 'Видати', 'Прийняти'],
    'stories': [{'id': 'U1', 'step': 'Внести', 'size': 2, 'value': 8, 'depends_on': []},
                {'id': 'U2', 'step': 'Внести', 'size': 3, 'value': 5, 'depends_on': ['U1']},
                {'id': 'U3', 'step': 'Знайти', 'size': 2, 'value': 8, 'depends_on': ['U1']},
                {'id': 'U4', 'step': 'Знайти', 'size': 3, 'value': 4, 'depends_on': ['U3']},
                {'id': 'U5', 'step': 'Видати', 'size': 3, 'value': 9, 'depends_on': ['U3']},
                {'id': 'U6', 'step': 'Прийняти', 'size': 2, 'value': 7, 'depends_on': ['U5']},
                {'id': 'U7', 'step': 'Прийняти', 'size': 1, 'value': 3, 'depends_on': ['U6']}]},
   10),
  {'selected': ['U1', 'U3', 'U5', 'U6', 'U7'],
   'size': 10,
   'left': 0,
   'uncovered_steps': [],
   'postponed': ['U2', 'U4'],
   'by_step': {'Внести': ['U1'], 'Знайти': ['U3'], 'Видати': ['U5'], 'Прийняти': ['U6', 'U7']}}),
 ('S2',
  'mvp_slice',
  ({'steps': ['Обрати викладача', 'Записатися', 'Отримати нагадування', 'Оцінити'],
    'stories': [{'id': 'Z1', 'step': 'Обрати викладача', 'size': 2, 'value': 6, 'depends_on': []},
                {'id': 'Z2', 'step': 'Записатися', 'size': 3, 'value': 9, 'depends_on': ['Z1']},
                {'id': 'Z3', 'step': 'Записатися', 'size': 2, 'value': 4, 'depends_on': []},
                {'id': 'Z4', 'step': 'Отримати нагадування', 'size': 2, 'value': 5, 'depends_on': ['Z2']},
                {'id': 'Z5', 'step': 'Обрати викладача', 'size': 1, 'value': 6, 'depends_on': []}]},
   8),
  {'selected': ['Z1', 'Z2', 'Z4', 'Z5'],
   'size': 8,
   'left': 0,
   'uncovered_steps': ['Оцінити'],
   'postponed': ['Z3'],
   'by_step': {'Обрати викладача': ['Z1', 'Z5'],
               'Записатися': ['Z2'],
               'Отримати нагадування': ['Z4'],
               'Оцінити': []}}),
 ('S3',
  'mvp_slice',
  ({'steps': ['Знайти', 'Резервувати', 'Забрати'],
    'stories': [{'id': 'B1', 'step': 'Знайти', 'size': 2, 'value': 6, 'depends_on': []},
                {'id': 'B2', 'step': 'Знайти', 'size': 2, 'value': 4, 'depends_on': ['B1']},
                {'id': 'B3', 'step': 'Резервувати', 'size': 3, 'value': 9, 'depends_on': ['B1']},
                {'id': 'B4', 'step': 'Резервувати', 'size': 1, 'value': 2, 'depends_on': []},
                {'id': 'B5', 'step': 'Забрати', 'size': 2, 'value': 6, 'depends_on': ['B3']},
                {'id': 'B6', 'step': 'Забрати', 'size': 2, 'value': 4, 'depends_on': []}]},
   9),
  {'selected': ['B1', 'B2', 'B3', 'B5'],
   'size': 9,
   'left': 0,
   'uncovered_steps': [],
   'postponed': ['B4', 'B6'],
   'by_step': {'Знайти': ['B1', 'B2'], 'Резервувати': ['B3'], 'Забрати': ['B5']}})]


@pytest.mark.parametrize("case", T02, ids=_ids(T02, "T02"))
def test_task_02(case):
    _, fn, args, expected = case
    run(2, fn, args, expected)
