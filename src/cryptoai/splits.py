from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


def _utc_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    """Normalize naive or timezone-aware boundaries to UTC."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


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
        return obj.loc[_utc_timestamp(self.discovery_start) : _utc_timestamp(self.discovery_end)]

    def validation_1_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[_utc_timestamp(self.validation_1_start) : _utc_timestamp(self.validation_1_end)]

    def validation_2_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[_utc_timestamp(self.validation_2_start) : _utc_timestamp(self.validation_2_end)]

    def pre_holdout_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[_utc_timestamp(self.discovery_start) : _utc_timestamp(self.validation_2_end)]

    def holdout_slice(self, obj: pd.Series | pd.DataFrame):
        return obj.loc[_utc_timestamp(self.holdout_start) : _utc_timestamp(self.holdout_end)]

    def assert_selection_index_is_pre_holdout(self, index: pd.DatetimeIndex) -> None:
        if not len(index):
            return
        max_ts = pd.Timestamp(index.max())
        if max_ts.tzinfo is None:
            max_ts = max_ts.tz_localize("UTC")
        else:
            max_ts = max_ts.tz_convert("UTC")
        if max_ts >= _utc_timestamp(self.holdout_start):
            raise ValueError("Selection leaked into the frozen 2025-2026 holdout period")
