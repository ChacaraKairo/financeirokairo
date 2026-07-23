from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def decimal_to_cents(value: Decimal) -> int:
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    account_type: str = Field(min_length=2, max_length=30)
    initial_balance_cents: int = 0
    currency_code: str = Field(default="BRL", min_length=3, max_length=3)
    institution: str | None = Field(default=None, max_length=120)


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    transaction_type: Literal["income", "expense"]
    description: str = Field(min_length=2, max_length=240)
    amount_cents: int = Field(gt=0)
    occurred_on: date
    account_id: int = Field(gt=0)
    category_id: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=2000)


class TransferCreate(BaseModel):
    description: str = Field(min_length=2, max_length=240)
    amount_cents: int = Field(gt=0)
    occurred_on: date
    source_account_id: int = Field(gt=0)
    destination_account_id: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def accounts_must_differ(self) -> TransferCreate:
        if self.source_account_id == self.destination_account_id:
            raise ValueError("source and destination accounts must be different")
        return self


class ImportItemPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    line_no: int = Field(ge=1)
    description: str = Field(min_length=2, max_length=300)
    brand: str | None = Field(default=None, max_length=120)
    quantity: Decimal = Field(gt=0)
    unit_label: str = Field(min_length=1, max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> ImportItemPayload:
        expected = (self.quantity * self.unit_price - self.discount).quantize(Decimal("0.01"))
        if abs(expected - self.line_total) > Decimal("0.02"):
            raise ValueError("line_total does not match quantity, unit_price and discount")
        return self


class ImportTotals(BaseModel):
    gross_total: Decimal = Field(ge=0)
    discount_total: Decimal = Field(ge=0)
    net_total: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_totals(self) -> ImportTotals:
        expected = (self.gross_total - self.discount_total).quantize(Decimal("0.01"))
        if abs(expected - self.net_total) > Decimal("0.02"):
            raise ValueError("net_total does not match gross_total minus discount_total")
        return self


class PurchasePayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    store_name: str = Field(min_length=2, max_length=180)
    purchase_date: date
    document_number: str | None = Field(default=None, max_length=100)
    account_id: int | None = Field(default=None, gt=0)
    items: list[ImportItemPayload] = Field(min_length=1)
    totals: ImportTotals

    @model_validator(mode="after")
    def validate_item_sum(self) -> PurchasePayload:
        item_total = sum((item.line_total for item in self.items), start=Decimal("0"))
        if abs(item_total - self.totals.net_total) > Decimal("0.02"):
            raise ValueError("sum of item totals does not match purchase net total")
        return self


class ImportEnvelope(BaseModel):
    source: Literal["mercado-json", "api", "manual", "csv-convertido"]
    currency: Literal["BRL"] = "BRL"
    purchase: PurchasePayload
