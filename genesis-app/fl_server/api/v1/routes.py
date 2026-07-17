"""
API v1 router aggregation.
Aggregates all version 1 API endpoint routers into a single router.
"""

from fastapi import APIRouter

from .endpoints import training

# Create the main v1 router
router = APIRouter()

# Include training endpoints with /training prefix
router.include_router(training.router, prefix="/training", tags=["training"])

# Include health endpoint at root level (no prefix)
health_router = APIRouter()
health_router.add_api_route("/health", training.health_check, methods=["GET"], tags=["health"])
router.include_router(health_router)