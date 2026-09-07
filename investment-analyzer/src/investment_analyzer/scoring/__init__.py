"""Erklärbares Scoring (Auftrag §7). Siehe ``score.py`` für Details und Leitplanken."""

from investment_analyzer.scoring.score import (
    DEFAULT_WEIGHTS,
    KLASSE_BEOBACHTEN,
    KLASSE_DATENLAGE_UNZUREICHEND,
    KLASSE_DERZEIT_UNATTRAKTIV,
    KLASSE_VERTIEFT_PRUEFEN,
    NOT_YET_IMPLEMENTABLE_COMPONENTS,
    ComponentScore,
    MetricNote,
    RiskDeduction,
    ScoreResult,
    compute_score,
    score_entity,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "KLASSE_BEOBACHTEN",
    "KLASSE_DATENLAGE_UNZUREICHEND",
    "KLASSE_DERZEIT_UNATTRAKTIV",
    "KLASSE_VERTIEFT_PRUEFEN",
    "NOT_YET_IMPLEMENTABLE_COMPONENTS",
    "ComponentScore",
    "MetricNote",
    "RiskDeduction",
    "ScoreResult",
    "compute_score",
    "score_entity",
]
