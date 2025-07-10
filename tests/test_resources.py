import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import psutil
from monitor.resources import (
    check_disk_usage,
    check_cpu_usage,
    check_memory_usage,
    check_zombie_processes
)


class TestResourceMonitoring:
    """Test suite for resource monitoring functions"""

    def test_check_disk_usage_status(self):
        """Test disk usage monitoring with various scenarios"""
        
        # Test case 1: Normal disk usage (above threshold)
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Mock 20% free space (80% used)
            mock_disk_usage.return_value = mock.Mock(
                total=1000000000000,  # 1TB
                free=200000000000,    # 200GB free
                used=800000000000     # 800GB used
            )
            
            result = check_disk_usage(threshold=10.0)
            
            assert result["ok"] is True
            assert result["percent_free"] == 20.0
            assert result["total_gb"] == 931.32  # 1TB in GB
            assert result["free_gb"] == 186.26   # 200GB
            assert "Low disk space" not in result.get("warning", "")
            assert "Disk free: 20.00%" in result["message"]

        # Test case 2: Low disk usage (below threshold)
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Mock 5% free space (95% used)
            mock_disk_usage.return_value = mock.Mock(
                total=1000000000000,  # 1TB
                free=50000000000,     # 50GB free
                used=950000000000     # 950GB used
            )
            
            result = check_disk_usage(threshold=10.0)
            
            assert result["ok"] is False
            assert result["percent_free"] == 5.0
            assert "warning" in result
            assert "Low disk space: only 5.00% free." in result["warning"]

        # Test case 3: Custom threshold
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Mock 15% free space
            mock_disk_usage.return_value = mock.Mock(
                total=1000000000000,
                free=150000000000,
                used=850000000000
            )
            
            result = check_disk_usage(threshold=20.0)
            
            assert result["ok"] is False
            assert result["percent_free"] == 15.0
            assert "warning" in result

    def test_check_cpu_usage_status(self):
        """Test CPU usage monitoring with various scenarios"""
        
        # Test case 1: Normal CPU usage (below threshold)
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 45.5
            
            result = check_cpu_usage(threshold=85.0)
            
            assert result["ok"] is True
            assert result["cpu_percent"] == 45.5
            assert result["message"] == "CPU usage: 45.50%"
            assert "warning" not in result

        # Test case 2: High CPU usage (above threshold)
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 90.0
            
            result = check_cpu_usage(threshold=85.0)
            
            assert result["ok"] is False
            assert result["cpu_percent"] == 90.0
            assert "warning" in result
            assert "High CPU usage: 90.00%." in result["warning"]

        # Test case 3: CPU usage exactly at threshold
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 85.0
            
            result = check_cpu_usage(threshold=85.0)
            
            assert result["ok"] is False
            assert result["cpu_percent"] == 85.0
            assert "warning" in result

        # Test case 4: Custom threshold
        with patch('psutil.cpu_percent') as mock_cpu_percent:
            mock_cpu_percent.return_value = 75.0
            
            result = check_cpu_usage(threshold=70.0)
            
            assert result["ok"] is False
            assert "High CPU usage: 75.00%." in result["warning"]

    def test_check_memory_usage_status(self):
        """Test memory usage monitoring with various scenarios"""
        
        # Test case 1: Normal memory usage (below threshold)
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = mock.Mock(
                total=16000000000,     # 16GB
                available=8000000000,   # 8GB available
                percent=50.0           # 50% used
            )
            
            result = check_memory_usage(threshold=85.0)
            
            assert result["ok"] is True
            assert result["used_percent"] == 50.0
            assert result["total_gb"] == 14.90  # 16GB in actual GB
            assert result["available_gb"] == 7.45  # 8GB available
            assert result["message"] == "Memory usage: 50.00%"
            assert "warning" not in result

        # Test case 2: High memory usage (above threshold)
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = mock.Mock(
                total=16000000000,
                available=1000000000,  # 1GB available
                percent=90.0           # 90% used
            )
            
            result = check_memory_usage(threshold=85.0)
            
            assert result["ok"] is False
            assert result["used_percent"] == 90.0
            assert "warning" in result
            assert "High memory usage: 90.00%." in result["warning"]

        # Test case 3: Memory usage exactly at threshold
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = mock.Mock(
                total=8000000000,
                available=1200000000,
                percent=85.0
            )
            
            result = check_memory_usage(threshold=85.0)
            
            assert result["ok"] is False
            assert result["used_percent"] == 85.0
            assert "warning" in result

        # Test case 4: Custom threshold
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = mock.Mock(
                total=8000000000,
                available=2000000000,
                percent=75.0
            )
            
            result = check_memory_usage(threshold=70.0)
            
            assert result["ok"] is False
            assert "High memory usage: 75.00%." in result["warning"]

    def test_check_zombie_processes_status(self):
        """Test zombie process detection with various scenarios"""
        
        # Test case 1: No zombie processes
        with patch('psutil.process_iter') as mock_process_iter:
            mock_processes = [
                mock.Mock(info={'pid': 1234, 'name': 'python', 'status': psutil.STATUS_RUNNING}),
                mock.Mock(info={'pid': 5678, 'name': 'nginx', 'status': psutil.STATUS_SLEEPING}),
                mock.Mock(info={'pid': 9012, 'name': 'mysql', 'status': psutil.STATUS_RUNNING})
            ]
            mock_process_iter.return_value = mock_processes
            
            result = check_zombie_processes()
            
            assert result["ok"] is True
            assert result["zombie_count"] == 0
            assert result["message"] == "Zombie processes: 0"
            assert "warning" not in result
            assert "zombies" not in result

        # Test case 2: One zombie process
        with patch('psutil.process_iter') as mock_process_iter:
            mock_processes = [
                mock.Mock(info={'pid': 1234, 'name': 'python', 'status': psutil.STATUS_RUNNING}),
                mock.Mock(info={'pid': 5678, 'name': 'defunct', 'status': psutil.STATUS_ZOMBIE}),
                mock.Mock(info={'pid': 9012, 'name': 'mysql', 'status': psutil.STATUS_RUNNING})
            ]
            mock_process_iter.return_value = mock_processes
            
            result = check_zombie_processes()
            
            assert result["ok"] is False
            assert result["zombie_count"] == 1
            assert result["message"] == "Zombie processes: 1"
            assert "warning" in result
            assert "Detected 1 zombie processes." in result["warning"]
            assert "zombies" in result
            assert len(result["zombies"]) == 1
            assert result["zombies"][0]["pid"] == 5678
            assert result["zombies"][0]["name"] == "defunct"

        # Test case 3: Multiple zombie processes
        with patch('psutil.process_iter') as mock_process_iter:
            mock_processes = [
                mock.Mock(info={'pid': 1111, 'name': 'zombie1', 'status': psutil.STATUS_ZOMBIE}),
                mock.Mock(info={'pid': 2222, 'name': 'zombie2', 'status': psutil.STATUS_ZOMBIE}),
                mock.Mock(info={'pid': 3333, 'name': 'normal', 'status': psutil.STATUS_RUNNING})
            ]
            mock_process_iter.return_value = mock_processes
            
            result = check_zombie_processes()
            
            assert result["ok"] is False
            assert result["zombie_count"] == 2
            assert result["message"] == "Zombie processes: 2"
            assert "Detected 2 zombie processes." in result["warning"]
            assert len(result["zombies"]) == 2

        # Test case 4: Handle psutil exceptions
        with patch('psutil.process_iter') as mock_process_iter:
            mock_process_good = mock.Mock(info={'pid': 1234, 'name': 'python', 'status': psutil.STATUS_RUNNING})
            mock_process_exception = mock.Mock()
            mock_process_exception.info = {'pid': 5678, 'name': 'test', 'status': psutil.STATUS_ZOMBIE}
            
            # Configure the mock to raise an exception when accessed
            def side_effect(*args, **kwargs):
                if mock_process_exception in args:
                    raise psutil.NoSuchProcess(5678)
                return mock_process_good.info
            
            mock_processes = [mock_process_good]
            mock_process_iter.return_value = mock_processes
            
            result = check_zombie_processes()
            
            assert result["ok"] is True
            assert result["zombie_count"] == 0


# Additional test fixtures and helpers
@pytest.fixture
def mock_disk_usage():
    """Fixture for mocking disk usage"""
    with patch('shutil.disk_usage') as mock:
        yield mock


@pytest.fixture
def mock_cpu_percent():
    """Fixture for mocking CPU percentage"""
    with patch('psutil.cpu_percent') as mock:
        yield mock


@pytest.fixture
def mock_memory():
    """Fixture for mocking virtual memory"""
    with patch('psutil.virtual_memory') as mock:
        yield mock


@pytest.fixture
def mock_processes():
    """Fixture for mocking process iterator"""
    with patch('psutil.process_iter') as mock:
        yield mock


# Integration-style tests
class TestResourceMonitoringIntegration:
    """Integration tests that combine multiple resource checks"""
    
    def test_all_resources_healthy(self, mock_disk_usage, mock_cpu_percent, mock_memory, mock_processes):
        """Test scenario where all resources are healthy"""
        # Setup mocks for healthy system
        mock_disk_usage.return_value = mock.Mock(total=1000000000000, free=500000000000, used=500000000000)
        mock_cpu_percent.return_value = 25.0
        mock_memory.return_value = mock.Mock(total=16000000000, available=8000000000, percent=50.0)
        mock_processes.return_value = [
            mock.Mock(info={'pid': 1234, 'name': 'python', 'status': psutil.STATUS_RUNNING})
        ]
        
        disk_result = check_disk_usage()
        cpu_result = check_cpu_usage()
        memory_result = check_memory_usage()
        zombie_result = check_zombie_processes()
        
        assert all([disk_result["ok"], cpu_result["ok"], memory_result["ok"], zombie_result["ok"]])
    
    def test_all_resources_unhealthy(self, mock_disk_usage, mock_cpu_percent, mock_memory, mock_processes):
        """Test scenario where all resources are unhealthy"""
        # Setup mocks for unhealthy system
        mock_disk_usage.return_value = mock.Mock(total=1000000000000, free=50000000000, used=950000000000)
        mock_cpu_percent.return_value = 95.0
        mock_memory.return_value = mock.Mock(total=16000000000, available=1000000000, percent=95.0)
        mock_processes.return_value = [
            mock.Mock(info={'pid': 1234, 'name': 'zombie', 'status': psutil.STATUS_ZOMBIE})
        ]
        
        disk_result = check_disk_usage()
        cpu_result = check_cpu_usage()
        memory_result = check_memory_usage()
        zombie_result = check_zombie_processes()
        
        assert not any([disk_result["ok"], cpu_result["ok"], memory_result["ok"], zombie_result["ok"]])


if __name__ == "__main__":
    pytest.main([__file__])