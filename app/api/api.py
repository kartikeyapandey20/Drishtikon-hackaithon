from fastapi import APIRouter
from app.api.endpoints import auth, users, images, processing
# Add import for specialized endpoints
from app.api.endpoints import specialized

# Create main API router
api_router = APIRouter()

# Include routers from different endpoint modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(images.router, prefix="/images", tags=["Images"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processing"])
# Add specialized routes for visually impaired features
api_router.include_router(
    specialized.router,
    prefix="/specialized",
    tags=["specialized features"]
) 