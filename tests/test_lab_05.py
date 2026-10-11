"""Відкриті тести задачі 5: Доступність HTML-прототипу.

Запуск: pytest tests/test_lab_05.py
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




T05 = [('S1',
  'audit_html',
  ('<html lang="uk"><head><title>Облік</title></head><body>\n'
   '<h1>Облік приладів</h1>\n'
   '<h3>Пошук</h3>\n'
   '<img src="a.png">\n'
   '<label for="q">Назва</label><input id="q">\n'
   '<input name="n">\n'
   '<button></button>\n'
   '<a href="/x">тут</a>\n'
   '</body></html>',),
  {'issues': [('heading-skip', 'h31'),
              ('img-alt', 'img1'),
              ('no-label', 'input2'),
              ('button-name', 'button1'),
              ('vague-link', 'a1')],
   'by_rule': {'heading-skip': 1, 'img-alt': 1, 'no-label': 1, 'button-name': 1, 'vague-link': 1},
   'ok': False}),
 ('S2',
  'audit_html',
  ('<body><h2>Запис</h2><h2>Слоти</h2><select aria-label="Викладач"><option>1</option></select><label>Тема '
   '<textarea></textarea></label><a href="#a" aria-label=""><span></span></a><div id="a"></div><div '
   'id="a"></div></body>',),
  {'issues': [('html-lang', 'document'),
              ('no-title', 'document'),
              ('no-h1', 'document'),
              ('link-name', 'a1'),
              ('duplicate-id', 'a')],
   'by_rule': {'html-lang': 1, 'no-title': 1, 'no-h1': 1, 'link-name': 1, 'duplicate-id': 1},
   'ok': False}),
 ('S3',
  'audit_html',
  ('<!doctype html><html '
   'lang="uk"><head><title>Бібліотека</title></head><body><h1>Резерв</h1><h2>Книга</h2><img src="c.png" '
   'alt=""><label for="isbn">ISBN</label><input id="isbn" type="text"><input type="hidden" name="t"><input '
   'type="submit" value="Знайти"><a href="/b">Мої '
   'резервації</a><button>Зарезервувати</button></body></html>',),
  {'issues': [], 'by_rule': {}, 'ok': True})]


@pytest.mark.parametrize("case", T05, ids=_ids(T05, "T05"))
def test_task_05(case):
    _, fn, args, expected = case
    run(5, fn, args, expected)
