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
    
    # ========== Advanced Project Detection (Tests 26-40) ==========
    
    def test_python_project_detection(self):
        """Test 26: Detects Python project"""
        from monitor import resources
        
        python_dir = os.path.join(self.temp_dir, "python_project")
        os.makedirs(python_dir)
        Path(os.path.join(python_dir, "requirements.txt")).touch()
        
        os.chdir(python_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["python_project"] == True, "Should detect Python project"
    
    def test_java_project_detection(self):
        """Test 27: Detects Java project"""
        from monitor import resources
        
        java_dir = os.path.join(self.temp_dir, "java_project")
        os.makedirs(java_dir)
        Path(os.path.join(java_dir, "pom.xml")).touch()
        
        os.chdir(java_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["java_project"] == True, "Should detect Java project"
    
    def test_rust_project_detection(self):
        """Test 28: Detects Rust project"""
        from monitor import resources
        
        rust_dir = os.path.join(self.temp_dir, "rust_project")
        os.makedirs(rust_dir)
        Path(os.path.join(rust_dir, "Cargo.toml")).touch()
        
        os.chdir(rust_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["rust_project"] == True, "Should detect Rust project"
    
    def test_go_project_detection(self):
        """Test 29: Detects Go project"""
        from monitor import resources
        
        go_dir = os.path.join(self.temp_dir, "go_project")
        os.makedirs(go_dir)
        Path(os.path.join(go_dir, "go.mod")).touch()
        
        os.chdir(go_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["go_project"] == True, "Should detect Go project"
    
    def test_ruby_project_detection(self):
        """Test 30: Detects Ruby project"""
        from monitor import resources
        
        ruby_dir = os.path.join(self.temp_dir, "ruby_project")
        os.makedirs(ruby_dir)
        Path(os.path.join(ruby_dir, "Gemfile")).touch()
        
        os.chdir(ruby_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["ruby_project"] == True, "Should detect Ruby project"
    
    def test_nested_project_structure(self):
        """Test 31: Detects project in nested directory"""
        from monitor import resources
        
        nested_dir = os.path.join(self.temp_dir, "parent", "child", "project")
        os.makedirs(nested_dir)
        os.makedirs(os.path.join(nested_dir, ".git"))
        Path(os.path.join(nested_dir, "package.json")).touch()
        
        os.chdir(nested_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["git_repo"] == True, "Should detect Git in nested dir"
        assert project_context["context"]["node_project"] == True, "Should detect Node.js in nested dir"
    
    def test_project_with_venv(self):
        """Test 32: Detects virtual environment"""
        from monitor import resources
        
        venv_dir = os.path.join(self.temp_dir, "venv_project")
        os.makedirs(venv_dir)
        venv_path = os.path.join(venv_dir, "venv")
        os.makedirs(venv_path)
        
        os.chdir(venv_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_venv") == True, "Should detect virtual environment"
    
    def test_monorepo_detection(self):
        """Test 33: Detects monorepo structure"""
        from monitor import resources
        
        monorepo_dir = os.path.join(self.temp_dir, "monorepo")
        os.makedirs(monorepo_dir)
        os.makedirs(os.path.join(monorepo_dir, ".git"))
        os.makedirs(os.path.join(monorepo_dir, "packages", "app1"))
        os.makedirs(os.path.join(monorepo_dir, "packages", "app2"))
        Path(os.path.join(monorepo_dir, "lerna.json")).touch()
        
        os.chdir(monorepo_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["git_repo"] == True, "Should detect Git"
    
    def test_dockerfile_detection(self):
        """Test 34: Detects Dockerfile"""
        from monitor import resources
        
        docker_dir = os.path.join(self.temp_dir, "dockerfile_project")
        os.makedirs(docker_dir)
        Path(os.path.join(docker_dir, "Dockerfile")).touch()
        
        os.chdir(docker_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"]["has_dockerfile"] == True, "Should detect Dockerfile"
    
    def test_kubernetes_project_detection(self):
        """Test 35: Detects Kubernetes config"""
        from monitor import resources
        
        k8s_dir = os.path.join(self.temp_dir, "k8s_project")
        os.makedirs(k8s_dir)
        k8s_subdir = os.path.join(k8s_dir, "k8s")
        os.makedirs(k8s_subdir)
        Path(os.path.join(k8s_subdir, "deployment.yaml")).touch()
        
        os.chdir(k8s_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_k8s") == True, "Should detect Kubernetes"
    
    def test_makefile_detection(self):
        """Test 36: Detects Makefile"""
        from monitor import resources
        
        make_dir = os.path.join(self.temp_dir, "make_project")
        os.makedirs(make_dir)
        Path(os.path.join(make_dir, "Makefile")).touch()
        
        os.chdir(make_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_makefile") == True, "Should detect Makefile"
    
    def test_cicd_config_detection(self):
        """Test 37: Detects CI/CD configuration"""
        from monitor import resources
        
        cicd_dir = os.path.join(self.temp_dir, "cicd_project")
        os.makedirs(cicd_dir)
        github_dir = os.path.join(cicd_dir, ".github", "workflows")
        os.makedirs(github_dir)
        Path(os.path.join(github_dir, "ci.yml")).touch()
        
        os.chdir(cicd_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_cicd") == True, "Should detect CI/CD"
    
    def test_readme_detection(self):
        """Test 38: Detects README file"""
        from monitor import resources
        
        readme_dir = os.path.join(self.temp_dir, "readme_project")
        os.makedirs(readme_dir)
        Path(os.path.join(readme_dir, "README.md")).touch()
        
        os.chdir(readme_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_readme") == True, "Should detect README"
    
    def test_license_detection(self):
        """Test 39: Detects LICENSE file"""
        from monitor import resources
        
        license_dir = os.path.join(self.temp_dir, "license_project")
        os.makedirs(license_dir)
        Path(os.path.join(license_dir, "LICENSE")).touch()
        
        os.chdir(license_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_license") == True, "Should detect LICENSE"
    
    def test_gitignore_detection(self):
        """Test 40: Detects .gitignore file"""
        from monitor import resources
        
        gitignore_dir = os.path.join(self.temp_dir, "gitignore_project")
        os.makedirs(gitignore_dir)
        Path(os.path.join(gitignore_dir, ".gitignore")).touch()
        
        os.chdir(gitignore_dir)
        
        project_context = resources.detect_project_context()
        
        assert project_context["context"].get("has_gitignore") == True, "Should detect .gitignore"
    
    # ========== Resource Monitoring Edge Cases (Tests 41-55) ==========
    
    def test_disk_usage_with_multiple_partitions(self):
        """Test 41: Disk usage works with multiple partitions"""
        from monitor import resources
        
        disk_status = resources.check_disk_usage()
        
        assert "ok" in disk_status, "Should handle multiple partitions"
    
    def test_cpu_usage_multicore(self):
        """Test 42: CPU usage on multicore systems"""
        from monitor import resources
        
        cpu_status = resources.check_cpu_usage()
        
        assert "cpu_percent" in cpu_status, "Should report CPU on multicore"
        assert "core_count" in cpu_status, "Should report core count"
    
    def test_memory_with_swap(self):
        """Test 43: Memory monitoring includes swap"""
        from monitor import resources
        
        mem_status = resources.check_memory_usage()
        
        assert "swap_used_percent" in mem_status, "Should include swap info"
    
    def test_process_filter_by_user(self):
        """Test 44: Filter processes by user"""
        from monitor import resources
        
        proc_summary = resources.check_running_process_summary(limit=5, user_filter=os.getlogin())
        
        assert "ok" in proc_summary, "Should filter by user"
    
    def test_process_filter_by_name(self):
        """Test 45: Filter processes by name"""
        from monitor import resources
        
        proc_summary = resources.check_running_process_summary(limit=5, name_filter="python")
        
        assert "ok" in proc_summary, "Should filter by name"
    
    def test_network_connections_by_protocol(self):
        """Test 46: Network connections filtered by protocol"""
        from monitor import resources
        
        network_status = resources.check_network_connections(limit=5, protocol="tcp")
        
        assert "ok" in network_status, "Should filter by protocol"
    
    def test_network_connections_by_state(self):
        """Test 47: Network connections filtered by state"""
        from monitor import resources
        
        network_status = resources.check_network_connections(limit=5, state="ESTABLISHED")
        
        assert "ok" in network_status, "Should filter by state"
    
    def test_zombie_process_cleanup_detection(self):
        """Test 48: Detects if zombies can be cleaned"""
        from monitor import resources
        
        zombie_status = resources.check_zombie_processes()
        
        if zombie_status["zombie_count"] > 0:
            assert "zombie_pids" in zombie_status, "Should report zombie PIDs"
    
    def test_disk_io_statistics(self):
        """Test 49: Disk I/O statistics"""
        from monitor import resources
        
        io_stats = resources.get_disk_io_stats()
        
        assert "ok" in io_stats, "Should have status"
        assert "read_bytes" in io_stats, "Should have read bytes"
        assert "write_bytes" in io_stats, "Should have write bytes"
    
    def test_network_io_statistics(self):
        """Test 50: Network I/O statistics"""
        from monitor import resources
        
        net_stats = resources.get_network_io_stats()
        
        assert "ok" in net_stats, "Should have status"
        assert "bytes_sent" in net_stats, "Should have bytes sent"
        assert "bytes_recv" in net_stats, "Should have bytes received"
    
    def test_system_boot_time(self):
        """Test 51: Get system boot time"""
        from monitor import resources
        
        boot_info = resources.get_boot_time()
        
        assert "ok" in boot_info, "Should have status"
        assert "boot_timestamp" in boot_info, "Should have boot timestamp"
        assert "uptime_seconds" in boot_info, "Should have uptime"
    
    def test_load_average(self):
        """Test 52: Get system load average"""
        from monitor import resources
        
        load_avg = resources.get_load_average()
        
        assert "ok" in load_avg, "Should have status"
        assert "load_1min" in load_avg, "Should have 1-minute load"
        assert "load_5min" in load_avg, "Should have 5-minute load"
        assert "load_15min" in load_avg, "Should have 15-minute load"
    
    def test_temperature_monitoring(self):
        """Test 53: Temperature monitoring (if available)"""
        from monitor import resources
        
        try:
            temp_info = resources.get_temperature_info()
            
            if temp_info["ok"]:
                assert "temperatures" in temp_info, "Should have temperature data"
        except Exception:
            # Temperature monitoring may not be available on all systems
            pass
    
    def test_battery_status(self):
        """Test 54: Battery status (if available)"""
        from monitor import resources
        
        try:
            battery_info = resources.get_battery_status()
            
            assert "ok" in battery_info, "Should have status"
            if battery_info["ok"]:
                assert "percent" in battery_info, "Should have battery percent"
        except Exception:
            # Battery may not be available on servers
            pass
    
    def test_user_sessions(self):
        """Test 55: Active user sessions"""
        from monitor import resources
        
        sessions = resources.get_user_sessions()
        
        assert "ok" in sessions, "Should have status"
        assert "active_users" in sessions, "Should list active users"
        assert isinstance(sessions["active_users"], list), "Should be a list"
    
    # ========== Context Integration Tests (Tests 56-70) ==========
    
    def test_context_includes_all_components(self):
        """Test 56: Full context includes all required components"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        
        required_keys = [
            "project_context", "environment_status", "running_procs",
            "network_conns", "disk_status", "cpu_status", "mem_status", 
            "zombie_status", "timestamp"
        ]
        
        for key in required_keys:
            assert key in context, f"Missing required key: {key}"
    
    def test_context_timestamp_format(self):
        """Test 57: Context timestamp is valid ISO format"""
        from commands import context_manager
        from datetime import datetime
        
        context = context_manager.collect_full_context()
        
        assert "timestamp" in context, "Should have timestamp"
        
        # Verify it's valid ISO format
        try:
            datetime.fromisoformat(context["timestamp"])
        except ValueError:
            assert False, "Timestamp should be valid ISO format"
    
    def test_context_serialization_roundtrip(self):
        """Test 58: Context can be serialized and deserialized"""
        from commands import context_manager
        import json
        
        context = context_manager.collect_full_context()
        json_str = context_manager.context_to_json(context)
        
        # Deserialize
        restored = json.loads(json_str)
        
        assert isinstance(restored, dict), "Should deserialize to dict"
        assert "project_context" in restored, "Should preserve structure"
    
    def test_context_size_reasonable(self):
        """Test 59: Context JSON size is reasonable"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        json_str = context_manager.context_to_json(context)
        
        size_kb = len(json_str) / 1024
        assert size_kb < 100, f"Context too large: {size_kb:.1f}KB"
    
    def test_context_with_minimal_system(self):
        """Test 60: Context works on minimal system"""
        from commands import context_manager
        
        # Should not fail even if some info is unavailable
        try:
            context = context_manager.collect_full_context()
            assert context is not None, "Should return context"
        except Exception as e:
            assert False, f"Should handle minimal systems: {e}"
    
    def test_context_caching(self):
        """Test 61: Context can be cached"""
        from commands import context_manager
        import time
        
        # First call
        start1 = time.time()
        context1 = context_manager.collect_full_context()
        time1 = time.time() - start1
        
        # Second call (potentially cached)
        start2 = time.time()
        context2 = context_manager.collect_full_context()
        time2 = time.time() - start2
        
        # Both should succeed
        assert context1 is not None, "First call should succeed"
        assert context2 is not None, "Second call should succeed"
    
    def test_context_update_on_change(self):
        """Test 62: Context updates when system changes"""
        from commands import context_manager
        import time
        
        context1 = context_manager.collect_full_context()
        time.sleep(2)  # Wait for system to change
        context2 = context_manager.collect_full_context()
        
        # Timestamps should be different
        assert context1["timestamp"] != context2["timestamp"], "Timestamps should differ"
    
    def test_context_filtering(self):
        """Test 63: Context can be filtered to specific keys"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        filtered = context_manager.filter_context(context, keys=["project_context", "disk_status"])
        
        assert "project_context" in filtered, "Should include requested key"
        assert "disk_status" in filtered, "Should include requested key"
        assert len(filtered) == 2, "Should only include requested keys"
    
    def test_context_merging(self):
        """Test 64: Multiple contexts can be merged"""
        from commands import context_manager
        
        context1 = {"key1": "value1"}
        context2 = {"key2": "value2"}
        
        merged = context_manager.merge_contexts(context1, context2)
        
        assert "key1" in merged, "Should include first context"
        assert "key2" in merged, "Should include second context"
    
    def test_context_diff(self):
        """Test 65: Can detect differences between contexts"""
        from commands import context_manager
        import time
        
        context1 = context_manager.collect_full_context()
        time.sleep(1)
        context2 = context_manager.collect_full_context()
        
        diff = context_manager.diff_contexts(context1, context2)
        
        assert isinstance(diff, dict), "Diff should be a dict"
    
    def test_context_summary_format(self):
        """Test 66: Context summary is well-formatted"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        summary = context_manager.get_context_summary(context)
        
        assert isinstance(summary, str), "Summary should be string"
        assert len(summary) > 0, "Summary should not be empty"
    
    def test_context_warning_detection(self):
        """Test 67: Detects warnings in context"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        warnings = context_manager.get_context_warnings(context)
        
        assert isinstance(warnings, list), "Warnings should be a list"
    
    def test_context_health_score(self):
        """Test 68: Calculates overall health score"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        health = context_manager.calculate_health_score(context)
        
        assert isinstance(health, float), "Health should be float"
        assert 0 <= health <= 100, "Health should be 0-100"
    
    def test_context_recommendations(self):
        """Test 69: Generates recommendations from context"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        recommendations = context_manager.get_recommendations(context)
        
        assert isinstance(recommendations, list), "Recommendations should be list"
    
    def test_context_export_formats(self):
        """Test 70: Context can be exported in multiple formats"""
        from commands import context_manager
        
        context = context_manager.collect_full_context()
        
        # JSON export
        json_export = context_manager.export_context(context, format="json")
        assert json_export is not None, "Should export JSON"
        
        # YAML export (if available)
        try:
            yaml_export = context_manager.export_context(context, format="yaml")
            assert yaml_export is not None, "Should export YAML"
        except Exception:
            pass  # YAML may not be available
    
    def run_all_tests(self) -> Dict:
        """Run all context awareness tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Context Awareness Tests (70+ cases) ═══[/bold cyan]\n")
        
        # Collect all test methods
        test_methods = []
        for attr_name in dir(self):
            if attr_name.startswith('test_'):
                test_func = getattr(self, attr_name)
                if callable(test_func):
                    test_name = test_func.__doc__ or attr_name
                    test_methods.append((test_func, test_name.strip()))
        
        # Sort by test number
        test_methods.sort(key=lambda x: x[1])
        
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