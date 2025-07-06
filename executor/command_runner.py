import subprocess
import shlex
import time
import signal
import os
import threading
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import psutil
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"
    ERROR = "error"

@dataclass
class ExecutionResult:
    command: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    status: ExecutionStatus
    pid: Optional[int] = None
    resource_usage: Optional[Dict] = None
    error_message: Optional[str] = None

class CommandRunner:
    
    def __init__(self, 
                 timeout: int = 300, 
                 max_output_size: int = 10 * 1024 * 1024,  # 10MB
                 shell: str = "/bin/bash",
                 working_dir: Optional[str] = None,
                 env_vars: Optional[Dict[str, str]] = None):
        """
        Initialize CommandRunner with safety parameters
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum output size in bytes
            shell: Shell to use for execution
            working_dir: Working directory for command execution
            env_vars: Additional environment variables
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.shell = shell
        self.working_dir = working_dir or os.getcwd()
        self.env_vars = env_vars or {}
        
        # Resource monitoring
        self.max_memory_mb = 1024  # 1GB
        self.max_cpu_percent = 80
        
        # Process tracking
        self.current_process = None
        self.start_time = None
        
        # Validate shell
        if not os.path.exists(shell):
            logger.warning(f"Shell {shell} not found, using /bin/sh")
            self.shell = "/bin/sh"
    
    def execute(self, command: str, **kwargs) -> ExecutionResult:
        """
        Execute a command with safety checks and resource monitoring
        
        Args:
            command: The command to execute
            **kwargs: Additional execution parameters
                - timeout: Override default timeout
                - cwd: Override working directory
                - env: Override environment variables
                - capture_output: Whether to capture stdout/stderr
                - shell: Override shell
        
        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()
        
        # Override parameters if provided
        exec_timeout = kwargs.get('timeout', self.timeout)
        exec_cwd = kwargs.get('cwd', self.working_dir)
        exec_env = self._prepare_environment(kwargs.get('env', {}))
        capture_output = kwargs.get('capture_output', True)
        use_shell = kwargs.get('shell', self.shell)
        
        logger.info(f"Executing command: {command}")
        logger.debug(f"Working directory: {exec_cwd}")
        logger.debug(f"Timeout: {exec_timeout}s")
        
        try:
            # Prepare command
            if isinstance(command, str):
                # For shell commands, use shell=True
                cmd_args = command
                use_shell_flag = True
            else:
                # For command lists, use shell=False
                cmd_args = command
                use_shell_flag = False
            
            # Execute command
            result = self._execute_with_monitoring(
                cmd_args,
                timeout=exec_timeout,
                cwd=exec_cwd,
                env=exec_env,
                capture_output=capture_output,
                shell=use_shell_flag
            )
            
            execution_time = time.time() - start_time
            
            # Update result with timing
            result.execution_time = execution_time
            
            logger.info(f"Command completed in {execution_time:.2f}s with exit code {result.exit_code}")
            
            return result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.warning(f"Command timed out after {execution_time:.2f}s")
            
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {exec_timeout} seconds",
                execution_time=execution_time,
                status=ExecutionStatus.TIMEOUT,
                error_message="Command execution timed out"
            )
            
        except KeyboardInterrupt:
            execution_time = time.time() - start_time
            logger.info("Command interrupted by user")
            
            if self.current_process:
                self._terminate_process(self.current_process)
            
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-2,
                stdout="",
                stderr="Command interrupted by user",
                execution_time=execution_time,
                status=ExecutionStatus.INTERRUPTED,
                error_message="Command interrupted by user"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution failed: {e}")
            
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                status=ExecutionStatus.ERROR,
                error_message=str(e)
            )
    
    def _execute_with_monitoring(self, 
                               command,
                               timeout: int,
                               cwd: str,
                               env: Dict[str, str],
                               capture_output: bool,
                               shell: bool) -> ExecutionResult:
        
        # Start process
        process = subprocess.Popen(
            command,
            shell=shell,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        
        self.current_process = process
        self.start_time = time.time()
        
        # Monitor resource usage
        resource_monitor = None
        if capture_output:
            resource_monitor = self._start_resource_monitoring(process.pid)
        
        try:
            # Wait for completion with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Get final resource usage
            resource_usage = None
            if resource_monitor:
                resource_usage = self._stop_resource_monitoring(resource_monitor)
            
            # Truncate output if too large
            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + "\n... (output truncated)"
            
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + "\n... (output truncated)"
            
            success = process.returncode == 0
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            
            return ExecutionResult(
                command=command if isinstance(command, str) else ' '.join(command),
                success=success,
                exit_code=process.returncode,
                stdout=stdout or "",
                stderr=stderr or "",
                execution_time=0,  # Will be set by caller
                status=status,
                pid=process.pid,
                resource_usage=resource_usage
            )
            
        finally:
            self.current_process = None
            if resource_monitor:
                self._stop_resource_monitoring(resource_monitor)
    
    def _prepare_environment(self, additional_env: Dict[str, str]) -> Dict[str, str]:
        env = os.environ.copy()
        
        # Add configured environment variables
        env.update(self.env_vars)
        
        # Add additional environment variables
        env.update(additional_env)
        
        # Ensure PATH is set
        if 'PATH' not in env:
            env['PATH'] = '/usr/local/bin:/usr/bin:/bin'
        
        return env
    
    def _start_resource_monitoring(self, pid: int) -> Dict:
        monitor_data = {
            'pid': pid,
            'max_memory_mb': 0,
            'max_cpu_percent': 0,
            'start_time': time.time(),
            'stop_monitoring': False
        }
        
        def monitor_process():
            try:
                process = psutil.Process(pid)
                while not monitor_data['stop_monitoring']:
                    try:
                        # Get memory usage
                        memory_info = process.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                        monitor_data['max_memory_mb'] = max(monitor_data['max_memory_mb'], memory_mb)
                        
                        # Get CPU usage
                        cpu_percent = process.cpu_percent()
                        monitor_data['max_cpu_percent'] = max(monitor_data['max_cpu_percent'], cpu_percent)
                        
                        # Check limits
                        if memory_mb > self.max_memory_mb:
                            logger.warning(f"Process {pid} exceeded memory limit: {memory_mb:.1f}MB")
                        
                        if cpu_percent > self.max_cpu_percent:
                            logger.warning(f"Process {pid} exceeded CPU limit: {cpu_percent:.1f}%")
                        
                        time.sleep(0.5)  # Check every 500ms
                        
                    except psutil.NoSuchProcess:
                        break
                    except Exception as e:
                        logger.debug(f"Resource monitoring error: {e}")
                        break
                        
            except Exception as e:
                logger.debug(f"Resource monitoring setup error: {e}")
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
        
        return monitor_data
    
    def _stop_resource_monitoring(self, monitor_data: Dict) -> Dict:
        monitor_data['stop_monitoring'] = True
        monitor_data['total_time'] = time.time() - monitor_data['start_time']
        
        return {
            'max_memory_mb': monitor_data['max_memory_mb'],
            'max_cpu_percent': monitor_data['max_cpu_percent'],
            'total_time': monitor_data['total_time']
        }
    
    def _terminate_process(self, process: subprocess.Popen):
        """Safely terminate a process and its children"""
        try:
            if process.poll() is None:  # Process is still running
                # Try graceful termination first
                if os.name != 'nt':
                    # On Unix systems, terminate the process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # Wait for graceful termination
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful termination fails
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
                    
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
    
    def execute_dry_run(self, command: str) -> ExecutionResult:
        logger.info(f"Dry run: {command}")
        
        # Parse command to check for basic syntax errors
        try:
            if isinstance(command, str):
                shlex.split(command)
        except ValueError as e:
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command syntax error: {e}",
                execution_time=0,
                status=ExecutionStatus.ERROR,
                error_message=f"Syntax error: {e}"
            )
        
        return ExecutionResult(
            command=command,
            success=True,
            exit_code=0,
            stdout="[DRY RUN] Command would be executed here",
            stderr="",
            execution_time=0,
            status=ExecutionStatus.SUCCESS
        )
    
    def execute_with_input(self, command: str, input_data: str, **kwargs) -> ExecutionResult:
        start_time = time.time()
        
        exec_timeout = kwargs.get('timeout', self.timeout)
        exec_cwd = kwargs.get('cwd', self.working_dir)
        exec_env = self._prepare_environment(kwargs.get('env', {}))
        
        logger.info(f"Executing command with input: {command}")
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=exec_cwd,
                env=exec_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.current_process = process
            
            # Send input and wait for completion
            stdout, stderr = process.communicate(input=input_data, timeout=exec_timeout)
            
            execution_time = time.time() - start_time
            success = process.returncode == 0
            status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
            
            return ExecutionResult(
                command=command,
                success=success,
                exit_code=process.returncode,
                stdout=stdout or "",
                stderr=stderr or "",
                execution_time=execution_time,
                status=status,
                pid=process.pid
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            if self.current_process:
                self._terminate_process(self.current_process)
            
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {exec_timeout} seconds",
                execution_time=execution_time,
                status=ExecutionStatus.TIMEOUT,
                error_message="Command execution timed out"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Command execution with input failed: {e}")
            
            return ExecutionResult(
                command=command,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                status=ExecutionStatus.ERROR,
                error_message=str(e)
            )
        
        finally:
            self.current_process = None
    
    def get_command_info(self, command: str) -> Dict:
        try:
            # Parse command
            parts = shlex.split(command)
            if not parts:
                return {'error': 'Empty command'}
            
            binary = parts[0]
            
            # Check if binary exists
            binary_path = shutil.which(binary)
            
            info = {
                'binary': binary,
                'binary_path': binary_path,
                'exists': binary_path is not None,
                'args': parts[1:] if len(parts) > 1 else [],
                'estimated_safety': self._estimate_safety(command)
            }
            
            # Get binary info if it exists
            if binary_path:
                try:
                    stat_info = os.stat(binary_path)
                    info['binary_size'] = stat_info.st_size
                    info['binary_permissions'] = oct(stat_info.st_mode)[-3:]
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _estimate_safety(self, command: str) -> str:
        dangerous_keywords = ['rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'kill', 'sudo', 'su']
        moderate_keywords = ['cp', 'mv', 'chmod', 'chown', 'wget', 'curl']
        
        command_lower = command.lower()
        
        for keyword in dangerous_keywords:
            if keyword in command_lower:
                return 'dangerous'
        
        for keyword in moderate_keywords:
            if keyword in command_lower:
                return 'moderate'
        
        return 'safe'

# Utility functions
def parse_command_string(command: str) -> List[str]:
    try:
        return shlex.split(command)
    except ValueError:
        # If shlex fails, fall back to simple split
        return command.split()

def escape_shell_arg(arg: str) -> str:
    return shlex.quote(arg)

def build_command_string(args: List[str]) -> str:
    return ' '.join(shlex.quote(arg) for arg in args)