"""
Test suite for error handling and retry logic in the crawler service.
"""
import asyncio
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from crawler_service import WebCrawler
from models import CrawlRequest, ErrorType, CrawlError
from config import settings


class TestErrorHandling:
    """Test error handling and retry logic"""
    
    @pytest.fixture
    async def crawler(self):
        """Create a crawler instance for testing"""
        async with WebCrawler() as crawler:
            yield crawler
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample crawl request"""
        return CrawlRequest(
            url="https://example.com",
            max_depth=1,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False
        )
    
    def test_error_classification(self, crawler):
        """Test error classification logic"""
        # Test timeout error
        timeout_error = aiohttp.ClientTimeout()
        error_type, is_retryable = crawler._classify_error(timeout_error)
        assert error_type == ErrorType.TRANSIENT
        assert is_retryable == settings.RETRY_ON_TIMEOUT
        
        # Test connection error
        conn_error = aiohttp.ClientConnectionError()
        error_type, is_retryable = crawler._classify_error(conn_error)
        assert error_type == ErrorType.TRANSIENT
        assert is_retryable == settings.RETRY_ON_CONNECTION_ERROR
        
        # Test 5xx error (transient)
        error_type, is_retryable = crawler._classify_error(None, 502)
        assert error_type == ErrorType.TRANSIENT
        assert is_retryable == True
        
        # Test 4xx error (permanent)
        error_type, is_retryable = crawler._classify_error(None, 404)
        assert error_type == ErrorType.PERMANENT
        assert is_retryable == False
        
        # Test 429 error (rate limiting - retryable)
        error_type, is_retryable = crawler._classify_error(None, 429)
        assert error_type == ErrorType.TRANSIENT
        assert is_retryable == True
        
        # Test unknown error
        unknown_error = Exception("Unknown error")
        error_type, is_retryable = crawler._classify_error(unknown_error)
        assert error_type == ErrorType.UNKNOWN
        assert is_retryable == False
    
    def test_retry_delay_calculation(self, crawler):
        """Test exponential backoff delay calculation"""
        # Test first retry (attempt 1)
        delay = crawler._calculate_retry_delay(1)
        assert delay >= 0
        assert delay <= settings.RETRY_DELAY_MAX
        
        # Test multiple retries
        delays = [crawler._calculate_retry_delay(i) for i in range(1, 6)]
        
        # Delays should generally increase (with jitter)
        for i in range(1, len(delays)):
            assert delays[i] >= 0  # Should be non-negative
            assert delays[i] <= settings.RETRY_DELAY_MAX  # Should not exceed max
    
    def test_create_crawl_error(self, crawler):
        """Test structured error creation"""
        url = "https://example.com"
        exception = aiohttp.ClientTimeout()
        retry_attempts = 2
        
        error = crawler._create_crawl_error(url, exception, None, retry_attempts)
        
        assert isinstance(error, CrawlError)
        assert error.url == url
        assert error.retry_attempts == retry_attempts
        assert error.max_retries == settings.MAX_RETRIES
        assert error.timestamp is not None
        assert error.message == str(exception)
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, crawler, sample_request):
        """Test retry logic for transient errors"""
        url = "https://example.com"
        
        # Mock session to simulate transient error then success
        mock_response = AsyncMock()
        mock_response.status = 502
        mock_response.text = AsyncMock(return_value="<html>Test</html>")
        mock_response.request_info = MagicMock()
        mock_response.history = []
        
        # First call fails with 502, second call succeeds
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                raise aiohttp.ClientResponseError(
                    request_info=MagicMock(),
                    history=[],
                    status=502,
                    message="Bad Gateway"
                )
            else:
                # Second call succeeds
                return mock_response
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            page = await crawler.crawl_url(url, sample_request)
            
            # Should have retried and eventually succeeded
            assert page.status_code == 502  # The successful response status
            assert page.retry_attempts == 1  # One retry attempt
            assert page.error is None  # No error after successful retry
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, crawler, sample_request):
        """Test that permanent errors are not retried"""
        url = "https://example.com"
        
        # Mock session to simulate permanent error
        async def mock_get(*args, **kwargs):
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=[],
                status=404,
                message="Not Found"
            )
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            page = await crawler.crawl_url(url, sample_request)
            
            # Should not retry permanent errors
            assert page.status_code == 0
            assert page.retry_attempts == 0
            assert page.error is not None
            assert page.error.error_type == ErrorType.PERMANENT
            assert page.error.is_retryable == False
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, crawler, sample_request):
        """Test behavior when max retries are exceeded"""
        url = "https://example.com"
        
        # Mock session to always fail with transient error
        async def mock_get(*args, **kwargs):
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=[],
                status=502,
                message="Bad Gateway"
            )
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            page = await crawler.crawl_url(url, sample_request)
            
            # Should have exhausted all retries
            assert page.status_code == 0
            assert page.retry_attempts == settings.MAX_RETRIES
            assert page.error is not None
            assert page.error.error_type == ErrorType.TRANSIENT
            assert page.error.is_retryable == False  # No more retries available
    
    @pytest.mark.asyncio
    async def test_retry_statistics_tracking(self, crawler, sample_request):
        """Test that retry statistics are properly tracked"""
        url = "https://example.com"
        
        # Mock session to simulate mixed success/failure
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails with transient error
                raise aiohttp.ClientResponseError(
                    request_info=MagicMock(),
                    history=[],
                    status=502,
                    message="Bad Gateway"
                )
            else:
                # Second call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html>Success</html>")
                return mock_response
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            page = await crawler.crawl_url(url, sample_request)
            
            # Check retry statistics
            stats = crawler.get_retry_stats()
            assert stats["total_retries"] >= 1
            assert stats["successful_retries"] >= 1
            assert stats["transient_errors"] >= 1
    
    @pytest.mark.asyncio
    async def test_structured_error_logging(self, crawler, sample_request):
        """Test structured error logging"""
        url = "https://example.com"
        
        # Mock session to simulate error
        async def mock_get(*args, **kwargs):
            raise aiohttp.ClientTimeout()
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            with patch.object(crawler, '_log_structured_error') as mock_log:
                page = await crawler.crawl_url(url, sample_request)
                
                # Should have logged structured error
                assert mock_log.called
                call_args = mock_log.call_args
                assert call_args[0][0].error_type == ErrorType.TRANSIENT
                assert call_args[0][0].url == url
    
    @pytest.mark.asyncio
    async def test_crawl_website_with_errors(self, crawler):
        """Test crawl_website handles errors and retries properly"""
        request = CrawlRequest(
            url="https://example.com",
            max_depth=1,
            follow_links=False,
            extract_text=True,
            extract_images=False,
            extract_links=False
        )
        
        # Mock session to simulate mixed success/failure
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails with transient error
                raise aiohttp.ClientResponseError(
                    request_info=MagicMock(),
                    history=[],
                    status=502,
                    message="Bad Gateway"
                )
            else:
                # Second call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="<html>Success</html>")
                return mock_response
        
        with patch.object(crawler.session, 'get', side_effect=mock_get):
            result = await crawler.crawl_website(request)
            
            # Check result structure
            assert result.status.value == "completed"
            assert len(result.pages) == 1
            assert len(result.structured_errors) == 0  # No errors after successful retry
            assert "total_retries" in result.retry_stats
            assert result.retry_stats["total_retries"] >= 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
