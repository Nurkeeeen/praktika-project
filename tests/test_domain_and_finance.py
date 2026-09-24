import sys
from pathlib import Path

import pytest

from app.domain import can_transition, match_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "finance"))
import tco_model  # noqa: E402


@pytest.mark.parametrize("cur,new,ok", [
    ("submitted", "forwarded", True),
    ("submitted", "accepted", False),
    ("interview", "accepted", True),
    ("accepted", "withdrawn", False),
    ("rejected", "forwarded", False),
])
def test_transitions(cur, new, ok):
    assert can_transition(cur, new) is ok


def test_match_score():
    assert match_score("Python;SQL", "python;sql;git") == pytest.approx(2 / 3)
    assert match_score("Python", "") == 0.0


def test_finance_model_recommended_option_positive():
    opts = {o.name[:4]: o for o in tco_model.options()}
    v3s = opts["В3-С"]
    assert v3s.npv > 0
    assert v3s.payback_years is not None
    # Своя разработка по рыночным ставкам не окупается за 3 года — ключевой вывод бизнес-кейса
    assert opts["В3. "].npv < 0 and opts["В2. "].npv < 0
