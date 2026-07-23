from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from financeiro_kairo.infrastructure.database.base import Base, TimestampMixin


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DIGITAL_WALLET = "digital_wallet"
    INVESTMENT = "investment"
    OTHER = "other"


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    CLEARED = "cleared"
    CANCELLED = "cancelled"


class CategoryKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    BOTH = "both"


class ImportStatus(StrEnum):
    PENDING = "pending"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    initial_balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    institution: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")

    __table_args__ = (
        CheckConstraint("length(currency_code) = 3", name="currency_code_length"),
        Index("ix_accounts_active_name", "active", "name"),
    )


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default=CategoryKind.EXPENSE.value, nullable=False)
    color: Mapped[str | None] = mapped_column(String(9))
    icon: Mapped[str | None] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped[Category | None] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list[Category]] = relationship(back_populates="parent")

    __table_args__ = (
        UniqueConstraint("parent_id", "normalized_name", name="category_parent_name"),
        Index("ix_categories_parent_active", "parent_id", "active"),
    )


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=TransactionStatus.CLEARED.value, nullable=False
    )
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    transfer_group: Mapped[str | None] = mapped_column(String(36))
    notes: Mapped[str | None] = mapped_column(Text)

    account: Mapped[Account] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship()

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="amount_nonnegative"),
        Index("ix_transactions_date_account", "occurred_on", "account_id"),
        Index("ix_transactions_category_date", "category_id", "occurred_on"),
        Index("ix_transactions_transfer_group", "transfer_group"),
    )


class Brand(TimestampMixin, Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Category | None] = relationship()
    variants: Mapped[list[ProductVariant]] = relationship(back_populates="product")


class ProductVariant(TimestampMixin, Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), nullable=False)
    package_type: Mapped[str | None] = mapped_column(String(40))
    package_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    package_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    units_per_package: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(32), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped[Product] = relationship(back_populates="variants")
    brand: Mapped[Brand | None] = relationship()
    aliases: Mapped[list[ProductAlias]] = relationship(back_populates="variant")

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "brand_id",
            "normalized_name",
            "package_quantity",
            "package_unit",
            name="variant_identity",
        ),
        CheckConstraint("package_quantity > 0", name="package_quantity_positive"),
        CheckConstraint("units_per_package > 0", name="units_per_package_positive"),
        Index("ix_variants_product_brand", "product_id", "brand_id"),
    )


class ProductAlias(TimestampMixin, Base):
    __tablename__ = "product_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    original_text: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="user", nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime)

    variant: Mapped[ProductVariant] = relationship(back_populates="aliases")


class Merchant(TimestampMixin, Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    document: Mapped[str | None] = mapped_column(String(32))
    city: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ImportBatch(TimestampMixin, Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ImportStatus.PENDING.value, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchased_on: Mapped[date] = mapped_column(Date, nullable=False)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id", ondelete="RESTRICT"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    import_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="SET NULL")
    )
    gross_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    merchant: Mapped[Merchant] = relationship()
    account: Mapped[Account | None] = relationship()
    import_batch: Mapped[ImportBatch | None] = relationship()
    items: Mapped[list[PurchaseItem]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("gross_total_cents >= 0", name="gross_nonnegative"),
        CheckConstraint("discount_cents >= 0", name="discount_nonnegative"),
        CheckConstraint("net_total_cents >= 0", name="net_nonnegative"),
        Index("ix_purchases_date_merchant", "purchased_on", "merchant_id"),
    )


class PurchaseItem(TimestampMixin, Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"))
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_description: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_description: Mapped[str] = mapped_column(String(300), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL")
    )
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    purchase: Mapped[Purchase] = relationship(back_populates="items")
    variant: Mapped[ProductVariant | None] = relationship()
    category: Mapped[Category | None] = relationship()
    price_observation: Mapped[PriceObservation | None] = relationship(
        back_populates="purchase_item", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("purchase_id", "line_number", name="purchase_line"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price_cents >= 0", name="unit_price_nonnegative"),
        CheckConstraint("total_cents >= 0", name="total_nonnegative"),
        Index("ix_purchase_items_variant", "variant_id"),
        Index("ix_purchase_items_unconfirmed", "user_confirmed"),
    )


class PriceObservation(TimestampMixin, Base):
    __tablename__ = "price_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_item_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_items.id", ondelete="CASCADE"), unique=True
    )
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"))
    observed_on: Mapped[date] = mapped_column(Date, nullable=False)
    paid_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    normalized_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_price_cents: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    promotion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    purchase_item: Mapped[PurchaseItem] = relationship(back_populates="price_observation")
    variant: Mapped[ProductVariant] = relationship()
    merchant: Mapped[Merchant] = relationship()

    __table_args__ = (
        CheckConstraint("normalized_quantity > 0", name="normalized_quantity_positive"),
        Index("ix_prices_variant_date", "variant_id", "observed_on"),
        Index("ix_prices_merchant_variant_date", "merchant_id", "variant_id", "observed_on"),
    )
