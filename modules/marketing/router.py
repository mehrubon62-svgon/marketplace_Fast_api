from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import get_db, User, Listing
from modules.users.router import require_admin, get_current_user
from modules.marketing.schemas import (
    BannerCreate,
    BannerOut,
    FlashSaleCreate,
    FlashSaleUpdate,
    FlashSaleListingsUpdate,
    FlashSaleOut,
)
from modules.marketing.crud import (
    create_banner,
    get_active_banners,
    delete_banner,
    create_flash_sale,
    get_active_flash_sales,
    get_all_flash_sales,
    get_flash_sale_by_id,
    update_flash_sale,
    set_flash_sale_listings,
    add_listings_to_flash_sale,
    remove_listing_from_flash_sale,
    deactivate_flash_sale,
)

router = APIRouter(prefix="/marketing", tags=["Marketing"])


@router.get("/banners", response_model=list[BannerOut])
def list_banners(db: Session = Depends(get_db)):
    return get_active_banners(db)


@router.post("/banners", response_model=BannerOut)
def add_banner(data: BannerCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return create_banner(db, **data.model_dump())


@router.delete("/banners/{banner_id}")
def remove_banner(banner_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not delete_banner(db, banner_id):
        raise HTTPException(status_code=404, detail="Banner not found")
    return {"detail": "Banner deleted"}


def _validate_listings(db: Session, listing_ids: list[int], user: User) -> list[Listing]:
    """Проверяет, что все товары существуют и принадлежат пользователю (или он админ)."""
    listings = db.query(Listing).filter(Listing.id.in_(listing_ids)).all()
    found_ids = {l.id for l in listings}
    missing = [i for i in listing_ids if i not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Listings not found: {missing}")

    if user.role.value != "admin":
        not_owned = [l.id for l in listings if l.owner_id != user.id]
        if not_owned:
            raise HTTPException(
                status_code=403,
                detail=f"You don't own these listings: {not_owned}",
            )
    return listings


@router.get("/flash-sales", response_model=list[FlashSaleOut])
def list_flash_sales(active_only: bool = True, db: Session = Depends(get_db)):
    return get_active_flash_sales(db) if active_only else get_all_flash_sales(db)


@router.get("/flash-sales/{fs_id}", response_model=FlashSaleOut)
def get_flash_sale(fs_id: int, db: Session = Depends(get_db)):
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    return fs


@router.post("/flash-sales", response_model=FlashSaleOut)
def add_flash_sale(
    data: FlashSaleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Создать акцию на один или несколько товаров.
    Продавец может создавать акции только на свои товары; админ — на любые.
    """
    if data.starts_at >= data.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be before ends_at")

    _validate_listings(db, data.listing_ids, user)
    return create_flash_sale(
        db,
        listing_ids=data.listing_ids,
        discount_percent=data.discount_percent,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        title=data.title,
    )


@router.patch("/flash-sales/{fs_id}", response_model=FlashSaleOut)
def edit_flash_sale(
    fs_id: int,
    data: FlashSaleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Flash sale not found")

    if user.role.value != "admin":
        not_owned = [l.id for l in fs.listings if l.owner_id != user.id]
        if not_owned:
            raise HTTPException(status_code=403, detail="Not your flash sale")

    if data.starts_at and data.ends_at and data.starts_at >= data.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be before ends_at")

    return update_flash_sale(db, fs_id, **data.model_dump(exclude_unset=True))


@router.put("/flash-sales/{fs_id}/listings", response_model=FlashSaleOut)
def replace_flash_sale_listings(
    fs_id: int,
    data: FlashSaleListingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Полностью заменить список товаров в акции."""
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    _validate_listings(db, data.listing_ids, user)
    return set_flash_sale_listings(db, fs_id, data.listing_ids)


@router.post("/flash-sales/{fs_id}/listings", response_model=FlashSaleOut)
def add_flash_sale_listings(
    fs_id: int,
    data: FlashSaleListingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Добавить товары к существующей акции."""
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    _validate_listings(db, data.listing_ids, user)
    return add_listings_to_flash_sale(db, fs_id, data.listing_ids)


@router.delete("/flash-sales/{fs_id}/listings/{listing_id}", response_model=FlashSaleOut)
def remove_flash_sale_listing(
    fs_id: int,
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Убрать конкретный товар из акции (саму акцию не удаляет)."""
    fs = get_flash_sale_by_id(db, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Flash sale not found")
    if user.role.value != "admin":
        not_owned = [l.id for l in fs.listings if l.owner_id != user.id]
        if not_owned:
            raise HTTPException(status_code=403, detail="Not your flash sale")
    if listing_id not in {l.id for l in fs.listings}:
        raise HTTPException(status_code=404, detail="Listing is not in this flash sale")
    return remove_listing_from_flash_sale(db, fs_id, listing_id)


@router.delete("/flash-sales/{fs_id}")
def remove_flash_sale(fs_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if not deactivate_flash_sale(db, fs_id):
        raise HTTPException(status_code=404, detail="Flash sale not found")
    return {"detail": "Flash sale deactivated"}
