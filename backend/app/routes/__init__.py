# Initialize the routes package
from .auth_routes import router as auth_router
from .table_routes import router as table_router
from .column_routes import router as column_router
from .data_routes import router as data_router

# Export the routers for easy importing
__all__ = ["auth_router", "table_router", "column_router", "data_router"]
