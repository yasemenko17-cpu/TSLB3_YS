"""Відкриті тести задачі 10: Зведений підсумок концепту.

Запуск: pytest tests/test_lab_10.py
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




T10 = [('S1',
  'concept_summary',
  ({'concept': {'score': 100},
    'mvp': {'size': 10, 'capacity': 10, 'uncovered_steps': []},
    'scenarios': {'coverage': 100},
    'navigation': {'unreachable': [], 'dead_ends': [], 'broken': [], 'no_exit': []},
    'a11y': {'issues': []},
    'plan': {'on_time': True, 'late_days': 0},
    'risks': {'top_score': 20, 'top_planned': True},
    'metrics': {'unlinked_kr': [], 'orphan_stories': [], 'activity_kr': []},
    'readiness': {'verdict': 'готово'}},),
  {'areas': {'concept': 'зелений',
             'mvp': 'зелений',
             'scenarios': 'зелений',
             'navigation': 'зелений',
             'a11y': 'зелений',
             'plan': 'зелений',
             'risks': 'зелений',
             'metrics': 'зелений',
             'readiness': 'зелений'},
   'decision': 'показ',
   'next_steps': []}),
 ('S2',
  'concept_summary',
  ({'concept': {'score': 80},
    'mvp': {'size': 7, 'capacity': 8, 'uncovered_steps': ['Оцінити']},
    'scenarios': {'coverage': 66},
    'navigation': {'unreachable': [], 'dead_ends': ['X'], 'broken': [], 'no_exit': []},
    'a11y': {'issues': [1, 2, 3, 4, 5]},
    'plan': {'on_time': False, 'late_days': 10},
    'risks': {'top_score': 12, 'top_planned': False},
    'metrics': {'unlinked_kr': [], 'orphan_stories': ['Z-04'], 'activity_kr': []},
    'readiness': {'verdict': 'не готово'}},),
  {'areas': {'concept': 'жовтий',
             'mvp': 'жовтий',
             'scenarios': 'червоний',
             'navigation': 'жовтий',
             'a11y': 'червоний',
             'plan': 'жовтий',
             'risks': 'жовтий',
             'metrics': 'жовтий',
             'readiness': 'червоний'},
   'decision': 'відкласти',
   'next_steps': ['Доведіть до кінця шляхи сценаріїв по екранах прототипу',
                  'Виправте зауваження доступності HTML-прототипу',
                  'Закрийте пункти чекліста готовності до показу']}),
 ('S3',
  'concept_summary',
  ({'concept': {'score': 100},
    'mvp': {'size': 5, 'capacity': 10, 'uncovered_steps': []},
    'scenarios': {'coverage': 100},
    'navigation': {'unreachable': [], 'dead_ends': [], 'broken': [], 'no_exit': []},
    'a11y': {'issues': []},
    'plan': {'on_time': False, 'late_days': 14},
    'risks': {'top_score': 15, 'top_planned': False},
    'metrics': {'unlinked_kr': [], 'orphan_stories': [], 'activity_kr': ['KR2']},
    'readiness': {'verdict': 'готово з зауваженнями'}},),
  {'areas': {'concept': 'зелений',
             'mvp': 'жовтий',
             'scenarios': 'зелений',
             'navigation': 'зелений',
             'a11y': 'зелений',
             'plan': 'жовтий',
             'risks': 'червоний',
             'metrics': 'жовтий',
             'readiness': 'жовтий'},
   'decision': 'доопрацювати',
   'next_steps': ['Заплануйте перевірку найризикованішого припущення',
                  'Додайте в MVP історію для кожного кроку карти або зменште обсяг',
                  'Скоротіть обсяг або перенесіть дату показу']})]


@pytest.mark.parametrize("case", T10, ids=_ids(T10, "T10"))
def test_task_10(case):
    _, fn, args, expected = case
    run(10, fn, args, expected)
