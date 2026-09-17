from app.routes.detection import router as detection_router
from app.routes.health import router as health_router
from app.routes.table_zones import router as table_zones_router

__all__ = ["detection_router", "health_router", "table_zones_router"]
