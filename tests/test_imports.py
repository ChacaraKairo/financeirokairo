from datetime import date
from decimal import Decimal

import pytest

from financeiro_kairo.application.services.catalog import (
    PriceNormalizationService,
    ProductMatcherService,
    normalize_text,
)
from financeiro_kairo.application.services.imports import DuplicateImportError, PurchaseImportService
from financeiro_kairo.domain.models import Brand, Product, ProductAlias, ProductVariant


def test_catalog_matching_price_and_purchase_import(session):
    brand = Brand(name="Camil", normalized_name="camil")
    product = Product(name="Arroz", normalized_name="arroz", base_unit="kg")
    session.add_all([brand, product])
    session.flush()
    variant = ProductVariant(
        product_id=product.id,
        brand_id=brand.id,
        name="Arroz Camil Tipo 1 5 kg",
        normalized_name="arroz camil tipo 1 5 kg",
        package_type="pacote",
        package_quantity=Decimal("5"),
        package_unit="kg",
        units_per_package=Decimal("1"),
    )
    session.add(variant)
    session.flush()
    session.add(
        ProductAlias(
            variant_id=variant.id,
            original_text="ARROZ CAMIL T1 5KG",
            normalized_text=normalize_text("ARROZ CAMIL T1 5KG"),
        )
    )
    session.flush()

    match = ProductMatcherService(session).match("arroz camil t1 5kg")
    assert match.variant_id == variant.id
    assert match.confidence == Decimal("100")

    quantity, price = PriceNormalizationService.unit_price_cents(
        2990, Decimal("1"), variant, "kg"
    )
    assert quantity == Decimal("5")
    assert price == Decimal("598.000000")

    payload = {
        "source": "mercado-json",
        "currency": "BRL",
        "purchase": {
            "store_name": "Mercado Central",
            "purchase_date": date(2026, 7, 20).isoformat(),
            "document_number": "123",
            "items": [
                {
                    "line_no": 1,
                    "description": "ARROZ CAMIL T1 5KG",
                    "brand": "Camil",
                    "quantity": "1",
                    "unit_label": "un",
                    "unit_price": "29.90",
                    "line_total": "29.90",
                    "discount": "0",
                }
            ],
            "totals": {
                "gross_total": "29.90",
                "discount_total": "0",
                "net_total": "29.90",
            },
        },
    }
    service = PurchaseImportService(session)
    purchase = service.import_payload(payload, "compra.json")
    assert purchase.net_total_cents == 2990
    assert purchase.items[0].variant_id == variant.id
    assert purchase.items[0].user_confirmed is True

    with pytest.raises(DuplicateImportError):
        service.import_payload(payload, "compra-repetida.json")
