from ghost_shield.metrics import LeakageScorer


def test_identical_text_is_critical_leakage() -> None:
    scorer = LeakageScorer()
    result = scorer.compute_score(
        "patient account record contains sensitive diagnosis information",
        "patient account record contains sensitive diagnosis information",
    )

    assert result.overall_leakage_score > 0.9
    assert result.risk_level == "CRITICAL"


def test_unrelated_text_is_low_leakage() -> None:
    scorer = LeakageScorer()
    result = scorer.compute_score(
        "patient account record contains sensitive diagnosis information",
        "the weather forecast predicts rain over the mountain valley",
    )

    assert result.overall_leakage_score < 0.2
    assert result.risk_level == "LOW"


def test_empty_and_single_word_inputs_are_safe() -> None:
    scorer = LeakageScorer()

    empty_result = scorer.compute_score("", "")
    single_word_result = scorer.compute_score("secret", "secret")

    assert empty_result.overall_leakage_score == 0.0
    assert empty_result.risk_level == "LOW"
    assert single_word_result.overall_leakage_score >= 0.0
    assert single_word_result.risk_level in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
