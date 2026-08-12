from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class ResearchSplit:
    """Leakage barrier for strategy discovery.

    Candidate selection may use only discovery/validation periods. The final holdout
    exists to estimate generalization once, after a specification has been locked.
    """

    discovery_start: str = "2020-01-01"
    discovery_end: str = "2022-12-31 23:00:00+00:00"
    validation_1_start: str = "2023-01-01"
    validation_1_end: str = "2023-12-31 23:00:00+00:00"
    validation_2_start: str = "2024-01-01"
    validation_2_end: str = "2024-12-31 23:00:00+00:00"
    holdout_start: str = "2025-01-01"
    holdout_end: str = "2026-07-31 23:00:00+00:00"

    def discovery_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[pd.Timestamp(self.discovery_start, tz="UTC") : pd.Timestamp(self.discovery_end)]

    def validation_1_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[pd.Timestamp(self.validation_1_start, tz="UTC") : pd.Timestamp(self.validation_1_end)]

    def validation_2_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[pd.Timestamp(self.validation_2_start, tz="UTC") : pd.Timestamp(self.validation_2_end)]

    def pre_holdout_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[pd.Timestamp(self.discovery_start, tz="UTC") : pd.Timestamp(self.validation_2_end)]

    def holdout_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[pd.Timestamp(self.holdout_start, tz="UTC") : pd.Timestamp(self.holdout_end)]

    def assert_selection_index_is_pre_holdout(self, index: pd.DatetimeIndex) -> None:
        if len(index) and index.max() >= pd.Timestamp(self.holdout_start, tz="UTC"):
            raise ValueError("Selection leaked into the frozen 2025-2026 holdout period")
