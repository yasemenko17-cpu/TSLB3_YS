"""Перевірка власних артефактів: pytest artifacts_check  (лише після виконання частини Б роботи).

Теку можна змінити змінною ARTIFACTS_DIR. Кожен тест відповідає одному правилу;
повідомлення пояснює, що виправити. Зміст (чи справді проблема важлива, чи прототип зручний) оцінює викладач на показі.
"""
import os
from pathlib import Path

import pytest
from conceptlint import RULES, load

ROOT = Path(os.environ.get("ARTIFACTS_DIR", Path(__file__).resolve().parent.parent / "artifacts"))


@pytest.fixture(scope="module")
def data():
    data, errors = load(ROOT)
    assert not errors, "\n" + "\n".join("- " + e for e in errors)
    return data


@pytest.mark.parametrize("rule", RULES, ids=[r.__name__ for r in RULES])
def test_rule(rule, data):
    problems = rule(data)
    assert not problems, "\n" + "\n".join("- " + p for p in problems)
