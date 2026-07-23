from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from financeiro_kairo.domain.models import ProductAlias, ProductVariant

_UNIT_FACTORS: dict[tuple[str, str], Decimal] = {
    ("g", "kg"): Decimal("0.001"),
    ("kg", "g"): Decimal("1000"),
    ("ml", "l"): Decimal("0.001"),
    ("l", "ml"): Decimal("1000"),
}
_UNIT_ALIASES = {
    "quilo": "kg",
    "quilos": "kg",
    "kilograma": "kg",
    "kilogramas": "kg",
    "grama": "g",
    "gramas": "g",
    "litro": "l",
    "litros": "l",
    "mililitro": "ml",
    "mililitros": "ml",
    "unidade": "un",
    "unidades": "un",
    "und": "un",
    "unid": "un",
    "pct": "pacote",
    "pc": "un",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    tokens = re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", without_marks)
    expanded = [_UNIT_ALIASES.get(token, token) for token in tokens]
    return " ".join(expanded).replace(",", ".").strip()


@dataclass(frozen=True, slots=True)
class MatchResult:
    variant_id: int | None
    confidence: Decimal
    stage: str
    explanation: str


class ProductMatcherService:
    AUTO_ACCEPT = Decimal("97")
    REVIEW = Decimal("85")

    def __init__(self, session: Session) -> None:
        self.session = session

    def match(self, raw_description: str) -> MatchResult:
        normalized = normalize_text(raw_description)
        exact = self.session.scalar(
            select(ProductAlias).where(ProductAlias.normalized_text == normalized)
        )
        if exact is not None:
            return MatchResult(exact.variant_id, Decimal("100"), "alias_exact", "alias confirmado")

        aliases = self.session.scalars(select(ProductAlias)).all()
        if not aliases:
            return MatchResult(None, Decimal("0"), "none", "catálogo sem aliases")

        alias_map = {alias.normalized_text: alias for alias in aliases}
        candidate = process.extractOne(normalized, alias_map.keys(), scorer=fuzz.token_set_ratio)
        if candidate is None:
            return MatchResult(None, Decimal("0"), "none", "nenhum candidato")

        text, score, _ = candidate
        confidence = Decimal(str(score)).quantize(Decimal("0.01"))
        alias = alias_map[text]
        if confidence < self.REVIEW:
            return MatchResult(None, confidence, "below_threshold", f"melhor candidato: {text}")
        return MatchResult(alias.variant_id, confidence, "fuzzy", f"similar ao alias: {text}")


class PriceNormalizationService:
    @staticmethod
    def convert_quantity(quantity: Decimal, source_unit: str, target_unit: str) -> Decimal:
        source = _UNIT_ALIASES.get(source_unit.casefold(), source_unit.casefold())
        target = _UNIT_ALIASES.get(target_unit.casefold(), target_unit.casefold())
        if source == target:
            return quantity
        factor = _UNIT_FACTORS.get((source, target))
        if factor is None:
            raise ValueError(f"incompatible units: {source_unit} and {target_unit}")
        return quantity * factor

    @classmethod
    def unit_price_cents(
        cls,
        paid_cents: int,
        purchased_quantity: Decimal,
        variant: ProductVariant,
        target_unit: str,
    ) -> tuple[Decimal, Decimal]:
        package_content = variant.package_quantity * variant.units_per_package
        content_in_target = cls.convert_quantity(package_content, variant.package_unit, target_unit)
        normalized_quantity = purchased_quantity * content_in_target
        if normalized_quantity <= 0:
            raise ValueError("normalized quantity must be positive")
        price = (Decimal(paid_cents) / normalized_quantity).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )
        return normalized_quantity, price
