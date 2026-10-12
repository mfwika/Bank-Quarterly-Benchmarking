from bankbench.crosscheck import npl_crosscheck


def _rows(cur, sm, npl, ratio, npl_formula=None):
    return [dict(section="NPL", label="Current", value=cur, formula=None),
            dict(section="NPL", label="Special Mention", value=sm, formula=None),
            dict(section="NPL", label="NPL", value=npl, formula=npl_formula),
            dict(section="RATIO", label="NPL Gross (%)", value=ratio, formula=None)]


def test_consistent_npl():
    x = npl_crosscheck(_rows(95.0, 3.2, 1.8, 1.81))
    assert x["ok"] and abs(x["hitung"] - 1.8) < 1e-9


def test_literal_formula_and_fraction_ratio():
    x = npl_crosscheck(_rows(95.0, 3.2, None, 0.0181, npl_formula="=(1000000+800000)/1000000"))
    assert x["ok"] and abs(x["laporan"] - 1.81) < 1e-9


def test_inconsistent_npl_flagged():
    x = npl_crosscheck(_rows(90.0, 5.0, 5.0, 1.8))
    assert not x["ok"] and x["selisih"] > 3


def test_missing_data_returns_none():
    assert npl_crosscheck(_rows(95.0, 3.2, None, 1.8, npl_formula="=I700/1000000")) is None
