"""
Logging middleware for the crawler microservice.
Provides structured request/response logging.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("middleware")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log it."""
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        url = str(request.url)
        path = request.url.path
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the request
        self.logger.info(
            "HTTP request processed",
            method=method,
            path=path,
            url=url,
            status_code=response.status_code,
            process_time=process_time,
            client_ip=client_ip,
            user_agent=user_agent,
            event_type="http_request"
        )
        
        return response
