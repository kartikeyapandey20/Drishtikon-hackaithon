from .repository import NewsRepository
from .schema import NewsResponse

class NewsDomain:
    def __init__(self):
        self.news_repository = NewsRepository()
    
    async def get_news_by_query(self, query: str, days: int = 7, limit: int = 10, force_refresh: bool = False) -> NewsResponse:
        return await self.news_repository.get_news_by_query(query, days, limit, force_refresh)
