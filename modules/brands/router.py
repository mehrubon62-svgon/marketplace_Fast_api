from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User
from modules.users.router import require_admin
from modules.brands.schemas import BrandCreate, BrandOut
from modules.brands.crud import create_brand, get_all_brands, get_brand_by_id, delete_brand

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=list[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return get_all_brands(db)


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/", response_model=BrandOut)
def add_brand(data: BrandCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return create_brand(db, **data.model_dump())


@router.delete("/{brand_id}")
def remove_brand(brand_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not delete_brand(db, brand_id):
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"detail": "Brand deleted"}
