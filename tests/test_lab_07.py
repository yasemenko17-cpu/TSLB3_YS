"""Відкриті тести задачі 7: Ризики й найризикованіше припущення.

Запуск: pytest tests/test_lab_07.py
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




T07 = [('S1',
  'risk_profile',
  ([{'id': 'a1', 'impact': 5, 'uncertainty': 4, 'cost': 3},
    {'id': 'a2', 'impact': 4, 'uncertainty': 4, 'cost': 2},
    {'id': 'a3', 'impact': 3, 'uncertainty': 3, 'cost': 1},
    {'id': 'a4', 'impact': 2, 'uncertainty': 3, 'cost': 1},
    {'id': 'a5', 'impact': 4, 'uncertainty': 5, 'cost': 5}],
   [{'id': 'r1', 'p': 50, 'loss': 10, 'mitigation': ''},
    {'id': 'r2', 'p': 20, 'loss': 5, 'mitigation': 'буфер'},
    {'id': 'r3', 'p': 80, 'loss': 2, 'mitigation': ' '},
    {'id': 'r4', 'p': 5, 'loss': 10, 'mitigation': ''}],
   6),
  {'ranked': [('a5', 20, 'високий'),
              ('a1', 20, 'високий'),
              ('a2', 16, 'високий'),
              ('a3', 9, 'середній'),
              ('a4', 6, 'низький')],
   'top': 'a5',
   'test_now': ['a5', 'a3'],
   'risk_ranked': [('r1', 500), ('r3', 160), ('r2', 100), ('r4', 50)],
   'unmitigated': ['r1', 'r3'],
   'buffer_days': 9}),
 ('S2',
  'risk_profile',
  ([{'id': 'b1', 'impact': 4, 'uncertainty': 3, 'cost': 2},
    {'id': 'b2', 'impact': 3, 'uncertainty': 4, 'cost': 1},
    {'id': 'b3', 'impact': 2, 'uncertainty': 2, 'cost': 1}],
   [],
   0),
  {'ranked': [('b2', 12, 'середній'), ('b1', 12, 'середній'), ('b3', 4, 'низький')],
   'top': 'b2',
   'test_now': [],
   'risk_ranked': [],
   'unmitigated': [],
   'buffer_days': 0}),
 ('S3',
  'risk_profile',
  ([{'id': 'c1', 'impact': 3, 'uncertainty': 3, 'cost': 2},
    {'id': 'c2', 'impact': 3, 'uncertainty': 3, 'cost': 2},
    {'id': 'c3', 'impact': 5, 'uncertainty': 3, 'cost': 4},
    {'id': 'c4', 'impact': 2, 'uncertainty': 4, 'cost': 1}],
   [{'id': 's1', 'p': 100, 'loss': 3, 'mitigation': 'резерв'},
    {'id': 's2', 'p': 33, 'loss': 3, 'mitigation': ''}],
   6),
  {'ranked': [('c3', 15, 'високий'), ('c1', 9, 'середній'), ('c2', 9, 'середній'), ('c4', 8, 'середній')],
   'top': 'c3',
   'test_now': ['c3', 'c1'],
   'risk_ranked': [('s1', 300), ('s2', 99)],
   'unmitigated': [],
   'buffer_days': 4})]


@pytest.mark.parametrize("case", T07, ids=_ids(T07, "T07"))
def test_task_07(case):
    _, fn, args, expected = case
    run(7, fn, args, expected)
