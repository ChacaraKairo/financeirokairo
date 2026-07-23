from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from financeiro_kairo.application.schemas import ImportEnvelope, decimal_to_cents
from financeiro_kairo.application.services.catalog import ProductMatcherService, normalize_text
from financeiro_kairo.domain.models import (
    ImportBatch,
    ImportStatus,
    Merchant,
    Purchase,
    PurchaseItem,
)


class DuplicateImportError(ValueError):
    pass


class PurchaseImportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.matcher = ProductMatcherService(session)

    @staticmethod
    def canonical_payload_hash(payload: dict[str, object]) -> str:
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def import_payload(self, raw_payload: dict[str, object], source_name: str) -> Purchase:
        envelope = ImportEnvelope.model_validate(raw_payload)
        source_hash = self.canonical_payload_hash(raw_payload)
        duplicate = self.session.scalar(
            select(ImportBatch).where(ImportBatch.source_hash == source_hash)
        )
        if duplicate is not None:
            raise DuplicateImportError(f"payload already imported in batch {duplicate.id}")

        batch = ImportBatch(
            source_name=source_name,
            source_hash=source_hash,
            status=ImportStatus.PENDING.value,
            total_lines=len(envelope.purchase.items),
        )
        self.session.add(batch)
        self.session.flush()

        merchant = self._find_or_create_merchant(envelope.purchase.store_name)
        purchase = Purchase(
            purchased_on=envelope.purchase.purchase_date,
            merchant_id=merchant.id,
            account_id=envelope.purchase.account_id,
            import_batch_id=batch.id,
            gross_total_cents=decimal_to_cents(envelope.purchase.totals.gross_total),
            discount_cents=decimal_to_cents(envelope.purchase.totals.discount_total),
            net_total_cents=decimal_to_cents(envelope.purchase.totals.net_total),
            source_type=envelope.source,
            document_number=envelope.purchase.document_number,
        )
        self.session.add(purchase)
        self.session.flush()

        matched = 0
        for item_data in envelope.purchase.items:
            result = self.matcher.match(item_data.description)
            if result.variant_id is not None:
                matched += 1
            item = PurchaseItem(
                purchase_id=purchase.id,
                line_number=item_data.line_no,
                raw_description=item_data.description,
                normalized_description=normalize_text(item_data.description),
                variant_id=result.variant_id,
                quantity=item_data.quantity,
                unit_price_cents=decimal_to_cents(item_data.unit_price),
                discount_cents=decimal_to_cents(item_data.discount),
                total_cents=decimal_to_cents(item_data.line_total),
                match_confidence=result.confidence,
                user_confirmed=result.confidence >= Decimal("97"),
            )
            purchase.items.append(item)

        batch.matched_lines = matched
        batch.status = (
            ImportStatus.COMPLETED.value if matched == batch.total_lines else ImportStatus.REVIEW.value
        )
        self.session.flush()
        return purchase

    def _find_or_create_merchant(self, name: str) -> Merchant:
        normalized = normalize_text(name)
        merchant = self.session.scalar(
            select(Merchant).where(Merchant.normalized_name == normalized)
        )
        if merchant is not None:
            return merchant
        merchant = Merchant(name=name.strip(), normalized_name=normalized)
        self.session.add(merchant)
        self.session.flush()
        return merchant
