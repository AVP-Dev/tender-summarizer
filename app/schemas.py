from __future__ import annotations

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    filename: str
    summary: str
