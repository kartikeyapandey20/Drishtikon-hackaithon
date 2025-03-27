from .repository import NewsRepository
from .schema import NewsResponse

class NewsDomain:
    def __init__(self):
        self.news_repository = NewsRepository()
    
    async def get_news_by_query(self, days: int = 7, limit: int = 10, force_refresh: bool = True) -> NewsResponse:
        return await self.news_repository.get_news_by_query( days, limit, force_refresh)
