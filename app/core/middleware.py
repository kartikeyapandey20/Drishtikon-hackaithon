from fastapi import Request, Response, HTTPException, status
import time
from typing import Dict, Callable, Awaitable
from collections import defaultdict
import asyncio
from loguru import logger


class RateLimitMiddleware:
    """Middleware to implement rate limiting for API requests."""
    
    def __init__(
        self,
        app: Callable[[Request], Awaitable[Response]],
        limit: int = 100,
        window: int = 60,
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: The FastAPI application
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.app = app
        self.limit = limit
        self.window = window
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_task = None
    
    async def __call__(self, request: Request) -> Response:
        """Process each request and apply rate limiting."""
        # Clean up old request timestamps periodically
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_requests())
        
        # Get client IP (consider using X-Forwarded-For header for proxied requests)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if the client has exceeded rate limit
        current_time = time.time()
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if current_time - timestamp < self.window
        ]
        
        if len(self.requests[client_ip]) >= self.limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again in {self.window} seconds.",
                headers={"Retry-After": str(self.window)},
            )
        
        # Add current request timestamp
        self.requests[client_ip].append(current_time)
        
        # Process the request
        return await self.app(request)
    
    async def _cleanup_old_requests(self) -> None:
        """Periodically clean up old request timestamps."""
        while True:
            await asyncio.sleep(self.window)
            current_time = time.time()
            for client_ip in list(self.requests.keys()):
                self.requests[client_ip] = [
                    timestamp for timestamp in self.requests[client_ip]
                    if current_time - timestamp < self.window
                ]
                if not self.requests[client_ip]:
                    del self.requests[client_ip]


class LoggingMiddleware:
    """Middleware to log API requests and responses."""
    
    def __init__(self, app: Callable[[Request], Awaitable[Response]]):
        """Initialize logging middleware."""
        self.app = app
    
    async def __call__(self, request: Request) -> Response:
        """Process each request and log details."""
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url = request.url
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        
        # Log request
        logger.info(f"Request: {method} {url} from {client_ip} - {user_agent}")
        
        # Process request
        try:
            response = await self.app(request)
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Response: {response.status_code} for {method} {url} - "
                f"Duration: {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log failed request
            logger.error(
                f"Error processing {method} {url} - "
                f"Duration: {process_time:.3f}s - Error: {str(e)}"
            )
            
            raise 