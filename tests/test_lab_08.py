"""Відкриті тести задачі 8: Метрики успіху й OKR.

Запуск: pytest tests/test_lab_08.py
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




T08 = [('S1',
  'okr_status',
  ({'objective': 'Швидка видача приладів',
    'key_results': [{'id': 'KR1',
                     'text': 'Скоротити час видачі групі з 15 до 5 хв',
                     'metric': 'issue_min',
                     'baseline': 15,
                     'target': 5},
                    {'id': 'KR2',
                     'text': 'Зменшити невернуті прилади з 14 до 3',
                     'metric': 'unreturned',
                     'baseline': 14,
                     'target': 3},
                    {'id': 'KR3',
                     'text': 'Консультувати лаборантів щодо журналу',
                     'metric': 'coach',
                     'baseline': 0,
                     'target': 10}],
    'initiatives': {'KR1': ['US-02', 'US-03'], 'KR2': ['US-04']}},
   {'issue_min': 10, 'unreturned': 14},
   ['US-01', 'US-02', 'US-03', 'US-04']),
  {'progress': {'KR1': 50, 'KR2': 0, 'KR3': None},
   'score': 25,
   'level': 'червоний',
   'unmeasured': ['KR3'],
   'activity_kr': ['KR3'],
   'unlinked_kr': ['KR3'],
   'orphan_stories': ['US-01'],
   'unknown_stories': []}),
 ('S2',
  'okr_status',
  ({'key_results': [{'id': 'KR1',
                     'text': 'Збільшити частку записів через сервіс з 20 до 60 відсотків',
                     'metric': 'booked_pct',
                     'baseline': 20,
                     'target': 60},
                    {'id': 'KR2',
                     'text': 'Зменшити неявки з 30 до 10 відсотків',
                     'metric': 'noshow_pct',
                     'baseline': 30,
                     'target': 10},
                    {'id': 'KR3',
                     'text': 'Залучити трьох викладачів до пілоту',
                     'metric': 'pilots',
                     'baseline': 0,
                     'target': 3}],
    'initiatives': {'KR1': ['Z-01', 'Z-02'], 'KR2': ['Z-02', 'Z-09'], 'KR3': ['Z-03']}},
   {'booked_pct': 75, 'noshow_pct': 40, 'pilots': 1},
   ['Z-01', 'Z-02', 'Z-03', 'Z-04']),
  {'progress': {'KR1': 100, 'KR2': 0, 'KR3': 33},
   'score': 44,
   'level': 'жовтий',
   'unmeasured': [],
   'activity_kr': [],
   'unlinked_kr': [],
   'orphan_stories': ['Z-04'],
   'unknown_stories': ['Z-09']}),
 ('S3',
  'okr_status',
  ({'key_results': [{'id': 'KR1',
                     'text': 'Довести частку резервацій онлайн до 70 відсотків',
                     'metric': 'online_pct',
                     'baseline': 20,
                     'target': 70},
                    {'id': 'KR2',
                     'text': 'Проаналізувати 50 запитів читачів',
                     'metric': 'requests',
                     'baseline': 0,
                     'target': 50}],
    'initiatives': {'KR1': ['B-01'], 'KR2': []}},
   {},
   ['B-01']),
  {'progress': {'KR1': None, 'KR2': None},
   'score': None,
   'level': 'немає даних',
   'unmeasured': ['KR1', 'KR2'],
   'activity_kr': ['KR2'],
   'unlinked_kr': ['KR2'],
   'orphan_stories': [],
   'unknown_stories': []})]


@pytest.mark.parametrize("case", T08, ids=_ids(T08, "T08"))
def test_task_08(case):
    _, fn, args, expected = case
    run(8, fn, args, expected)
