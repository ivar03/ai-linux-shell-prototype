import pytest
from commands.auto_tagger import auto_tag, SAFE_COMMANDS, CLEANUP_KEYWORDS, MONITORING_KEYWORDS, NETWORK_KEYWORDS, INSTALL_KEYWORDS, BACKUP_KEYWORDS, READ_ONLY_COMMANDS


class TestAutoTagger:
    """Test suite for auto_tagger module."""
    
    def test_auto_tag_basic_commands(self):
        """Test auto-tagging of basic/safe commands."""
        # Test safe commands
        safe_command_tests = [
            ("ls -la", "list files", ["safe"]),
            ("cat file.txt", "show file content", ["safe"]),
            ("pwd", "show current directory", ["safe"]),
            ("whoami", "show current user", ["safe"]),
            ("date", "show current date", ["safe"]),
            ("echo hello", "print hello", ["safe"]),
            ("ps aux", "show processes", ["safe"]),
            ("df -h", "show disk usage", ["safe"]),
            ("free -m", "show memory usage", ["safe"]),
            ("uptime", "show system uptime", ["safe"])
        ]
        
        for command, query, expected_tags in safe_command_tests:
            tags = auto_tag(query, command)
            assert "safe" in tags, f"Command '{command}' should be tagged as 'safe'"
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}'"
        
        # Test read-only commands
        read_only_tests = [
            ("find . -name '*.txt'", "find text files", ["safe"]),
            ("grep 'pattern' file.txt", "search for pattern", ["safe"]),
            ("less file.txt", "view file", ["safe"]),
            ("head -n 10 file.txt", "show first 10 lines", ["safe"]),
            ("tail -f logfile.txt", "follow log file", ["safe"]),
            ("wc -l file.txt", "count lines", ["safe"]),
            ("sort file.txt", "sort file contents", ["safe"]),
            ("uniq file.txt", "show unique lines", ["safe"])
        ]
        
        for command, query, expected_tags in read_only_tests:
            tags = auto_tag(query, command)
            assert "safe" in tags, f"Read-only command '{command}' should be tagged as 'safe'"
    
    def test_auto_tag_complex_commands(self):
        """Test auto-tagging of complex commands with specific categories."""
        # Test cleanup commands
        cleanup_tests = [
            ("rm -rf /tmp/old_files", "remove old temporary files", ["cleanup"]),
            ("apt autoremove", "clean up unused packages", ["cleanup", "install"]),
            ("docker system prune", "clean up docker resources", ["cleanup"]),
            ("find . -name '*.log' -delete", "delete log files", ["cleanup"]),
            ("rm *.tmp", "remove temporary files", ["cleanup"])
        ]
        
        for command, query, expected_tags in cleanup_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
        
        # Test monitoring commands
        monitoring_tests = [
            ("htop", "show system processes", ["monitoring"]),
            ("top -p 1234", "monitor specific process", ["monitoring"]),
            ("watch -n 1 'df -h'", "watch disk usage", ["monitoring"]),
            ("vmstat 1", "show virtual memory stats", ["monitoring"]),
            ("iostat -x 1", "show IO statistics", ["monitoring"]),
            ("glances", "show system overview", ["monitoring"])
        ]
        
        for command, query, expected_tags in monitoring_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
        
        # Test network commands
        network_tests = [
            ("ping google.com", "test connectivity to google", ["network"]),
            ("curl -I https://example.com", "check website headers", ["network"]),
            ("wget https://example.com/file.txt", "download file", ["network"]),
            ("ssh user@server", "connect to remote server", ["network"]),
            ("scp file.txt user@server:/tmp/", "copy file to server", ["network"]),
            ("nmap -sP 192.168.1.0/24", "scan network", ["network"]),
            ("nc -l 8080", "listen on port 8080", ["network"])
        ]
        
        for command, query, expected_tags in network_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
        
        # Test install/update commands
        install_tests = [
            ("apt update", "update package lists", ["install"]),
            ("apt install vim", "install vim editor", ["install"]),
            ("yum update", "update system packages", ["install"]),
            ("brew install node", "install nodejs", ["install"]),
            ("pip install requests", "install python package", ["install"]),
            ("npm install -g typescript", "install typescript globally", ["install"])
        ]
        
        for command, query, expected_tags in install_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
        
        # Test backup commands
        backup_tests = [
            ("cp -r /home/user /backup/", "backup user directory", ["backup"]),
            ("rsync -av /data/ /backup/data/", "sync data to backup", ["backup"]),
            ("tar -czf backup.tar.gz /home/user", "create compressed backup", ["backup"]),
            ("zip -r backup.zip /important/", "create zip backup", ["backup"]),
            ("gzip large_file.txt", "compress file", ["backup"])
        ]
        
        for command, query, expected_tags in backup_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
        
        # Test resource-intensive commands
        resource_tests = [
            ("make -j4", "compile with 4 jobs", ["resource-intensive"]),
            ("gcc -O2 program.c", "compile program", ["resource-intensive"]),
            ("mvn clean install", "build maven project", ["resource-intensive"]),
            ("npm run build", "build nodejs project", ["resource-intensive"])
        ]
        
        for command, query, expected_tags in resource_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
    
    def test_auto_tag_multiple_tags(self):
        """Test commands that should receive multiple tags."""
        multi_tag_tests = [
            # Safe + monitoring
            ("top", "show running processes", ["safe", "monitoring"]),
            
            # Cleanup + install (apt autoremove)
            ("apt autoremove", "remove unused packages", ["cleanup", "install"]),
            
            # Network + backup (rsync over ssh)
            ("rsync -av -e ssh /data/ user@server:/backup/", "backup data to remote server", ["network", "backup"]),
            
            # Safe + network (ping)
            ("ping -c 4 8.8.8.8", "test network connectivity", ["safe", "network"]),
            
            # Backup + cleanup (tar with rm)
            ("tar -czf backup.tar.gz /tmp/data && rm -rf /tmp/data", "backup and cleanup temp data", ["backup", "cleanup"]),
            
            # Install + network (wget + dpkg)
            ("wget https://example.com/package.deb && dpkg -i package.deb", "download and install package", ["network", "install"]),
            
            # Monitoring + network (watching network stats)
            ("watch -n 1 'netstat -tuln'", "monitor network connections", ["monitoring", "network"]),
            
            # Safe + backup (copying files)
            ("cp -r /home/user/documents /backup/", "backup user documents", ["safe", "backup"])
        ]
        
        for command, query, expected_tags in multi_tag_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Command '{command}' should have tag '{tag}', got: {tags}"
            
            # Verify we got at least the expected number of tags
            assert len(tags) >= len(expected_tags), f"Command '{command}' should have at least {len(expected_tags)} tags, got: {tags}"
    
    def test_auto_tag_case_insensitive(self):
        """Test that auto-tagging is case insensitive."""
        case_tests = [
            ("LS -LA", "LIST FILES", ["safe"]),
            ("RM -RF /tmp/test", "REMOVE TEST FILES", ["cleanup"]),
            ("CURL https://example.com", "DOWNLOAD FROM URL", ["network"]),
            ("APT UPDATE", "UPDATE PACKAGES", ["install"]),
            ("HTOP", "SHOW PROCESSES", ["monitoring"]),
            ("CP file.txt backup.txt", "COPY FILE", ["backup"])
        ]
        
        for command, query, expected_tags in case_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Case insensitive test failed for command '{command}', expected tag '{tag}', got: {tags}"
    
    def test_auto_tag_query_context(self):
        """Test that query context influences tagging."""
        # Test where query provides context that command alone wouldn't
        query_context_tests = [
            # Query mentions install but command doesn't explicitly show it
            ("./configure --prefix=/usr", "install software from source", ["install"]),
            
            # Query mentions backup but command is generic copy
            ("cp -r /home/user /external/drive/", "backup user data", ["backup"]),
            
            # Query mentions cleanup but command is generic removal
            ("find /tmp -mtime +7 -exec rm {} \\;", "cleanup old temporary files", ["cleanup"]),
            
            # Query mentions update but command doesn't show it explicitly
            ("git pull origin main", "update code from repository", ["install"]),
        ]
        
        for command, query, expected_tags in query_context_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Query context test failed for '{command}' with query '{query}', expected tag '{tag}', got: {tags}"
    
    def test_auto_tag_empty_inputs(self):
        """Test handling of empty or invalid inputs."""
        empty_tests = [
            ("", "", []),
            ("   ", "   ", []),
            ("", "some query", []),
            ("some command", "", [])
        ]
        
        for command, query, expected_tags in empty_tests:
            tags = auto_tag(query, command)
            assert isinstance(tags, list), f"Should return list for empty inputs, got: {type(tags)}"
            # Empty inputs should return empty list or very minimal tags
            assert len(tags) <= 1, f"Empty inputs should return minimal tags, got: {tags}"
    
    def test_auto_tag_unique_tags(self):
        """Test that duplicate tags are removed."""
        # Command that could potentially generate duplicate tags
        command = "ls -la && ls -la"  # Safe command repeated
        query = "list files twice"
        
        tags = auto_tag(query, command)
        
        # Check that tags are unique
        assert len(tags) == len(set(tags)), f"Tags should be unique, got duplicates: {tags}"
        
        # Test with a command that hits multiple keyword categories
        command = "rsync -av /backup/ /network/backup/ && cp /backup/file.txt /local/backup/"
        query = "backup files to network and local backup"
        
        tags = auto_tag(query, command)
        
        # Should not have duplicate 'backup' tags
        assert len(tags) == len(set(tags)), f"Tags should be unique, got duplicates: {tags}"
        assert "backup" in tags, "Should have backup tag"
    
    def test_auto_tag_command_prefixes(self):
        """Test that command prefixes are properly detected."""
        prefix_tests = [
            # Commands that start with safe commands
            ("ls -la /home/user", "list user directory", ["safe"]),
            ("cat /etc/passwd", "show password file", ["safe"]),
            ("echo $PATH", "show path variable", ["safe"]),
            
            # Commands that start with other keywords
            ("rm -rf /tmp/test", "remove test directory", ["cleanup"]),
            ("curl -v https://api.example.com", "test api endpoint", ["network"]),
            ("apt list --installed", "show installed packages", ["install"])
        ]
        
        for command, query, expected_tags in prefix_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Prefix test failed for command '{command}', expected tag '{tag}', got: {tags}"
    
    def test_auto_tag_substring_matching(self):
        """Test that substring matching works correctly."""
        substring_tests = [
            # Keywords that appear in the middle of commands
            ("systemctl restart nginx", "restart web server", []),  # Should not match 'install' from systemctl
            ("find /home -name '*backup*'", "find backup files", ["backup"]),  # Should match 'backup' in filename
            ("ps aux | grep ping", "find ping processes", ["safe", "network"]),  # Should match both ps (safe) and ping (network)
            ("docker run --rm alpine:latest", "run container", ["cleanup"]),  # Should match 'rm' in --rm flag
        ]
        
        for command, query, expected_tags in substring_tests:
            tags = auto_tag(query, command)
            for tag in expected_tags:
                assert tag in tags, f"Substring test failed for command '{command}', expected tag '{tag}', got: {tags}"
    
    def test_auto_tag_edge_cases(self):
        """Test edge cases and unusual command structures."""
        edge_cases = [
            # Commands with complex piping
            ("ps aux | grep python | grep -v grep", "find python processes", ["safe"]),
            
            # Commands with quotes and special characters
            ("echo 'Hello, World!' > /tmp/test.txt", "write hello world to file", ["safe"]),
            
            # Commands with environment variables
            ("export PATH=$PATH:/usr/local/bin", "update path variable", []),
            
            # Commands with redirection
            ("ls -la > directory_listing.txt", "save directory listing", ["safe"]),
            
            # Commands with background execution
            ("nohup long_running_script.sh &", "run script in background", []),
            
            # Commands with command substitution
            ("echo $(date)", "show current date", ["safe"]),
        ]
        
        for command, query, expected_tags in edge_cases:
            tags = auto_tag(query, command)
            # Just ensure it doesn't crash and returns a list
            assert isinstance(tags, list), f"Edge case test failed for command '{command}', should return list, got: {type(tags)}"
            
            # Check expected tags if any
            for tag in expected_tags:
                assert tag in tags, f"Edge case test failed for command '{command}', expected tag '{tag}', got: {tags}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])