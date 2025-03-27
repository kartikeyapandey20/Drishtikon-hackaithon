from fastapi import APIRouter, Depends, Query
from typing import Optional
from .domain import NewsDomain
from .schema import NewsResponse

class NewsRouter:
    def __init__(self) -> None:
        self.__domain = NewsDomain()
        
    @property
    def router(self):
        """
        Get the API router for news search.

        Returns:
            APIRouter: The API router.
        """
        api_router = APIRouter(prefix="/news", tags=["News"], responses={404: {"description": "Not found"}})
        
        @api_router.get("/", response_model=NewsResponse)
        async def get_news_by_query(
            days: int = Query(7, description="Number of days to look back for news"),
            limit: int = Query(10, description="Maximum number of articles to return"),
            force_refresh: Optional[bool] = Query(True, description="Force a refresh of the cache")
        ):
            """
            Get news articles based on a search query.
            """
            return await self.__domain.get_news_by_query(days=days, limit=limit, force_refresh=force_refresh)
            
        return api_router
