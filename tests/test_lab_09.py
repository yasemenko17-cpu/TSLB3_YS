"""Відкриті тести задачі 9: Чекліст готовності до показу.

Запуск: pytest tests/test_lab_09.py
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




T09 = [('S1',
  'readiness',
  ({'consistency': 100,
    'scenarios_total': 4,
    'scenarios_ok': 4,
    'unreachable': 0,
    'dead_ends': 0,
    'a11y_issues': 0,
    'on_time': True,
    'top_tested': True,
    'kr_count': 3,
    'unlinked_kr': 0,
    'sessions': [{'user': 'u1', 'done': True}, {'user': 'u2', 'done': True}, {'user': 'u3', 'done': True}],
    'findings': [{'severity': 2, 'status': 'відкрито'}, {'severity': 4, 'status': 'виправлено'}],
    'demo_minutes': 5},),
  {'checks': [('K1', True),
              ('K2', True),
              ('K3', True),
              ('K4', True),
              ('K5', True),
              ('K6', True),
              ('K7', True),
              ('K8', True),
              ('K9', True),
              ('K10', True)],
   'failed': [],
   'verdict': 'готово'}),
 ('S2',
  'readiness',
  ({'consistency': 100,
    'scenarios_total': 4,
    'scenarios_ok': 4,
    'unreachable': 0,
    'dead_ends': 0,
    'a11y_issues': 2,
    'on_time': True,
    'top_tested': False,
    'kr_count': 3,
    'unlinked_kr': 0,
    'sessions': [{'user': 'u1', 'done': True},
                 {'user': 'u1', 'done': True},
                 {'user': 'u2', 'done': True},
                 {'user': 'u3', 'done': True},
                 {'user': 'u4', 'done': False}],
    'findings': [{'severity': 2, 'status': 'відкрито'}, {'severity': 4, 'status': 'виправлено'}],
    'demo_minutes': 9},),
  {'checks': [('K1', True),
              ('K2', True),
              ('K3', True),
              ('K4', False),
              ('K5', True),
              ('K6', False),
              ('K7', True),
              ('K8', True),
              ('K9', True),
              ('K10', False)],
   'failed': ['K4', 'K6', 'K10'],
   'verdict': 'готово з зауваженнями'}),
 ('S3',
  'readiness',
  ({'consistency': 100,
    'scenarios_total': 2,
    'scenarios_ok': 2,
    'unreachable': 0,
    'dead_ends': 1,
    'a11y_issues': 0,
    'on_time': True,
    'top_tested': True,
    'kr_count': 6,
    'unlinked_kr': 0,
    'sessions': [{'user': 'u1', 'done': True}, {'user': 'u2', 'done': True}, {'user': 'u3', 'done': False}],
    'findings': [{'severity': 3, 'status': 'відкрито'}],
    'demo_minutes': 4},),
  {'checks': [('K1', True),
              ('K2', False),
              ('K3', False),
              ('K4', True),
              ('K5', True),
              ('K6', True),
              ('K7', False),
              ('K8', False),
              ('K9', False),
              ('K10', True)],
   'failed': ['K2', 'K3', 'K7', 'K8', 'K9'],
   'verdict': 'не готово'})]


@pytest.mark.parametrize("case", T09, ids=_ids(T09, "T09"))
def test_task_09(case):
    _, fn, args, expected = case
    run(9, fn, args, expected)
