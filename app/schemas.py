from __future__ import annotations

from pydantic import BaseModel, Field


class TenderSummary(BaseModel):
    contract_amount: str | None = Field(
        default=None, description="Сумма контракта с валютой"
    )
    deadlines: str | None = Field(default=None, description="Сроки выполнения работ")
    key_requirements: list[str] = Field(
        default_factory=list, description="Ключевые требования к исполнителю"
    )
    penalties: list[str] = Field(
        default_factory=list, description="Штрафы и санкции за нарушение условий"
    )


class SummaryResponse(BaseModel):
    filename: str
    pages_processed: int | None = None
    summary: TenderSummary
