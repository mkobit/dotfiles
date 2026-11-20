from types import SimpleNamespace

from conftest import _slow_test_summary


def test_duration_summary_includes_setup_call_and_teardown():
    reports = [
        SimpleNamespace(nodeid="slow", when="setup", duration=4.0),
        SimpleNamespace(nodeid="slow", when="call", duration=1.0),
        SimpleNamespace(nodeid="slow", when="teardown", duration=2.0),
        SimpleNamespace(nodeid="fast", when="call", duration=3.0),
    ]
    summary = _slow_test_summary(reports)
    assert summary.index("`slow`") < summary.index("`fast`")
    assert "7.000" in summary
    assert "4.000 | 1.000 | 2.000" in summary


def test_duration_summary_limits_rows_and_escapes_table_cells():
    reports = [SimpleNamespace(nodeid=f"test[{i}|`value`]<x>", when="call", duration=float(i)) for i in range(30)]
    summary = _slow_test_summary(reports)
    assert "test[29&#124;&#96;value&#96;]&lt;x&gt;" in summary
    assert "test[0" not in summary
    assert summary.count("| `test[") == 20
