from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException, status
import feedparser
from .schema import NewsArticle, NewsResponse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsRepository:
    def __init__(self):
        self.rss_feeds = {
            # General News Sources
            "reuters": "https://www.reuters.com/rssFeed/worldNews",
            "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "cnn": "https://rss.cnn.com/rss/edition.rss",
            "al_jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "india_today": "https://www.indiatoday.in/rss/1206577",
            "the_guardian": "https://www.theguardian.com/world/rss",
            "hindu": "https://www.thehindu.com/news/international/feeder/default.rss",
            "ndtv": "https://feeds.feedburner.com/ndtvnews-world-news",
            "times_of_india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
            "news18": "https://www.news18.com/rss/world.xml"
        }
        self.cache_duration = timedelta(hours=1)
        self._last_fetch = None
        self._cached_news = None

    async def get_news_by_query(
        self,
        days: int = 7,
        limit: int = 10,
        force_refresh: bool = True
    ) -> NewsResponse:
        """
        Fetch latest news articles.

        Args:
            days (int): Number of days to look back for news
            limit (int): Maximum number of articles to return
            force_refresh (bool): Whether to force a refresh of cached data

        Returns:
            NewsResponse: Object containing the news articles and metadata
        """
        # Check cache if not forcing refresh
        if not force_refresh and self._cached_news and self._last_fetch:
            if datetime.now() - self._last_fetch < self.cache_duration:
                return self._cached_news

        try:
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            logger.info(f"Fetching latest news")
            logger.info(f"Using cutoff date: {cutoff_date}")

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                for source, feed_url in self.rss_feeds.items():
                    try:
                        logger.info(f"Fetching feed from {source}: {feed_url}")
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': 'application/rss+xml, application/xml, application/xhtml+xml, text/html;q=0.9, text/plain;q=0.8, */*;q=0.5',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Connection': 'keep-alive',
                        }
                        response = await client.get(feed_url, headers=headers)
                        
                        if response.status_code == 200:
                            logger.info(f"Successfully fetched feed from {source}")
                            feed = feedparser.parse(response.content)
                            
                            # Handle different feed formats
                            entries = feed.entries if hasattr(feed, 'entries') else []
                            logger.info(f"Found {len(entries)} entries in {source}")
                            
                            for entry in entries:
                                try:
                                    # Handle different date formats
                                    if hasattr(entry, 'published_parsed'):
                                        published_at = datetime(*entry.published_parsed[:6])
                                    elif hasattr(entry, 'updated_parsed'):
                                        published_at = datetime(*entry.updated_parsed[:6])
                                    elif hasattr(entry, 'published'):
                                        try:
                                            published_at = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                                        except ValueError:
                                            published_at = datetime.now()
                                    else:
                                        published_at = datetime.now()  # Fallback to current time
                                        
                                    if published_at < cutoff_date:
                                        continue

                                    # Get image URL from various possible sources
                                    image_url = None
                                    if 'media_content' in entry:
                                        image_url = entry.media_content[0].get('url')
                                    elif 'media_thumbnail' in entry:
                                        image_url = entry.media_thumbnail[0].get('url')
                                    elif 'links' in entry:
                                        for link in entry.links:
                                            if link.get('type', '').startswith('image/'):
                                                image_url = link.get('href')
                                                break

                                    news_article = NewsArticle(
                                        title=entry.title if hasattr(entry, 'title') else 'No Title',
                                        content=entry.get('description', entry.get('summary', entry.title if hasattr(entry, 'title') else 'No Content')),
                                        url=entry.link if hasattr(entry, 'link') else '#',
                                        source=source,
                                        published_at=published_at,
                                        image_url=image_url,
                                        author=entry.get('author', None),
                                        relevance_score=1.0  # Default score for all articles
                                    )
                                    articles.append(news_article)
                                    logger.info(f"Found article from {source}: {news_article.title[:50]}...")
                                except (AttributeError, ValueError, TypeError) as e:
                                    logger.error(f"Error processing entry from {source}: {str(e)}")
                                    continue
                        else:
                            logger.warning(f"Failed to fetch feed from {source}. Status code: {response.status_code}")
                    except Exception as e:
                        logger.error(f"Error fetching feed from {source}: {str(e)}")
                        continue

            # Sort by date only
            articles.sort(key=lambda x: -x.published_at.timestamp())
            articles = articles[:limit]

            logger.info(f"Found {len(articles)} articles")
            
            news_response = NewsResponse(
                articles=articles,
                total_count=len(articles),
                last_updated=datetime.now()
            )

            self._cached_news = news_response
            self._last_fetch = datetime.now()

            return news_response

        except Exception as e:
            logger.error(f"Unexpected error in get_news_by_query: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
