"""Відкриті тести задачі 6: План MVP за ітераціями.

Запуск: pytest tests/test_lab_06.py
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




T06 = [('S1',
  'plan_iterations',
  ([{'id': 'A', 'size': 3, 'depends_on': []},
    {'id': 'B', 'size': 2, 'depends_on': ['A']},
    {'id': 'C', 'size': 2, 'depends_on': []},
    {'id': 'D', 'size': 4, 'depends_on': ['B']},
    {'id': 'E', 'size': 1, 'depends_on': []}],
   5,
   '2026-11-02',
   14,
   '2026-12-20'),
  {'iterations': [{'n': 1, 'start': '2026-11-02', 'end': '2026-11-15', 'items': ['A', 'C'], 'load': 5},
                  {'n': 2, 'start': '2026-11-16', 'end': '2026-11-29', 'items': ['B', 'E'], 'load': 3},
                  {'n': 3, 'start': '2026-11-30', 'end': '2026-12-13', 'items': ['D'], 'load': 4}],
   'finish': '2026-12-13',
   'on_time': True,
   'late_days': 0,
   'utilization': 80}),
 ('S2',
  'plan_iterations',
  ([{'id': 'P', 'size': 4, 'depends_on': []},
    {'id': 'Q', 'size': 4, 'depends_on': ['P']},
    {'id': 'R', 'size': 4, 'depends_on': ['Q']}],
   5,
   '2026-10-26',
   7,
   '2026-11-08'),
  {'iterations': [{'n': 1, 'start': '2026-10-26', 'end': '2026-11-01', 'items': ['P'], 'load': 4},
                  {'n': 2, 'start': '2026-11-02', 'end': '2026-11-08', 'items': ['Q'], 'load': 4},
                  {'n': 3, 'start': '2026-11-09', 'end': '2026-11-15', 'items': ['R'], 'load': 4}],
   'finish': '2026-11-15',
   'on_time': False,
   'late_days': 7,
   'utilization': 80}),
 ('S3',
  'plan_iterations',
  ([{'id': 'M', 'size': 3, 'depends_on': []},
    {'id': 'N', 'size': 3, 'depends_on': []},
    {'id': 'O', 'size': 2, 'depends_on': []}],
   5,
   '2027-01-11',
   14,
   '2027-02-07'),
  {'iterations': [{'n': 1, 'start': '2027-01-11', 'end': '2027-01-24', 'items': ['M', 'O'], 'load': 5},
                  {'n': 2, 'start': '2027-01-25', 'end': '2027-02-07', 'items': ['N'], 'load': 3}],
   'finish': '2027-02-07',
   'on_time': True,
   'late_days': 0,
   'utilization': 80})]


@pytest.mark.parametrize("case", T06, ids=_ids(T06, "T06"))
def test_task_06(case):
    _, fn, args, expected = case
    run(6, fn, args, expected)
