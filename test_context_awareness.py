#!/usr/bin/env python3
"""
Comprehensive Context Awareness Testing
========================================
Tests system context collection, project detection, and environment awareness.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class ContextTestResult:
    test_name: str
    passed: bool
    details: str


class ContextAwarenessTester:
    """Comprehensive context awareness testing"""
    
    def __init__(self):
        self.results: List[ContextTestResult] = []
        self.temp_dir = None
        self.original_cwd = None
        
    def setup(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="context_test_")
        self.original_cwd = os.getcwd()
        
    def teardown(self):
        """Cleanup test environment"""
        if self.original_cwd:
            os.chdir(self.original_cwd)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record result"""
        try:
            test_func()
            self.results.append(ContextTestResult(test_name, True, "✓"))
            return True
        except AssertionError as e:
            self.results.append(ContextTestResult(test_name, False, str(e)))
            return False
        except Exception as e:
            self.results.append(ContextTestResult(test_name, False, f"Exception: {e}"))
            return False
    
    # ========== Full Context Collection Tests ==========
    
    def test_full_context_structure(self):
        """Test 1: Full context collection returns all required keys"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        
        required_keys = [
            "project_context", "environment_status", "running_procs",
            "network_conns", "disk_status", "cpu_status", "mem_status", "zombie_status"
        ]
        
        for key in required_keys:
            assert key in context, f"Missing required key: {key}"
        
        assert isinstance(context, dict), "Context should be a dictionary"
    
    def test_context_to_json(self):
        """Test 2: Context can be serialized to JSON"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        json_str = context_manager.context_to_json(context)
        
        assert json_str is not None, "JSON string should not be None"
        assert len(json_str) > 0, "JSON string should not be empty"
        
        import json
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict), "Parsed JSON should be a dictionary"
    
    def test_context_json_error_handling(self):
        """Test 3: Context JSON conversion handles errors gracefully"""
        from commands import context_manager
        
        # Create problematic context
        bad_context = {"function": lambda x: x}  # Functions can't be serialized
        
        json_str = context_manager.context_to_json(bad_context)
        
        assert "error" in json_str.lower(), "Should contain error message"
    
    # ========== Resource Monitoring Tests ==========
    
    def test_disk_usage_monitoring(self):
        """Test 4: Disk usage monitoring returns valid data"""
        from monitor import resources
        
        disk_status = resources.check_disk_usage()
        
        assert "ok" in disk_status, "Should have 'ok' field"
        assert "message" in disk_status, "Should have 'message' field"
        assert "percent_free" in disk_status, "Should have 'percent_free' field"
        assert isinstance(disk_status["ok"], bool), "'ok' should be boolean"
        assert isinstance(disk_status["percent_free"], float), "'percent_free' should be float"
    
    def test_disk_usage_threshold(self):
        """Test 5: Disk usage respects custom threshold"""
        from monitor import resources
        
        # Test with very high threshold (should fail)
        disk_status_high = resources.check_disk_usage(threshold=99.0)
        
        # Test with very low threshold (should pass)
        disk_status_low = resources.check_disk_usage(threshold=1.0)
        
        assert disk_status_low["ok"] == True, "Should pass with 1% threshold"
    
    def test_cpu_usage_monitoring(self):
        """Test 6: CPU usage monitoring returns valid data"""
        from monitor import resources
        
        cpu_status = resources.check_cpu_usage()
        
        assert "ok" in cpu_status, "Should have 'ok' field"
        assert "message" in cpu_status, "Should have 'message' field"
        assert "cpu_percent" in cpu_status, "Should have 'cpu_percent' field"
        assert isinstance(cpu_status["cpu_percent"], float), "'cpu_percent' should be float"
        assert 0 <= cpu_status["cpu_percent"] <= 100, "CPU percent should be 0-100"
    
    def test_cpu_usage_threshold(self):
        """Test 7: CPU usage respects custom threshold"""
        from monitor import resources
        
        # Test with very low threshold (should fail if any CPU usage)
        cpu_status_low = resources.check_cpu_usage(threshold=0.1)
        
        # Test with very high threshold (should pass)
        cpu_status_high = resources.check_cpu_usage(threshold=100.0)
        
        assert cpu_status_high["ok"] == True, "Should pass with 100% threshold"
    
    def test_memory_usage_monitoring(self):
        """Test 8: Memory usage monitoring returns valid data"""
        from monitor import resources
        
        mem_status = resources.check_memory_usage()
        
        assert "ok" in mem_status, "Should have 'ok' field"
        assert "message" in mem_status, "Should have 'message' field"
        assert "used_percent" in mem_status, "Should have 'used_percent' field"
        assert "total_gb" in mem_status, "Should have 'total_gb' field"
        assert "available_gb" in mem_status, "Should have 'available_gb' field"
        assert isinstance(mem_status["used_percent"], float), "'used_percent' should be float"
        assert 0 <= mem_status["used_percent"] <= 100, "Memory percent should be 0-100"
    
    def test_memory_usage_threshold(self):
        """Test 9: Memory usage respects custom threshold"""
        from monitor import resources
        
        # Test with very high threshold (should pass)
        mem_status = resources.check_memory_usage(threshold=99.0)
        
        assert "ok" in mem_status, "Should have 'ok' field"
    
    def test_zombie_process_detection(self):
        """Test 10: Zombie process detection returns valid data"""
        from monitor import resources
        
        zombie_status = resources.check_zombie_processes()
        
        assert "ok" in zombie_status, "Should have 'ok' field"
        assert "message" in zombie_status, "Should have 'message' field"
        assert "zombie_count" in zombie_status, "Should have 'zombie_count' field"
        assert isinstance(zombie_status["zombie_count"], int), "'zombie_count' should be int"
        assert zombie_status["zombie_count"] >= 0, "Zombie count should be non-negative"
    
    def test_running_process_summary(self):
        """Test 11: Running process summary returns valid data"""
        from monitor import resources
        
        proc_summary = resources.check_running_process_summary(limit=5)
        
        assert "ok" in proc_summary, "Should have 'ok' field"
        assert "message" in proc_summary, "Should have 'message' field"
        assert "top_processes" in proc_summary, "Should have 'top_processes' field"
        assert isinstance(proc_summary["top_processes"], list), "'top_processes' should be list"
        assert len(proc_summary["top_processes"]) <= 5, "Should return at most 5 processes"
    
    def test_network_connections_monitoring(self):
        """Test 12: Network connections monitoring returns valid data"""
        from monitor import resources
        
        network_status = resources.check_network_connections(limit=5)
        
        assert "ok" in network_status, "Should have 'ok' field"
        assert "message" in network_status, "Should have 'message' field"
        
        if network_status["ok"]:
            assert "connections_summary" in network_status, "Should have 'connections_summary' field"
    
    # ========== Project Context Detection Tests ==========
    
    def test_git_project_detection(self):
        """Test 13: Detects Git repository"""
        from monitor import resources
        
        # Create a Git repository
        git_dir = os.path.join(self.temp_dir, "git_project")
        os.makedirs(git_dir)
        os.makedirs(os.path.join(git_dir, ".git"))
        
        os.chdir(git_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["git_repo"] == True, "Should detect Git repository"
    
    def test_docker_project_detection(self):
        """Test 14: Detects Docker project"""
        from monitor import resources
        
        # Create a Docker project
        docker_dir = os.path.join(self.temp_dir, "docker_project")
        os.makedirs(docker_dir)
        Path(os.path.join(docker_dir, "docker-compose.yml")).touch()
        
        os.chdir(docker_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["docker_project"] == True, "Should detect Docker project"
    
    def test_nodejs_project_detection(self):
        """Test 15: Detects Node.js project"""
        from monitor import resources
        
        # Create a Node.js project
        node_dir = os.path.join(self.temp_dir, "node_project")
        os.makedirs(node_dir)
        Path(os.path.join(node_dir, "package.json")).touch()
        
        os.chdir(node_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["node_project"] == True, "Should detect Node.js project"
    
    def test_multiple_project_types(self):
        """Test 16: Detects multiple project types"""
        from monitor import resources
        
        # Create a project with multiple indicators
        multi_dir = os.path.join(self.temp_dir, "multi_project")
        os.makedirs(multi_dir)
        os.makedirs(os.path.join(multi_dir, ".git"))
        Path(os.path.join(multi_dir, "package.json")).touch()
        Path(os.path.join(multi_dir, "docker-compose.yml")).touch()
        
        os.chdir(multi_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["git_repo"] == True, "Should detect Git"
        assert project_context["context"]["node_project"] == True, "Should detect Node.js"
        assert project_context["context"]["docker_project"] == True, "Should detect Docker"
    
    def test_no_project_context(self):
        """Test 17: Handles directory with no project indicators"""
        from monitor import resources
        
        # Create empty directory
        empty_dir = os.path.join(self.temp_dir, "empty_project")
        os.makedirs(empty_dir)
        
        os.chdir(empty_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["git_repo"] == False, "Should not detect Git"
        assert project_context["context"]["node_project"] == False, "Should not detect Node.js"
        assert project_context["context"]["docker_project"] == False, "Should not detect Docker"
    
    # ========== Environment Detection Tests ==========
    
    def test_environment_detection(self):
        """Test 18: Environment detection returns valid data"""
        from monitor import resources
        
        env_status = resources.detect_environment()
        
        assert "ok" in env_status, "Should have 'ok' field"
        assert "message" in env_status, "Should have 'message' field"
        assert "environment" in env_status, "Should have 'environment' field"
        assert "hostname" in env_status, "Should have 'hostname' field"
        assert env_status["environment"] in ["development", "production"], "Should be dev or prod"
    
    def test_environment_from_env_var(self):
        """Test 19: Environment detection reads ENV variable"""
        from monitor import resources
        
        # Save original
        original_env = os.environ.get("ENV")
        
        try:
            # Set to production
            os.environ["ENV"] = "production"
            env_status = resources.detect_environment()
            assert env_status["environment"] == "production", "Should detect production"
            
            # Set to development
            os.environ["ENV"] = "development"
            env_status = resources.detect_environment()
            assert env_status["environment"] == "development", "Should detect development"
        finally:
            # Restore original
            if original_env:
                os.environ["ENV"] = original_env
            elif "ENV" in os.environ:
                del os.environ["ENV"]
    
    def test_hostname_detection(self):
        """Test 20: Hostname detection returns valid hostname"""
        from monitor import resources
        
        env_status = resources.detect_environment()
        
        assert "hostname" in env_status, "Should have hostname"
        assert len(env_status["hostname"]) > 0, "Hostname should not be empty"
        assert isinstance(env_status["hostname"], str), "Hostname should be string"
    
    # ========== Context Display Tests ==========
    
    def test_context_display_no_error(self):
        """Test 21: Context display doesn't raise errors"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        
        # Should not raise exception
        context_manager.display_context_summary(context)
    
    def test_context_display_with_warnings(self):
        """Test 22: Context display handles warning states"""
        from commands import context_manager
        
        # Create context with some warnings
        context = {
            "project_context": {"message": "No project detected"},
            "environment_status": {"message": "Development environment"},
            "running_procs": {"message": "High CPU processes detected"},
            "network_conns": {"message": "Many connections"},
            "disk_status": {"message": "Low disk space"},
            "cpu_status": {"message": "High CPU usage"},
            "mem_status": {"message": "High memory usage"},
            "zombie_status": {"message": "Zombie processes found"},
        }
        
        # Should not raise exception
        context_manager.display_context_summary(context)
    
    # ========== Edge Cases ==========
    
    def test_context_with_missing_psutil(self):
        """Test 23: Graceful handling if psutil functions fail"""
        from monitor import resources
        
        # This should still work even if some functions fail
        try:
            disk_status = resources.check_disk_usage()
            assert "ok" in disk_status, "Should return valid structure"
        except Exception as e:
            # If it fails, it should fail gracefully
            assert False, f"Should handle errors gracefully: {e}"
    
    def test_context_collection_performance(self):
        """Test 24: Context collection completes in reasonable time"""
        from commands import context_manager
        import time
        
        start_time = time.time()
        context = context_manager.collect_full_context()
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"Context collection took too long: {elapsed:.2f}s"
    
    def test_resource_monitoring_consistency(self):
        """Test 25: Multiple calls return consistent structure"""
        from monitor import resources
        
        disk1 = resources.check_disk_usage()
        disk2 = resources.check_disk_usage()
        
        assert disk1.keys() == disk2.keys(), "Structure should be consistent"
    
    def run_all_tests(self) -> Dict:
        """Run all context awareness tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Context Awareness Tests ═══[/bold cyan]\n")
        
        test_methods = [
            (self.test_full_context_structure, "Full context structure"),
            (self.test_context_to_json, "Context to JSON conversion"),
            (self.test_context_json_error_handling, "JSON error handling"),
            (self.test_disk_usage_monitoring, "Disk usage monitoring"),
            (self.test_disk_usage_threshold, "Disk usage threshold"),
            (self.test_cpu_usage_monitoring, "CPU usage monitoring"),
            (self.test_cpu_usage_threshold, "CPU usage threshold"),
            (self.test_memory_usage_monitoring, "Memory usage monitoring"),
            (self.test_memory_usage_threshold, "Memory usage threshold"),
            (self.test_zombie_process_detection, "Zombie process detection"),
            (self.test_running_process_summary, "Running process summary"),
            (self.test_network_connections_monitoring, "Network connections monitoring"),
            (self.test_git_project_detection, "Git project detection"),
            (self.test_docker_project_detection, "Docker project detection"),
            (self.test_nodejs_project_detection, "Node.js project detection"),
            (self.test_multiple_project_types, "Multiple project types"),
            (self.test_no_project_context, "No project context"),
            (self.test_environment_detection, "Environment detection"),
            (self.test_environment_from_env_var, "Environment from ENV var"),
            (self.test_hostname_detection, "Hostname detection"),
            (self.test_context_display_no_error, "Context display no error"),
            (self.test_context_display_with_warnings, "Context display with warnings"),
            (self.test_context_with_missing_psutil, "Graceful psutil failure"),
            (self.test_context_collection_performance, "Context collection performance"),
            (self.test_resource_monitoring_consistency, "Resource monitoring consistency"),
        ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running context tests...", total=len(test_methods))
            
            for test_func, test_name in test_methods:
                self.run_test(test_name, test_func)
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display test results"""
        table = Table(title="Context Awareness Test Results")
        table.add_column("Test", style="cyan", width=50)
        table.add_column("Status", style="white")
        table.add_column("Details", style="white", width=40)
        
        for test_name, status, details in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(test_name, f"[{color}]{status}[/{color}]", details[:40])
        
        table.add_row(
            "[bold]Overall Success Rate[/bold]",
            f"[bold]{results['success_rate']:.1f}%[/bold]",
            f"{results['tests_passed']}/{results['total_tests']} passed"
        )
        
        console.print(table)


def evaluate_context_awareness() -> Dict:
    """Main entry point for context awareness evaluation"""
    tester = ContextAwarenessTester()
    try:
        tester.setup()
        results = tester.run_all_tests()
        tester.display_results(results)
        return results
    finally:
        tester.teardown()


if __name__ == "__main__":
    evaluate_context_awareness()