from contextlib import asynccontextmanager
from fastapi import FastAPI
from models import Base, engine

from modules.users.router import router as users_router
from modules.shops.router import router as shops_router
from modules.categories.router import router as categories_router
from modules.listings.router import router as listings_router
from modules.cart.router import router as cart_router
from modules.orders.router import router as orders_router
from modules.reviews.router import router as reviews_router
from modules.favorites.router import router as favorites_router
from modules.search.router import router as search_router
from modules.ai_agent.router import router as ai_agent_router
from modules.recommendations.router import router as recommendations_router

# Расширения
from modules.addresses.router import router as addresses_router
from modules.brands.router import router as brands_router
from modules.tags.router import router as tags_router
from modules.product_media.router import router as product_media_router
from modules.payments.router import router as payments_router
from modules.shipments.router import router as shipments_router
from modules.coupons.router import router as coupons_router
from modules.chats.router import router as chats_router
from modules.notifications.router import router as notifications_router
from modules.shop_extras.router import router as shop_extras_router
from modules.review_extras.router import router as review_extras_router
from modules.reports.router import router as reports_router
from modules.marketing.router import router as marketing_router
from modules.recently_viewed.router import router as recently_viewed_router

# Новые модули по ТЗ
from modules.wallet.router import router as wallet_router
from modules.discounts.router import router as discounts_router, public_router as discounts_public_router
from modules.websockets.router import router as ws_router
from modules.cache.redis_client import init_redis, close_redis

# Создание таблиц: используем create_all для удобной разработки;
# в проде применяйте `alembic upgrade head`.
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Marketplace API",
    version="2.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "tryItOutEnabled": True,
    },
    lifespan=lifespan,
)

# --- Nested routers ---
listings_router.include_router(product_media_router)
shops_router.include_router(shop_extras_router)
reviews_router.include_router(review_extras_router)

# Базовые
app.include_router(users_router)
app.include_router(wallet_router)
app.include_router(shops_router)
app.include_router(categories_router)
app.include_router(listings_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(reviews_router)
app.include_router(favorites_router)
app.include_router(search_router)
app.include_router(discounts_router)
app.include_router(discounts_public_router)

# Расширения
app.include_router(addresses_router)
app.include_router(brands_router)
app.include_router(tags_router)
app.include_router(payments_router)
app.include_router(shipments_router)
app.include_router(coupons_router)
app.include_router(chats_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(marketing_router)
app.include_router(recently_viewed_router)

# AI
app.include_router(ai_agent_router)
app.include_router(recommendations_router)

# WebSocket
app.include_router(ws_router)


@app.get("/")
def root():
    return {"message": "Marketplace API is running", "docs": "/docs", "ws": "/ws?token=<jwt>"}
