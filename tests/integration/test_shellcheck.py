def test_shellcheck_candidate_has_required_keys(shellcheck_candidate):
    assert "sourceRelative" in shellcheck_candidate
    assert "sourceAbsolute" in shellcheck_candidate
