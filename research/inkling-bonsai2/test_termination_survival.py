import pytest

from termination_survival import curve, parse_integer


def test_fixed_budget_and_observed_final():
    rows=[dict(id=0,time=2132,outcome="final")]
    rows.extend(dict(id=i,time=4096,outcome="censored") for i in range(1,30))
    estimate=curve(rows,4096)
    assert estimate["points"][-1]["at_risk"]==29
    assert estimate["points"][-1]["incomplete_probability"]==pytest.approx(29/30)
    assert estimate["restricted_mean_tokens_without_final"]==pytest.approx(120916/30)
    assert estimate["median_tokens_to_final"] is None
    assert curve(rows,8192)["restricted_mean_tokens_without_final"] is None


def test_competing_termination_and_same_time_censoring():
    rows=[dict(id=0,time=4,outcome="terminal_without_final"),
          dict(id=1,time=5,outcome="final"),dict(id=2,time=5,outcome="censored")]
    last=curve(rows,5)["points"][-1]
    assert last["at_risk"]==2
    assert last["final_cumulative_incidence"]==pytest.approx(1/3)
    assert last["competing_cumulative_incidence"]==pytest.approx(1/3)
    assert last["cause_specific_km"]==pytest.approx(.5)
    with pytest.raises(ValueError):curve(rows+rows[:1],5)


def test_last_visible_integer():
    assert parse_integer("First I tried 91.\n#### 007")==7
    assert parse_integer("#### 7\nI should reconsider.") is None
    assert parse_integer("No final answer yet") is None
