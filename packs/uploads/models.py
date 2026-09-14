"""Per-file batch status supplied to the learner."""
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadResult:
    file_id: str
    error: str | None = None
