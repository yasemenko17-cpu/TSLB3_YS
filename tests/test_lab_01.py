"""Відкриті тести задачі 1: Узгодженість концепту.

Запуск: pytest tests/test_lab_01.py
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




T01 = [('S1',
  'check_concept',
  ({'segments': {'S1': 'лаборант', 'S2': 'студент'},
    'problems': {'P1': {'segments': ['S1']}, 'P2': {'segments': ['S1', 'S2']}},
    'propositions': {'V1': {'solves': ['P1']}, 'V2': {'solves': ['P2']}},
    'scenarios': {'K1': {'proposition': 'V1', 'segment': 'S1'},
                  'K2': {'proposition': 'V2', 'segment': 'S2'}}},),
  {'broken': [],
   'problems_without_segment': [],
   'unsolved_problems': [],
   'idle_propositions': [],
   'segments_without_problem': [],
   'propositions_without_scenario': [],
   'mismatched_scenarios': [],
   'chains': ['P1', 'P2'],
   'score': 100}),
 ('S2',
  'check_concept',
  ({'segments': {'S1': 'студент', 'S2': 'викладач', 'S3': 'бухгалтер'},
    'problems': {'P1': {'segments': ['S1']}, 'P2': {'segments': ['S2', 'S9']}, 'P3': {'segments': []}},
    'propositions': {'V1': {'solves': ['P1', 'P7']}, 'V2': {'solves': ['P7']}, 'V3': {'solves': ['P2']}},
    'scenarios': {'K1': {'proposition': 'V1', 'segment': 'S1'},
                  'K2': {'proposition': 'V3', 'segment': 'S1'},
                  'K3': {'proposition': 'V8', 'segment': 'S2'}}},),
  {'broken': [('проблема→сегмент', 'P2', 'S9'),
              ('пропозиція→проблема', 'V1', 'P7'),
              ('пропозиція→проблема', 'V2', 'P7'),
              ('сценарій→пропозиція', 'K3', 'V8')],
   'problems_without_segment': ['P3'],
   'unsolved_problems': ['P3'],
   'idle_propositions': ['V2'],
   'segments_without_problem': ['S3'],
   'propositions_without_scenario': ['V2'],
   'mismatched_scenarios': ['K2'],
   'chains': ['P1'],
   'score': 33}),
 ('S3',
  'check_concept',
  ({'segments': {'S1': 'читач', 'S2': 'бібліотекар'},
    'problems': {'P1': {'segments': ['S1']}, 'P2': {'segments': ['S1', 'S2']}},
    'propositions': {'V1': {'solves': ['P1', 'P2']}, 'V2': {'solves': []}},
    'scenarios': {'K1': {'proposition': 'V1', 'segment': 'S2'}}},),
  {'broken': [],
   'problems_without_segment': [],
   'unsolved_problems': [],
   'idle_propositions': ['V2'],
   'segments_without_problem': [],
   'propositions_without_scenario': ['V2'],
   'mismatched_scenarios': [],
   'chains': ['P2'],
   'score': 50})]


@pytest.mark.parametrize("case", T01, ids=_ids(T01, "T01"))
def test_task_01(case):
    _, fn, args, expected = case
    run(1, fn, args, expected)
