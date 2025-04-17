from .start import router as start_router
from .search import router as search_router
from .orders import router as orders_router
from .catalog import router as catalog_router

routers = [start_router, search_router,  orders_router, catalog_router]