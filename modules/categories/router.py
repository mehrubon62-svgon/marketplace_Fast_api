from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import get_current_user, require_admin
from modules.categories.schemas import CategoryCreate, CategoryOut
from modules.categories.crud import (
    create_category,
    get_all_categories,
    get_category_by_name,
    delete_category,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryOut)
def add_category(data: CategoryCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if get_category_by_name(db, data.name):
        raise HTTPException(status_code=400, detail="Category already exists")
    if data.parent_id:
        from modules.categories.crud import get_category_by_id
        if not get_category_by_id(db, data.parent_id):
            raise HTTPException(status_code=404, detail="Parent category not found")
    return create_category(db, data.name, data.parent_id)


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return get_all_categories(db)


@router.delete("/{category_id}")
def remove_category(category_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    cat = delete_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"detail": "Category deleted"}
