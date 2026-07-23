from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from financeiro_kairo.application.services.catalog import normalize_text
from financeiro_kairo.domain.models import Category, CategoryKind


class CategoryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, *, include_inactive: bool = False) -> list[Category]:
        query = select(Category).order_by(Category.parent_id, Category.name)
        if not include_inactive:
            query = query.where(Category.active.is_(True))
        return list(self.session.scalars(query).all())

    def create(
        self,
        *,
        name: str,
        kind: str = CategoryKind.EXPENSE.value,
        parent_id: int | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> Category:
        clean_name = name.strip()
        if len(clean_name) < 2:
            raise ValueError("category name must have at least two characters")
        if kind not in {item.value for item in CategoryKind}:
            raise ValueError("invalid category kind")
        if parent_id is not None:
            self._require(parent_id)
        normalized = normalize_text(clean_name)
        existing = self.session.scalar(
            select(Category).where(
                Category.parent_id == parent_id,
                Category.normalized_name == normalized,
            )
        )
        if existing is not None:
            raise ValueError("category already exists under this parent")
        category = Category(
            name=clean_name,
            normalized_name=normalized,
            kind=kind,
            parent_id=parent_id,
            color=color,
            icon=icon,
        )
        self.session.add(category)
        self.session.flush()
        return category

    def update(
        self,
        category_id: int,
        *,
        name: str | None = None,
        parent_id: int | None = None,
        kind: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> Category:
        category = self._require(category_id)
        if parent_id == category_id:
            raise ValueError("category cannot be its own parent")
        if parent_id is not None:
            self._require(parent_id)
            self._assert_no_cycle(category_id, parent_id)
        if name is not None:
            clean_name = name.strip()
            if len(clean_name) < 2:
                raise ValueError("category name must have at least two characters")
            category.name = clean_name
            category.normalized_name = normalize_text(clean_name)
        if kind is not None:
            if kind not in {item.value for item in CategoryKind}:
                raise ValueError("invalid category kind")
            category.kind = kind
        category.parent_id = parent_id
        category.color = color
        category.icon = icon
        self.session.flush()
        return category

    def archive(self, category_id: int) -> Category:
        category = self._require(category_id)
        category.active = False
        self.session.flush()
        return category

    def restore(self, category_id: int) -> Category:
        category = self._require(category_id)
        category.active = True
        self.session.flush()
        return category

    def _assert_no_cycle(self, category_id: int, parent_id: int) -> None:
        current_id: int | None = parent_id
        visited: set[int] = set()
        while current_id is not None:
            if current_id == category_id:
                raise ValueError("category hierarchy cannot contain cycles")
            if current_id in visited:
                raise ValueError("existing category hierarchy contains a cycle")
            visited.add(current_id)
            current = self._require(current_id)
            current_id = current.parent_id

    def _require(self, category_id: int) -> Category:
        category = self.session.get(Category, category_id)
        if category is None:
            raise LookupError(f"category {category_id} was not found")
        return category
