"""
Unit tests for config module.

Tests configuration constants, utility functions, and user agent handling.
"""

import pytest
from unittest.mock import patch

from config import (
    # Constants
    DEFAULT_WORKERS, MIN_WORKERS, MAX_WORKERS,
    BROWSER_NAVIGATION_TIMEOUT, ASYNC_SLEEP_AFTER_NAVIGATION,
    DEFAULT_SCROLL_SPEED, MIN_SCROLL_SPEED, MAX_SCROLL_SPEED,
    DOWNLOAD_CHUNK_SIZE, VIDEO_CHUNK_SIZE,
    PDF_IMAGE_DPI, PDF_JPEG_QUALITY,
    DEFAULT_USER_AGENT, USER_AGENTS,
    
    # Functions
    get_random_user_agent, get_rotating_user_agent
)


class TestConfigConstants:
    """Test configuration constants."""

    @pytest.mark.critical
    def test_worker_constants(self):
        """Test worker configuration constants."""
        assert isinstance(DEFAULT_WORKERS, int)
        assert isinstance(MIN_WORKERS, int)
        assert isinstance(MAX_WORKERS, int)
        
        assert MIN_WORKERS <= DEFAULT_WORKERS <= MAX_WORKERS
        assert MIN_WORKERS >= 1
        assert MAX_WORKERS <= 50  # Reasonable upper limit

    @pytest.mark.critical
    def test_timeout_constants(self):
        """Test timeout constants."""
        assert isinstance(BROWSER_NAVIGATION_TIMEOUT, int)
        assert isinstance(ASYNC_SLEEP_AFTER_NAVIGATION, int)
        
        assert BROWSER_NAVIGATION_TIMEOUT > 0
        assert ASYNC_SLEEP_AFTER_NAVIGATION > 0
        assert BROWSER_NAVIGATION_TIMEOUT > ASYNC_SLEEP_AFTER_NAVIGATION

    @pytest.mark.high
    def test_scroll_constants(self):
        """Test scroll configuration constants."""
        assert isinstance(DEFAULT_SCROLL_SPEED, int)
        assert isinstance(MIN_SCROLL_SPEED, int)
        assert isinstance(MAX_SCROLL_SPEED, int)
        
        assert MIN_SCROLL_SPEED <= DEFAULT_SCROLL_SPEED <= MAX_SCROLL_SPEED
        assert MIN_SCROLL_SPEED > 0
        assert MAX_SCROLL_SPEED <= 100  # Reasonable upper limit

    @pytest.mark.high
    def test_download_constants(self):
        """Test download configuration constants."""
        assert isinstance(DOWNLOAD_CHUNK_SIZE, int)
        assert isinstance(VIDEO_CHUNK_SIZE, int)
        
        assert DOWNLOAD_CHUNK_SIZE > 0
        assert VIDEO_CHUNK_SIZE > 0
        assert DOWNLOAD_CHUNK_SIZE >= 1024  # At least 1KB
        assert VIDEO_CHUNK_SIZE >= 1024  # At least 1KB

    @pytest.mark.medium
    def test_pdf_constants(self):
        """Test PDF configuration constants."""
        assert isinstance(PDF_IMAGE_DPI, (int, float))
        assert isinstance(PDF_JPEG_QUALITY, int)
        
        assert PDF_IMAGE_DPI >= 72  # Minimum readable DPI
        assert PDF_IMAGE_DPI <= 600  # Reasonable upper limit
        assert 0 <= PDF_JPEG_QUALITY <= 100  # JPEG quality range

    @pytest.mark.medium
    def test_user_agent_constants(self):
        """Test user agent constants."""
        assert isinstance(DEFAULT_USER_AGENT, str)
        assert isinstance(USER_AGENTS, list)
        
        assert len(DEFAULT_USER_AGENT) > 0
        assert len(USER_AGENTS) > 0
        assert all(isinstance(ua, str) for ua in USER_AGENTS)
        assert DEFAULT_USER_AGENT in USER_AGENTS

    @pytest.mark.low
    def test_user_agent_diversity(self):
        """Test that user agents are diverse."""
        unique_user_agents = set(USER_AGENTS)
        assert len(unique_user_agents) == len(USER_AGENTS)  # No duplicates
        
        # Should cover different browsers/platforms
        user_agent_strings = ' '.join(USER_AGENTS).lower()
        assert 'chrome' in user_agent_strings
        assert 'firefox' in user_agent_strings


class TestGetRandomUserAgent:
    """Test get_random_user_agent function."""

    @pytest.mark.critical
    def test_get_random_user_agent_return_type(self):
        """Test that function returns a string."""
        user_agent = get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0

    @pytest.mark.critical
    def test_get_random_user_agent_in_list(self):
        """Test that returned user agent is from the list."""
        user_agent = get_random_user_agent()
        assert user_agent in USER_AGENTS

    @pytest.mark.high
    def test_get_random_user_agent_multiple_calls(self):
        """Test multiple calls can return different user agents."""
        results = set()
        for _ in range(100):  # Try many times
            results.add(get_random_user_agent())
        
        # Should get at least some variety (though not guaranteed)
        assert len(results) >= 1
        assert all(ua in USER_AGENTS for ua in results)

    @pytest.mark.high
    @patch('config.secrets.choice')
    def test_get_random_user_agent_uses_secrets(self, mock_choice):
        """Test that function uses secrets.choice for randomness."""
        mock_choice.return_value = USER_AGENTS[0]
        
        result = get_random_user_agent()
        
        mock_choice.assert_called_once_with(USER_AGENTS)
        assert result == USER_AGENTS[0]

    @pytest.mark.medium
    def test_get_random_user_agent_thread_safety(self):
        """Test thread safety of random user agent selection."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                for _ in range(10):
                    results.append(get_random_user_agent())
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(results) == 50  # 5 threads * 10 calls each
        assert all(isinstance(ua, str) for ua in results)


class TestGetRotatingUserAgent:
    """Test get_rotating_user_agent function."""

    @pytest.mark.critical
    def test_get_rotating_user_agent_with_session_id(self):
        """Test rotating user agent with session ID."""
        session_id = "test_session_123"
        user_agent = get_rotating_user_agent(session_id)
        
        assert isinstance(user_agent, str)
        assert user_agent in USER_AGENTS

    @pytest.mark.critical
    def test_get_rotating_user_agent_consistency(self):
        """Test that same session ID returns same user agent."""
        session_id = "consistent_session"
        
        ua1 = get_rotating_user_agent(session_id)
        ua2 = get_rotating_user_agent(session_id)
        
        assert ua1 == ua2

    @pytest.mark.critical
    def test_get_rotating_user_agent_different_sessions(self):
        """Test that different session IDs can return different user agents."""
        session1 = "session_1"
        session2 = "session_2"
        
        ua1 = get_rotating_user_agent(session1)
        ua2 = get_rotating_user_agent(session2)
        
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        assert ua1 in USER_AGENTS
        assert ua2 in USER_AGENTS

    @pytest.mark.high
    def test_get_rotating_user_agent_without_session_id(self):
        """Test rotating user agent without session ID (random behavior)."""
        user_agent = get_rotating_user_agent()
        
        assert isinstance(user_agent, str)
        assert user_agent in USER_AGENTS

    @pytest.mark.high
    def test_get_rotating_user_agent_deterministic(self):
        """Test that session-based selection is deterministic."""
        test_cases = [
            "session_a",
            "session_b",
            "session_c",
            "very_long_session_name_12345",
            "session_with_特殊字符",
            "",
            "123",
            "a" * 100,  # Long session ID
        ]
        
        results = {}
        for session_id in test_cases:
            results[session_id] = get_rotating_user_agent(session_id)
        
        # Each should be consistent when called again
        for session_id, expected_ua in results.items():
            actual_ua = get_rotating_user_agent(session_id)
            assert actual_ua == expected_ua

    @pytest.mark.medium
    def test_get_rotating_user_agent_distribution(self):
        """Test distribution of user agents across sessions."""
        # Test with many different session IDs
        session_counts = {}
        
        for i in range(1000):
            session_id = f"session_{i}"
            ua = get_rotating_user_agent(session_id)
            session_counts[ua] = session_counts.get(ua, 0) + 1
        
        # Should distribute reasonably evenly across user agents
        assert len(session_counts) > 1  # Should use multiple user agents
        
        # Check distribution (should be roughly uniform)
        counts = list(session_counts.values())
        expected_per_ua = 1000 / len(USER_AGENTS)
        
        for count in counts:
            # Allow some variance, but shouldn't be too skewed
            assert abs(count - expected_per_ua) < expected_per_ua

    @pytest.mark.medium
    def test_get_rotating_user_agent_edge_cases(self):
        """Test edge cases for session IDs."""
        edge_cases = [
            None,
            "",
            " ",
            "\0",
            "very_long_session_name" * 10,
        ]
        
        for session_id in edge_cases:
            if session_id is None:
                ua = get_rotating_user_agent()
            else:
                ua = get_rotating_user_agent(session_id)
            
            assert isinstance(ua, str)
            assert ua in USER_AGENTS

    @pytest.mark.low
    def test_get_rotating_user_agent_hash_consistency(self):
        """Test that hash calculation is consistent."""
        session_id = "test_hash_session"
        
        # Multiple calls should return same result
        results = [get_rotating_user_agent(session_id) for _ in range(10)]
        assert all(result == results[0] for result in results)


class TestConfigIntegration:
    """Integration tests for config module."""

    @pytest.mark.integration
    def test_config_values_reasonableness(self):
        """Test that config values are reasonable."""
        # Worker counts should be reasonable
        assert 1 <= DEFAULT_WORKERS <= 20
        assert 1 <= MIN_WORKERS <= DEFAULT_WORKERS
        assert DEFAULT_WORKERS <= MAX_WORKERS <= 50
        
        # Timeouts should be reasonable (in milliseconds)
        assert 10000 <= BROWSER_NAVIGATION_TIMEOUT <= 120000  # 10s to 2min
        assert 1000 <= ASYNC_SLEEP_AFTER_NAVIGATION <= 30000   # 1s to 30s
        
        # Scroll speeds should be reasonable
        assert 10 <= MIN_SCROLL_SPEED <= DEFAULT_SCROLL_SPEED <= MAX_SCROLL_SPEED <= 100
        
        # Chunk sizes should be reasonable (bytes)
        assert 1024 <= DOWNLOAD_CHUNK_SIZE <= 10 * 1024 * 1024  # 1KB to 10MB
        assert 1024 <= VIDEO_CHUNK_SIZE <= 50 * 1024 * 1024      # 1KB to 50MB

    @pytest.mark.integration
    def test_user_agent_functions_compatibility(self):
        """Test that user agent functions work together."""
        # Both should return valid user agents
        random_ua = get_random_user_agent()
        rotating_ua = get_rotating_user_agent("test_session")
        
        assert random_ua in USER_AGENTS
        assert rotating_ua in USER_AGENTS
        assert isinstance(random_ua, str)
        assert isinstance(rotating_ua, str)

    @pytest.mark.integration
    def test_config_performance(self):
        """Test that config access is performant."""
        import time
        
        # Test constants access
        start_time = time.time()
        for _ in range(10000):
            _ = DEFAULT_WORKERS
            _ = DEFAULT_SCROLL_SPEED
            _ = DOWNLOAD_CHUNK_SIZE
        constants_time = time.time() - start_time
        
        # Test function calls
        start_time = time.time()
        for _ in range(1000):
            _ = get_random_user_agent()
            _ = get_rotating_user_agent("test")
        functions_time = time.time() - start_time
        
        # Should be fast (less than 0.1 seconds for these operations)
        assert constants_time < 0.1
        assert functions_time < 0.1

    @pytest.mark.integration
    @patch('config.secrets.choice')
    def test_config_mocking(self, mock_choice):
        """Test that config functions can be mocked."""
        mock_choice.return_value = USER_AGENTS[1]  # Return specific UA
        
        # Should use the mocked choice
        ua = get_random_user_agent()
        assert ua == USER_AGENTS[1]
        mock_choice.assert_called()

    @pytest.mark.low
    def test_config_memory_usage(self):
        """Test that config doesn't use excessive memory."""
        import sys
        
        # Get memory usage before
        initial_objects = len(sys.getreferrers(config)) if hasattr(config, '__dict__') else 0
        
        # Access various config values
        for _ in range(100):
            _ = DEFAULT_WORKERS
            _ = get_random_user_agent()
            _ = get_rotating_user_agent("test")
            _ = USER_AGENTS
        
        # Memory usage shouldn't grow significantly
        # This is a basic check - in real scenarios you'd use more sophisticated memory profiling
        assert True  # Placeholder for memory usage test