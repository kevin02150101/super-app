# 04 — Repository 層設計

## 1. 職責

- 封裝所有資料存取邏輯（SQLAlchemy）。
- 對 Service 提供以「實體 / DTO」為單位的方法。
- **禁止**包含業務邏輯（驗證、計算、權限）。

## 2. BaseRepository

```python
# repositories/base_repository.py
from typing import Generic, TypeVar, Type, Optional, List
from extensions import db

T = TypeVar("T")

class BaseRepository(Generic[T]):
    model: Type[T]

    @classmethod
    def get(cls, id_: int) -> Optional[T]:
        return db.session.get(cls.model, id_)

    @classmethod
    def list(cls, **filters) -> List[T]:
        return db.session.query(cls.model).filter_by(**filters).all()

    @classmethod
    def add(cls, entity: T) -> T:
        db.session.add(entity)
        db.session.commit()
        return entity

    @classmethod
    def delete(cls, entity: T) -> None:
        db.session.delete(entity)
        db.session.commit()
```

## 3. 各 Repository

### UserRepository
- `get_by_email(email) -> User | None`
- `create(email, password_hash, nickname) -> User`

### AnalysisRepository
- `create(user_id, image_path, summary, raw_json) -> Analysis`
- `paginate(user_id, page, per_page) -> Pagination`
- `get_by_id_for_user(id_, user_id) -> Analysis | None`
- `delete_for_user(id_, user_id) -> bool`
- `sum_calories(user_id, start, end) -> float`
- `group_by_category(user_id) -> list[(category, count, total_calories)]`

### FoodItemRepository
- `bulk_create(analysis_id, items: list[dict]) -> list[FoodItem]`
- `list_by_analysis(analysis_id) -> list[FoodItem]`

## 4. 規約

- 所有查詢必須以 `user_id` 過濾，避免越權。
- Repository 不丟業務例外（如 `PermissionError`），改回傳 `None` / `bool`，由 Service 解讀。
