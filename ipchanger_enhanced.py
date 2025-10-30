#!/usr/bin/env python3
"""
Network IP Changer - Professional Windows Network Configuration Tool (Enhanced Edition)

A comprehensive network management application with GUI and CLI interfaces supporting:
- Static IP and DHCP configuration (v1.0.0 compatible)
- Network profile management 
- Multi-language support (6 languages)
- Command-line interface and batch operations
- Network connectivity testing and speed analysis
- Advanced DNS configuration (DoH/DoT support)
- Network adapter management
- VPN profile management
- Advanced routing configuration
- Real-time network monitoring dashboard

Author: PyxSara
Version: 2.0.0
License: MIT License
Repository: https://github.com/PyxSara/ipchanger
"""

import sys, os, json, re, subprocess, ctypes, argparse, csv, time, threading, socket, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import platform
import ipaddress
import sqlite3

# GUI imports (only if GUI mode)
gui_available = True
try:
    from PySide6.QtCore import Qt, QLocale, QTimer, QThread, Signal
    from PySide6.QtWidgets import (
        QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
        QComboBox, QLineEdit, QTextEdit, QMessageBox, QFileDialog, QGroupBox,
        QRadioButton, QButtonGroup, QFormLayout, QListWidget, QListWidgetItem,
        QInputDialog, QSizePolicy, QSpacerItem, QTabWidget, QProgressBar,
        QTableWidget, QTableWidgetItem, QCheckBox, QSpinBox, QSlider,
        QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView
    )
    from PySide6.QtGui import QIcon, QFont, QPixmap
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
except ImportError as e:
    gui_available = False
    print(f"Warning: GUI dependencies not available: {e}")
    print("Running in CLI-only mode.")

# Application Information
__version__ = "2.0.0"
__author__ = "PyxSara"
__license__ = "MIT"
__repository__ = "https://github.com/PyxSara/ipchanger"

# Enhanced Configuration
APP_DIR = Path(__file__).resolve().parent
LOG_PATH = APP_DIR / "netconfig.log"
UNDO_PATH = APP_DIR / "netconfig_undo.json"
PROFILES_PATH = APP_DIR / "netconfig_profiles.json"
VPN_PROFILES_PATH = APP_DIR / "vpn_profiles.json"
ROUTES_PATH = APP_DIR / "custom_routes.json"
MONITORING_DB = APP_DIR / "network_monitoring.db"
I18N_DIR = APP_DIR / "i18n"
ICON_PATH = APP_DIR / "ip.ico"

# Feature flags for compatibility
ENABLE_ADVANCED_FEATURES = True
ENABLE_CLI_MODE = True
ENABLE_BATCH_OPERATIONS = True
ENABLE_NETWORK_TESTING = True
ENABLE_VPN_MANAGEMENT = True
ENABLE_MONITORING = True

def elevate_if_needed():
    """Request admin privileges if not already elevated. Works on Windows Home and Pro."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    
    if not is_admin:
        try:
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 0
            )
            if ret > 32:
                sys.exit(0)
            else:
                return False
        except Exception:
            return False
    return True

def load_translations():
    """Load translation files for internationalization."""
    trans = {}
    if not I18N_DIR.exists():
        return trans
    for p in I18N_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                trans[p.stem] = json.load(f)
        except Exception:
            pass
    return trans

# Initialize translations
TRANSLATIONS = load_translations()
if "en" not in TRANSLATIONS:
    TRANSLATIONS["en"] = {"title":"Network Configurator","language":"Language:"}
RTL_LANGS = {"ar","fa","ku_sorani"}

CURRENT_LANG = "en"
CURRENT_TR = TRANSLATIONS.get(CURRENT_LANG, {})
IS_RTL = False

def tr(key):
    """Translation function."""
    return CURRENT_TR.get(key, key)

def set_language(lang_code: str) -> str:
    """Update global language settings for shared UI components."""
    global CURRENT_LANG, CURRENT_TR, IS_RTL
    if lang_code in TRANSLATIONS:
        CURRENT_LANG = lang_code
    else:
        CURRENT_LANG = "en"
    CURRENT_TR = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS.get("en", {}))
    IS_RTL = CURRENT_LANG in RTL_LANGS
    return CURRENT_LANG

# Enhanced networking functions
def run_netsh(args):
    """Execute netsh commands with enhanced error handling."""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        p = subprocess.run(
            ["netsh"] + args, 
            capture_output=True, 
            text=True, 
            shell=False,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=30  # Add timeout
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def run_powershell(command, timeout=30):
    """Run PowerShell command with timeout."""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        p = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            shell=False,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=timeout
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "PowerShell command timed out"
    except Exception as e:
        return 1, "", str(e)

def log_message(message, level="INFO"):
    """Enhanced logging with levels and timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
        if level in ["ERROR", "CRITICAL"] or "--verbose" in sys.argv:
            print(f"{level}: {message}")
    except Exception:
        pass

# Network Testing Functions
class NetworkTester:
    """Advanced network connectivity and performance testing."""
    
    @staticmethod
    def ping_host(host, count=4, timeout=3):
        """Ping a host and return real statistics."""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout*1000), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout*count+5)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                output = result.stdout.lower()
                stats = {
                    "success": True, 
                    "packets_sent": count, 
                    "packets_lost": 0, 
                    "avg_time": 0,
                    "min_time": 0,
                    "max_time": 0,
                    "host": host,
                    "duration": duration
                }
                
                # Parse Windows ping output
                if system == "windows":
                    # Extract packet loss
                    if "lost =" in output:
                        lost_match = re.search(r'lost = (\d+)', output)
                        if lost_match:
                            stats["packets_lost"] = int(lost_match.group(1))
                    
                    # Extract timing statistics
                    if "average =" in output:
                        avg_match = re.search(r'average = (\d+)ms', output)
                        if avg_match:
                            stats["avg_time"] = int(avg_match.group(1))
                    
                    if "minimum =" in output:
                        min_match = re.search(r'minimum = (\d+)ms', output)
                        if min_match:
                            stats["min_time"] = int(min_match.group(1))
                    
                    if "maximum =" in output:
                        max_match = re.search(r'maximum = (\d+)ms', output)
                        if max_match:
                            stats["max_time"] = int(max_match.group(1))
                
                return stats
            else:
                error_msg = result.stderr.strip() if result.stderr else "Ping failed"
                return {"success": False, "error": error_msg, "host": host}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Ping timeout", "host": host}
        except Exception as e:
            return {"success": False, "error": str(e), "host": host}
    
    @staticmethod
    def test_dns_resolution(domain="google.com", dns_server=None, timeout=5):
        """Test DNS resolution speed and reliability."""
        try:
            start_time = time.time()
            
            if dns_server:
                # Use nslookup with specific DNS server - more reliable approach
                try:
                    cmd = ["nslookup", domain, dns_server]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                    
                    if result.returncode == 0:
                        output = result.stdout.lower()
                        success = "can't find" not in output and "server failed" not in output
                        
                        # Extract IP addresses from nslookup output
                        ips = []
                        import re
                        ip_pattern = r'address:\s*(\d+\.\d+\.\d+\.\d+)'
                        matches = re.findall(ip_pattern, result.stdout)
                        ips = [ip for ip in matches if not ip.startswith('127.')]  # Filter out localhost
                    else:
                        success = False
                        ips = []
                        
                except subprocess.TimeoutExpired:
                    success = False
                    ips = []
                except Exception:
                    success = False
                    ips = []
            else:
                # Use Python's built-in resolution with timeout
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(timeout)
                try:
                    ip = socket.gethostbyname(domain)
                    ips = [ip]
                    success = True
                finally:
                    socket.setdefaulttimeout(old_timeout)
            
            resolution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "success": success, 
                "resolution_time": round(resolution_time, 2), 
                "domain": domain,
                "dns_server": dns_server or "System DNS",
                "resolved_ips": ips if 'ips' in locals() else []
            }
            
        except socket.timeout:
            return {"success": False, "error": "DNS timeout", "domain": domain, "dns_server": dns_server}
        except Exception as e:
            return {"success": False, "error": str(e), "domain": domain, "dns_server": dns_server}
    
    @staticmethod
    def traceroute(host, max_hops=30):
        """Perform traceroute to destination."""
        try:
            cmd = f"tracert -h {max_hops} {host}"
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=60)
            
            hops = []
            lines = result.stdout.split('\n')[4:]  # Skip header lines
            
            for line in lines:
                if line.strip() and not "Trace complete" in line:
                    hop_match = re.match(r'\s*(\d+)', line)
                    if hop_match:
                        hop_num = int(hop_match.group(1))
                        # Extract IP addresses and times
                        ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
                        time_matches = re.findall(r'(\d+) ms', line)
                        
                        hop_info = {
                            "hop": hop_num,
                            "ips": ip_matches,
                            "times": [int(t) for t in time_matches]
                        }
                        hops.append(hop_info)
            
            return {"success": True, "hops": hops}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def speed_test_basic(quick=True):
        """Improved network speed test with better reliability."""
        # Use more reliable test files with different sizes
        if quick:
            test_urls = [
                {"url": "http://ipv4.download.thinkbroadband.com/1MB.zip", "expected_mb": 1},
                {"url": "http://ipv4.download.thinkbroadband.com/5MB.zip", "expected_mb": 5}
            ]
        else:
            test_urls = [
                {"url": "http://ipv4.download.thinkbroadband.com/1MB.zip", "expected_mb": 1},
                {"url": "http://ipv4.download.thinkbroadband.com/5MB.zip", "expected_mb": 5},
                {"url": "http://ipv4.download.thinkbroadband.com/10MB.zip", "expected_mb": 10}
            ]
        
        results = []
        for test in test_urls:
            url = test["url"]
            expected_mb = test["expected_mb"]
            
            try:
                # Create request with proper headers
                headers = {
                    'User-Agent': 'NetworkIPChanger/2.0.0 (Speed Test)',
                    'Accept': '*/*',
                    'Connection': 'close'
                }
                
                req = urllib.request.Request(url, headers=headers)
                
                start_time = time.time()
                with urllib.request.urlopen(req, timeout=15) as response:
                    # Read in chunks to avoid memory issues
                    total_size = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        total_size += len(chunk)
                        
                        # Break early if we've read enough for timing
                        if total_size >= expected_mb * 1024 * 1024:
                            break
                
                end_time = time.time()
                
                size_mb = total_size / (1024 * 1024)
                duration = end_time - start_time
                
                if duration > 0:
                    speed_mbps = (size_mb * 8) / duration
                    speed_kbps = speed_mbps * 1024
                else:
                    speed_mbps = 0
                    speed_kbps = 0
                
                results.append({
                    "url": url,
                    "size_mb": round(size_mb, 2),
                    "duration": round(duration, 2),
                    "speed_mbps": round(speed_mbps, 2),
                    "speed_kbps": round(speed_kbps, 0),
                    "success": True
                })
                
            except urllib.error.URLError as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": f"URL Error: {str(e)}"
                })
            except socket.timeout:
                results.append({
                    "url": url,
                    "success": False,
                    "error": "Connection timeout"
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        return results

# Enhanced Network Functions
def list_adapters():
    """Get all network adapters with enhanced information."""
    adapters = []
    
    # Get basic adapter list
    rc, out, err = run_netsh(["interface", "show", "interface"])
    if rc == 0 and out:
        for line in out.splitlines()[3:]:
            parts = line.strip().split()
            if len(parts) >= 4:
                status = parts[0]
                adapter_name = " ".join(parts[3:])
                if not any(x in adapter_name.lower() for x in ['loopback', 'isatap', 'teredo']):
                    adapters.append({
                        "name": adapter_name,
                        "status": status,
                        "type": "Unknown"
                    })
    
    # Enhance with PowerShell information
    ps_cmd = "Get-NetAdapter | Select-Object Name, InterfaceDescription, LinkSpeed, MediaType | ConvertTo-Json"
    rc, out, err = run_powershell(ps_cmd)
    if rc == 0 and out:
        try:
            ps_data = json.loads(out)
            if not isinstance(ps_data, list):
                ps_data = [ps_data]
            
            # Match and enhance adapter information
            for adapter in adapters:
                for ps_adapter in ps_data:
                    if ps_adapter.get("Name") == adapter["name"]:
                        adapter["description"] = ps_adapter.get("InterfaceDescription", "")
                        adapter["link_speed"] = ps_adapter.get("LinkSpeed", 0)
                        adapter["media_type"] = ps_adapter.get("MediaType", "Unknown")
                        break
        except json.JSONDecodeError:
            pass
    
    return adapters

def get_adapter_config(adapter_name):
    """Get current configuration of a network adapter with enhanced details."""
    config = {
        "adapter": adapter_name,
        "dhcp": True,
        "ip": "",
        "mask": "",
        "gateway": "",
        "dns": [],
        "status": "Unknown",
        "mac_address": "",
        "mtu": 1500
    }
    
    # Get IP configuration
    rc, out, err = run_netsh(["interface", "ip", "show", "config", f'name="{adapter_name}"'])
    if rc == 0 and out:
        for line in out.splitlines():
            line = line.strip()
            if "DHCP enabled:" in line:
                config["dhcp"] = "Yes" in line
            elif "IP Address:" in line and not config["ip"]:
                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    config["ip"] = ip_match.group(1)
            elif "Subnet Prefix:" in line and not config["mask"]:
                mask_match = re.search(r'/(\d+)', line)
                if mask_match:
                    prefix = int(mask_match.group(1))
                    config["mask"] = str(ipaddress.IPv4Network(f'0.0.0.0/{prefix}', strict=False).netmask)
            elif "Default Gateway:" in line:
                gw_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if gw_match:
                    config["gateway"] = gw_match.group(1)
            elif "DNS servers configured through DHCP:" in line or "Statically Configured DNS Servers:" in line:
                dns_servers = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
                config["dns"].extend(dns_servers)
    
    # Get additional information via PowerShell
    ps_cmd = f'Get-NetAdapter -Name "{adapter_name}" | Select-Object MacAddress, MtuSize | ConvertTo-Json'
    rc, out, err = run_powershell(ps_cmd)
    if rc == 0 and out:
        try:
            ps_data = json.loads(out)
            config["mac_address"] = ps_data.get("MacAddress", "")
            config["mtu"] = ps_data.get("MtuSize", 1500)
        except json.JSONDecodeError:
            pass
    
    return config

def enable_disable_adapter(adapter_name, enable=True):
    """Enable or disable a network adapter with safety checks."""
    if not ENABLE_ADVANCED_FEATURES:
        return False, "Advanced features disabled"
    
    action = "enable" if enable else "disable"
    log_message(f"Attempting to {action} adapter: {adapter_name}")
    
    # Safety check: Don't disable if it's the only active adapter
    if not enable:
        active_adapters = [a for a in list_adapters() if a["status"] == "Connected"]
        if len(active_adapters) <= 1:
            return False, "Cannot disable the only active network adapter"
    
    rc, out, err = run_netsh(["interface", "set", "interface", f'name="{adapter_name}"', f'admin={action}'])
    
    success = rc == 0
    log_message(f"Adapter {action} {'successful' if success else 'failed'}: {err if err else out}")
    return success, err if err else out

# Command Line Interface
class NetworkCLI:
    """Command-line interface for network operations."""
    
    def __init__(self):
        self.parser = self.setup_parser()
    
    def setup_parser(self):
        """Setup argument parser for CLI operations."""
        parser = argparse.ArgumentParser(
            description='Network IP Changer - Professional Network Configuration Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --list-adapters
  %(prog)s --adapter "Ethernet" --dhcp
  %(prog)s --adapter "Wi-Fi" --static --ip 192.168.1.100 --mask 255.255.255.0 --gateway 192.168.1.1 --dns 8.8.8.8,8.8.4.4
  %(prog)s --batch-config config.json
  %(prog)s --test-connectivity
  %(prog)s --speed-test
            """
        )
        
        # Mode selection
        parser.add_argument('--cli', action='store_true', help='Force CLI mode')
        parser.add_argument('--gui', action='store_true', help='Force GUI mode (default)')
        
        # Adapter operations
        parser.add_argument('--list-adapters', action='store_true', help='List all network adapters')
        parser.add_argument('--adapter', type=str, help='Target network adapter name')
        parser.add_argument('--enable-adapter', type=str, help='Enable specified adapter')
        parser.add_argument('--disable-adapter', type=str, help='Disable specified adapter')
        
        # IP configuration
        parser.add_argument('--dhcp', action='store_true', help='Configure adapter for DHCP')
        parser.add_argument('--static', action='store_true', help='Configure adapter for static IP')
        parser.add_argument('--ip', type=str, help='IP address for static configuration')
        parser.add_argument('--mask', type=str, help='Subnet mask for static configuration')
        parser.add_argument('--gateway', type=str, help='Default gateway for static configuration')
        parser.add_argument('--dns', type=str, help='DNS servers (comma-separated)')
        
        # Batch operations
        parser.add_argument('--batch-config', type=str, help='Apply batch configuration from JSON/CSV file')
        parser.add_argument('--export-config', type=str, help='Export current configuration to file')
        
        # Testing operations
        parser.add_argument('--test-connectivity', action='store_true', help='Test network connectivity')
        parser.add_argument('--ping', type=str, help='Ping specific host')
        parser.add_argument('--traceroute', type=str, help='Traceroute to specific host')
        parser.add_argument('--speed-test', action='store_true', help='Perform network speed test')
        parser.add_argument('--dns-test', type=str, help='Test DNS resolution for domain')
        
        # Profile operations
        parser.add_argument('--save-profile', type=str, help='Save current configuration as profile')
        parser.add_argument('--load-profile', type=str, help='Load and apply configuration profile')
        parser.add_argument('--list-profiles', action='store_true', help='List all saved profiles')
        
        # Utility options
        parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
        
        return parser
    
    def run(self, args):
        """Execute CLI operations."""
        if args.verbose:
            log_message("Verbose mode enabled")
        
        # List adapters
        if args.list_adapters:
            self.list_adapters()
            return
        
        # Adapter management
        if args.enable_adapter:
            self.enable_disable_adapter(args.enable_adapter, True)
            return
        
        if args.disable_adapter:
            self.enable_disable_adapter(args.disable_adapter, False)
            return
        
        # Network testing
        if args.test_connectivity:
            self.test_connectivity()
            return
        
        if args.ping:
            self.ping_host(args.ping)
            return
        
        if args.traceroute:
            self.traceroute_host(args.traceroute)
            return
        
        if args.speed_test:
            self.speed_test()
            return
        
        if args.dns_test:
            self.dns_test(args.dns_test)
            return
        
        # Configuration operations
        if args.batch_config:
            self.batch_configure(args.batch_config)
            return
        
        if args.export_config:
            self.export_configuration(args.export_config)
            return
        
        # Profile operations
        if args.list_profiles:
            self.list_profiles()
            return
        
        if args.save_profile:
            self.save_profile(args.save_profile, args.adapter)
            return
        
        if args.load_profile:
            self.load_profile(args.load_profile, args.adapter)
            return
        
        # IP configuration
        if args.adapter:
            if args.dhcp:
                self.configure_dhcp(args.adapter)
            elif args.static and args.ip:
                self.configure_static(args.adapter, args.ip, args.mask, args.gateway, args.dns)
            else:
                self.show_adapter_config(args.adapter)
        else:
            print("No operation specified. Use --help for usage information.")
    
    def list_adapters(self):
        """List all network adapters."""
        print("Network Adapters:")
        print("-" * 80)
        adapters = list_adapters()
        
        for adapter in adapters:
            print(f"Name: {adapter['name']}")
            print(f"Status: {adapter.get('status', 'Unknown')}")
            print(f"Type: {adapter.get('media_type', 'Unknown')}")
            if adapter.get('description'):
                print(f"Description: {adapter['description']}")
            print("-" * 40)
    
    def show_adapter_config(self, adapter_name):
        """Show current configuration of an adapter."""
        config = get_adapter_config(adapter_name)
        
        print(f"Configuration for '{adapter_name}':")
        print("-" * 50)
        print(f"DHCP Enabled: {config['dhcp']}")
        print(f"IP Address: {config.get('ip', 'Not configured')}")
        print(f"Subnet Mask: {config.get('mask', 'Not configured')}")
        print(f"Default Gateway: {config.get('gateway', 'Not configured')}")
        print(f"DNS Servers: {', '.join(config.get('dns', []))}")
        print(f"MAC Address: {config.get('mac_address', 'Unknown')}")
        print(f"MTU: {config.get('mtu', 'Unknown')}")
    
    def configure_dhcp(self, adapter_name):
        """Configure adapter for DHCP."""
        print(f"Configuring '{adapter_name}' for DHCP...")
        
        # Set IP to DHCP
        rc1, out1, err1 = run_netsh(["interface", "ip", "set", "address", f'name="{adapter_name}"', "dhcp"])
        
        # Set DNS to DHCP
        rc2, out2, err2 = run_netsh(["interface", "ip", "set", "dns", f'name="{adapter_name}"', "dhcp"])
        
        if rc1 == 0 and rc2 == 0:
            print("✅ DHCP configuration applied successfully")
            log_message(f"DHCP configured for {adapter_name}")
        else:
            print(f"❌ Configuration failed: {err1 or err2}")
            log_message(f"DHCP configuration failed for {adapter_name}: {err1 or err2}", "ERROR")
    
    def configure_static(self, adapter_name, ip, mask=None, gateway=None, dns=None):
        """Configure adapter for static IP."""
        print(f"Configuring '{adapter_name}' for static IP...")
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            print(f"❌ Invalid IP address: {ip}")
            return
        
        # Build netsh command
        cmd = ["interface", "ip", "set", "address", f'name="{adapter_name}"', "static", ip]
        if mask:
            cmd.append(mask)
        if gateway:
            cmd.append(gateway)
        
        rc, out, err = run_netsh(cmd)
        
        if rc == 0:
            print(f"✅ IP address {ip} configured successfully")
            log_message(f"Static IP {ip} configured for {adapter_name}")
            
            # Configure DNS if provided
            if dns:
                dns_servers = [d.strip() for d in dns.split(',')]
                for i, dns_server in enumerate(dns_servers):
                    dns_cmd = ["interface", "ip", "set", "dns", f'name="{adapter_name}"']
                    if i == 0:
                        dns_cmd.extend(["static", dns_server])
                    else:
                        dns_cmd.extend(["static", dns_server, "index=" + str(i + 1)])
                    
                    rc_dns, out_dns, err_dns = run_netsh(dns_cmd)
                    if rc_dns == 0:
                        print(f"✅ DNS server {dns_server} configured")
                    else:
                        print(f"❌ Failed to configure DNS {dns_server}: {err_dns}")
        else:
            print(f"❌ Configuration failed: {err}")
            log_message(f"Static IP configuration failed for {adapter_name}: {err}", "ERROR")
    
    def enable_disable_adapter(self, adapter_name, enable=True):
        """Enable or disable network adapter."""
        action = "enable" if enable else "disable"
        print(f"Attempting to {action} adapter '{adapter_name}'...")
        
        success, message = enable_disable_adapter(adapter_name, enable)
        if success:
            print(f"✅ Adapter {action}d successfully")
        else:
            print(f"❌ Failed to {action} adapter: {message}")
    
    def test_connectivity(self):
        """Test network connectivity quickly."""
        print("Testing network connectivity...")
        print("-" * 50)
        
        # Test common hosts with faster, single ping
        test_hosts = ["8.8.8.8", "1.1.1.1", "google.com", "cloudflare.com"]
        
        for host in test_hosts:
            print(f"Testing {host}...", end=" ", flush=True)
            result = NetworkTester.ping_host(host, count=1, timeout=2)
            
            if result["success"]:
                avg_time = result.get("avg_time", 0)
                print(f"✅ {avg_time}ms")
            else:
                print(f"❌ Failed")
                
        print("-" * 50)
    
    def ping_host(self, host):
        """Ping specific host quickly."""
        print(f"Pinging {host}...", end=" ", flush=True)
        result = NetworkTester.ping_host(host, count=2, timeout=3)
        
        if result["success"]:
            sent = result.get("packets_sent", 0)
            lost = result.get("packets_lost", 0)
            avg_time = result.get("avg_time", 0)
            min_time = result.get("min_time", 0)
            max_time = result.get("max_time", 0)
            print(f"✅")
            print(f"  Packets: Sent = {sent}, Lost = {lost}")
            print(f"  Times: Min = {min_time}ms, Max = {max_time}ms, Avg = {avg_time}ms")
        else:
            print(f"❌")
            print(f"  Error: {result.get('error', 'Unknown error')}")
    
    def traceroute_host(self, host):
        """Traceroute to specific host."""
        print(f"Tracing route to {host}...")
        result = NetworkTester.traceroute(host)
        
        if result["success"]:
            for hop in result["hops"]:
                hop_num = hop["hop"]
                ips = hop.get("ips", [])
                times = hop.get("times", [])
                
                ip_str = ips[0] if ips else "*"
                time_str = f"{min(times)}ms" if times else "*"
                print(f"{hop_num:2d}  {time_str:>8}  {ip_str}")
        else:
            print(f"Traceroute failed: {result.get('error', 'Unknown error')}")
    
    def speed_test(self):
        """Perform quick network speed test."""
        print("Running quick speed test...")
        print("⏳ Testing download speed...", end=" ", flush=True)
        
        results = NetworkTester.speed_test_basic(quick=True)
        
        successful_tests = [r for r in results if r["success"]]
        if successful_tests:
            avg_speed = sum(r["speed_mbps"] for r in successful_tests) / len(successful_tests)
            total_data = sum(r["size_mb"] for r in successful_tests)
            
            print(f"✅")
            print(f"📊 Speed Test Results:")
            print(f"  Average download speed: {avg_speed:.2f} Mbps ({avg_speed * 128:.0f} KB/s)")
            print(f"  Total data transferred: {total_data:.1f} MB")
            print(f"  Tests completed: {len(successful_tests)}/{len(results)}")
            
            for result in successful_tests:
                print(f"    {result['size_mb']:.1f}MB: {result['speed_mbps']:.2f} Mbps in {result['duration']:.1f}s")
                
        else:
            print(f"❌")
            print("❌ All speed tests failed. Possible issues:")
            for result in results:
                if not result["success"]:
                    print(f"  • {result.get('error', 'Unknown error')}")
            print("  • Check internet connection")
            print("  • Firewall might be blocking connections")
    
    def dns_test(self, domain):
        """Test DNS resolution quickly."""
        print(f"🔍 Testing DNS resolution for '{domain}'...")
        
        # Test with system DNS first
        print("  System DNS...", end=" ", flush=True)
        result = NetworkTester.test_dns_resolution(domain, timeout=3)
        if result["success"]:
            ips = result.get('resolved_ips', [])
            ip_str = f" → {ips[0]}" if ips else ""
            print(f"✅ {result['resolution_time']:.1f}ms{ip_str}")
        else:
            print(f"❌ {result.get('error', 'Failed')}")
        
        # Test with common DNS servers
        dns_servers = [
            ("8.8.8.8", "Google DNS"),
            ("1.1.1.1", "Cloudflare DNS"), 
            ("208.67.222.222", "OpenDNS")
        ]
        
        for dns_server, name in dns_servers:
            print(f"  {name}...", end=" ", flush=True)
            result = NetworkTester.test_dns_resolution(domain, dns_server, timeout=3)
            if result["success"]:
                print(f"✅ {result['resolution_time']:.1f}ms")
            else:
                print(f"❌ Failed")
                
        print("🔍 DNS test completed")
    
    def batch_configure(self, config_file):
        """Apply batch configuration from file."""
        print(f"Loading batch configuration from {config_file}...")
        
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                print(f"❌ Configuration file not found: {config_file}")
                return
            
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            elif config_path.suffix.lower() == '.csv':
                configs = []
                with open(config_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    configs = list(reader)
            else:
                print("❌ Unsupported file format. Use JSON or CSV.")
                return
            
            for config in configs:
                adapter_name = config.get('adapter')
                if not adapter_name:
                    print("⚠️ Skipping configuration without adapter name")
                    continue
                
                print(f"Configuring {adapter_name}...")
                
                if config.get('dhcp', '').lower() == 'true':
                    self.configure_dhcp(adapter_name)
                elif config.get('ip'):
                    self.configure_static(
                        adapter_name,
                        config.get('ip'),
                        config.get('mask'),
                        config.get('gateway'),
                        config.get('dns')
                    )
                
        except Exception as e:
            print(f"❌ Batch configuration failed: {e}")
            log_message(f"Batch configuration failed: {e}", "ERROR")
    
    def export_configuration(self, output_file):
        """Export current network configuration."""
        print(f"Exporting configuration to {output_file}...")
        
        try:
            adapters = list_adapters()
            configurations = []
            
            for adapter in adapters:
                if adapter["status"] == "Connected":
                    config = get_adapter_config(adapter["name"])
                    configurations.append(config)
            
            output_path = Path(output_file)
            
            if output_path.suffix.lower() == '.json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(configurations, f, indent=2)
            elif output_path.suffix.lower() == '.csv':
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if configurations:
                        fieldnames = configurations[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for config in configurations:
                            # Convert lists to comma-separated strings for CSV
                            config_copy = config.copy()
                            if isinstance(config_copy.get('dns'), list):
                                config_copy['dns'] = ','.join(config_copy['dns'])
                            writer.writerow(config_copy)
            
            print(f"✅ Configuration exported to {output_file}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            log_message(f"Configuration export failed: {e}", "ERROR")
    
    def list_profiles(self):
        """List all saved profiles."""
        try:
            if PROFILES_PATH.exists():
                with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                print("Saved Profiles:")
                print("-" * 40)
                for name, config in profiles.items():
                    mode = "DHCP" if config.get('mode') == 'dhcp' else "Static"
                    ip = config.get('ip', 'Auto')
                    print(f"{name}: {mode} ({ip})")
            else:
                print("No saved profiles found")
                
        except Exception as e:
            print(f"❌ Failed to list profiles: {e}")
    
    def save_profile(self, profile_name, adapter_name):
        """Save current adapter configuration as profile."""
        if not adapter_name:
            print("❌ Adapter name required for saving profile")
            return
        
        try:
            config = get_adapter_config(adapter_name)
            
            # Convert to profile format
            profile = {
                "mode": "dhcp" if config["dhcp"] else "static",
                "ip": config.get("ip", ""),
                "mask": config.get("mask", ""),
                "gateway": config.get("gateway", ""),
                "dns": config.get("dns", [])
            }
            
            # Load existing profiles
            profiles = {}
            if PROFILES_PATH.exists():
                with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            
            # Add new profile
            profiles[profile_name] = profile
            
            # Save profiles
            with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2)
            
            print(f"✅ Profile '{profile_name}' saved successfully")
            log_message(f"Profile '{profile_name}' saved")
            
        except Exception as e:
            print(f"❌ Failed to save profile: {e}")
            log_message(f"Failed to save profile '{profile_name}': {e}", "ERROR")
    
    def load_profile(self, profile_name, adapter_name):
        """Load and apply configuration profile."""
        if not adapter_name:
            print("❌ Adapter name required for loading profile")
            return
        
        try:
            if not PROFILES_PATH.exists():
                print("❌ No profiles file found")
                return
            
            with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                print(f"❌ Profile '{profile_name}' not found")
                return
            
            profile = profiles[profile_name]
            print(f"Loading profile '{profile_name}' for adapter '{adapter_name}'...")
            
            if profile.get('mode') == 'dhcp':
                self.configure_dhcp(adapter_name)
            else:
                dns_str = ','.join(profile.get('dns', [])) if profile.get('dns') else None
                self.configure_static(
                    adapter_name,
                    profile.get('ip'),
                    profile.get('mask'),
                    profile.get('gateway'),
                    dns_str
                )
            
        except Exception as e:
            print(f"❌ Failed to load profile: {e}")
            log_message(f"Failed to load profile '{profile_name}': {e}", "ERROR")
    
    def interactive_mode(self):
        """Run interactive CLI mode."""
        print("\n🔧 Network IP Changer - Interactive CLI Mode")
        print("=" * 50)
        print("Available commands:")
        print("  list-adapters              - List all network adapters")
        print("  config <adapter> dhcp      - Configure adapter for DHCP")
        print("  config <adapter> static    - Configure adapter for static IP")
        print("  show <adapter>             - Show adapter configuration")
        print("  enable <adapter>           - Enable network adapter")
        print("  disable <adapter>          - Disable network adapter")
        print("  test-connectivity          - Test network connectivity")
        print("  ping <host>                - Ping specific host")
        print("  speed-test                 - Run network speed test")
        print("  dns-test <domain>          - Test DNS resolution")
        print("  list-profiles              - List saved profiles")
        print("  save-profile <name> <adapter> - Save current config as profile")
        print("  load-profile <name> <adapter> - Load and apply profile")
        print("  help                       - Show this help")
        print("  exit                       - Exit interactive mode")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n>>> ").strip()
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif cmd in ['help', 'h', '?']:
                    self.interactive_mode()  # Show help again
                    break
                elif cmd == 'list-adapters':
                    self.list_adapters()
                elif cmd == 'test-connectivity':
                    self.test_connectivity()
                elif cmd == 'speed-test':
                    self.speed_test()
                elif cmd == 'list-profiles':
                    self.list_profiles()
                elif cmd == 'config' and len(parts) >= 3:
                    adapter = parts[1]
                    mode = parts[2].lower()
                    if mode == 'dhcp':
                        self.configure_dhcp(adapter)
                    elif mode == 'static':
                        print(f"Configuring {adapter} for static IP...")
                        ip = input("Enter IP address: ").strip()
                        mask = input("Enter subnet mask (default: 255.255.255.0): ").strip() or "255.255.255.0"
                        gateway = input("Enter gateway (optional): ").strip() or None
                        dns = input("Enter DNS servers (comma-separated, optional): ").strip() or None
                        self.configure_static(adapter, ip, mask, gateway, dns)
                    else:
                        print("❌ Mode must be 'dhcp' or 'static'")
                elif cmd == 'show' and len(parts) >= 2:
                    self.show_adapter_config(parts[1])
                elif cmd == 'enable' and len(parts) >= 2:
                    self.enable_disable_adapter(parts[1], True)
                elif cmd == 'disable' and len(parts) >= 2:
                    self.enable_disable_adapter(parts[1], False)
                elif cmd == 'ping' and len(parts) >= 2:
                    self.ping_host(parts[1])
                elif cmd == 'dns-test' and len(parts) >= 2:
                    self.dns_test(parts[1])
                elif cmd == 'save-profile' and len(parts) >= 3:
                    self.save_profile(parts[1], parts[2])
                elif cmd == 'load-profile' and len(parts) >= 3:
                    self.load_profile(parts[1], parts[2])
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return 0

def main():
    """Main application entry point."""
    # Parse command line arguments
    cli = NetworkCLI()
    args = cli.parser.parse_args()
    
    # Determine mode
    force_cli = args.cli or any(arg for arg in vars(args).values() if arg not in [False, None, 'gui'])
    force_gui = args.gui and not force_cli
    
    # Check if we should run in CLI mode
    if force_cli or not gui_available:
        if not gui_available and not force_cli:
            print("GUI dependencies not available. Running in CLI mode.")
        
        # Try to elevate privileges for network operations
        if not elevate_if_needed():
            print("⚠️ Warning: Running without administrator privileges. Some operations may fail.")
        
        # Run CLI
        cli.run(args)
        return
    
    # GUI Mode (Original v1.0.0 compatible interface with enhancements)
    if not gui_available:
        print("❌ GUI mode requested but PySide6 not available")
        sys.exit(1)
    
    # Try to elevate privileges
    elevation_success = elevate_if_needed()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Network Configurator Enhanced")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    
    # Initialize language settings
    global CURRENT_LANG, CURRENT_TR, IS_RTL
    sys_lang = QLocale.system().name()[:2]
    if sys_lang in TRANSLATIONS:
        CURRENT_LANG = sys_lang
    else:
        CURRENT_LANG = "en"
    CURRENT_TR = TRANSLATIONS.get(CURRENT_LANG, {})
    IS_RTL = CURRENT_LANG in RTL_LANGS
    
    # Create enhanced GUI (will be implemented in next part)
    w = create_enhanced_gui()
    
    # Show admin warning if needed
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        reply = QMessageBox.critical(
            w,
            "❌ Administrator Rights Required",
            "🔒 This application requires administrator privileges to modify network settings.\n\n"
            "❌ Current Status: Running as regular user\n"
            "✅ Required: Administrator privileges\n\n"
            "🔧 To fix this issue:\n"
            "1. Close this program\n"
            "2. Right-click on the program file\n"
            "3. Select 'Run as administrator'\n"
            "4. Click 'Yes' when prompted by Windows\n\n"
            "⚠️ Network configuration changes will FAIL without admin rights!\n\n"
            "Do you want to continue anyway? (Changes will fail)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            sys.exit(0)
    
    w.show()
    sys.exit(app.exec())

def create_enhanced_gui():
    """Create the enhanced GUI interface (placeholder for now)."""
    # This will be implemented with the enhanced GUI in the next part
    # For now, return a basic widget to maintain compatibility
    widget = QWidget()
    widget.setWindowTitle(f"Network IP Changer Enhanced v{__version__}")
    widget.resize(800, 600)
    
    layout = QVBoxLayout()
    label = QLabel("Enhanced Network IP Changer\nCLI mode available with --help")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    widget.setLayout(layout)
    
    return widget

if __name__ == "__main__":
    main()