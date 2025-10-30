# VPN and Advanced Networking Modules for Network IP Changer Enhanced

import json
import socket
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class VPNManager:
    """VPN profile management and configuration."""
    
    def __init__(self, vpn_profiles_path):
        self.vpn_profiles_path = Path(vpn_profiles_path)
        self.profiles = self.load_profiles()
    
    def load_profiles(self):
        """Load VPN profiles from file."""
        if self.vpn_profiles_path.exists():
            try:
                with open(self.vpn_profiles_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def save_profiles(self):
        """Save VPN profiles to file."""
        try:
            with open(self.vpn_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2)
            return True
        except Exception:
            return False
    
    def add_profile(self, name, config):
        """Add a new VPN profile."""
        required_fields = ['type', 'server', 'username']
        if not all(field in config for field in required_fields):
            return False, "Missing required fields"
        
        self.profiles[name] = {
            'type': config['type'],  # 'pptp', 'l2tp', 'sstp', 'ikev2'
            'server': config['server'],
            'username': config['username'],
            'password': config.get('password', ''),  # Store encrypted in real implementation
            'preshared_key': config.get('preshared_key', ''),
            'local_ip': config.get('local_ip', ''),
            'remote_ip': config.get('remote_ip', ''),
            'dns_servers': config.get('dns_servers', []),
            'routes': config.get('routes', []),
            'auto_connect': config.get('auto_connect', False),
            'created': datetime.now().isoformat()
        }
        
        return self.save_profiles(), "Profile added successfully"
    
    def remove_profile(self, name):
        """Remove a VPN profile."""
        if name in self.profiles:
            del self.profiles[name]
            return self.save_profiles(), "Profile removed successfully"
        return False, "Profile not found"
    
    def connect_vpn(self, profile_name):
        """Connect to VPN using profile."""
        if profile_name not in self.profiles:
            return False, "Profile not found"
        
        profile = self.profiles[profile_name]
        
        try:
            # Create VPN connection using Windows RASDIAL
            cmd = [
                'rasdial',
                profile_name,
                profile['username'],
                profile['password'] if profile['password'] else ''
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Apply custom routes if specified
                if profile.get('routes'):
                    self.apply_vpn_routes(profile['routes'])
                
                # Apply custom DNS if specified
                if profile.get('dns_servers'):
                    self.apply_vpn_dns(profile_name, profile['dns_servers'])
                
                return True, "VPN connected successfully"
            else:
                return False, f"Connection failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def disconnect_vpn(self, profile_name):
        """Disconnect VPN connection."""
        try:
            cmd = ['rasdial', profile_name, '/disconnect']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "VPN disconnected successfully"
            else:
                return False, f"Disconnect failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Disconnect error: {str(e)}"
    
    def get_connection_status(self):
        """Get status of all VPN connections."""
        try:
            result = subprocess.run(['rasdial'], capture_output=True, text=True)
            connections = []
            
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Connected to' in line:
                    connection_name = line.split('Connected to')[1].strip()
                    connections.append({
                        'name': connection_name,
                        'status': 'Connected',
                        'type': 'VPN'
                    })
            
            return connections
            
        except Exception:
            return []
    
    def apply_vpn_routes(self, routes):
        """Apply custom routes for VPN connection."""
        for route in routes:
            try:
                cmd = [
                    'route', 'add',
                    route['destination'],
                    'mask', route['netmask'],
                    route['gateway']
                ]
                subprocess.run(cmd, check=True)
            except Exception:
                pass
    
    def apply_vpn_dns(self, connection_name, dns_servers):
        """Apply custom DNS servers for VPN connection."""
        try:
            # This would require more complex Windows API calls
            # For now, we'll use netsh to set DNS for the VPN adapter
            for i, dns in enumerate(dns_servers):
                if i == 0:
                    cmd = ['netsh', 'interface', 'ip', 'set', 'dns', f'name="{connection_name}"', 'static', dns]
                else:
                    cmd = ['netsh', 'interface', 'ip', 'add', 'dns', f'name="{connection_name}"', dns, f'index={i+1}']
                subprocess.run(cmd)
        except Exception:
            pass

class AdvancedRouting:
    """Advanced routing configuration and management."""
    
    def __init__(self, routes_path):
        self.routes_path = Path(routes_path)
        self.custom_routes = self.load_routes()
    
    def load_routes(self):
        """Load custom routes from file."""
        if self.routes_path.exists():
            try:
                with open(self.routes_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def save_routes(self):
        """Save custom routes to file."""
        try:
            with open(self.routes_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_routes, f, indent=2)
            return True
        except Exception:
            return False
    
    def get_routing_table(self):
        """Get current system routing table."""
        try:
            result = subprocess.run(['route', 'print'], capture_output=True, text=True)
            routes = []
            
            lines = result.stdout.split('\n')
            in_ipv4_section = False
            
            for line in lines:
                if 'IPv4 Route Table' in line:
                    in_ipv4_section = True
                    continue
                
                if in_ipv4_section and line.strip():
                    parts = line.split()
                    if len(parts) >= 5 and parts[0].replace('.', '').replace('0', '').isdigit():
                        routes.append({
                            'destination': parts[0],
                            'netmask': parts[1],
                            'gateway': parts[2],
                            'interface': parts[3],
                            'metric': parts[4] if len(parts) > 4 else '1'
                        })
            
            return routes
            
        except Exception:
            return []
    
    def add_static_route(self, destination, netmask, gateway, interface=None, metric=1, persistent=False):
        """Add a static route."""
        try:
            cmd = ['route', 'add', destination, 'mask', netmask, gateway]
            
            if interface:
                cmd.extend(['if', interface])
            
            cmd.extend(['metric', str(metric)])
            
            if persistent:
                cmd.insert(1, '-p')  # Make route persistent
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Save to custom routes if successful
                route_info = {
                    'destination': destination,
                    'netmask': netmask,
                    'gateway': gateway,
                    'interface': interface,
                    'metric': metric,
                    'persistent': persistent,
                    'created': datetime.now().isoformat()
                }
                
                self.custom_routes.append(route_info)
                self.save_routes()
                
                return True, "Route added successfully"
            else:
                return False, f"Failed to add route: {result.stderr}"
                
        except Exception as e:
            return False, f"Route add error: {str(e)}"
    
    def remove_static_route(self, destination, netmask=None, gateway=None):
        """Remove a static route."""
        try:
            cmd = ['route', 'delete', destination]
            
            if netmask:
                cmd.extend(['mask', netmask])
            
            if gateway:
                cmd.append(gateway)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Remove from custom routes
                self.custom_routes = [
                    r for r in self.custom_routes 
                    if not (r['destination'] == destination and 
                           (not netmask or r['netmask'] == netmask) and
                           (not gateway or r['gateway'] == gateway))
                ]
                self.save_routes()
                
                return True, "Route removed successfully"
            else:
                return False, f"Failed to remove route: {result.stderr}"
                
        except Exception as e:
            return False, f"Route remove error: {str(e)}"
    
    def get_default_gateways(self):
        """Get all default gateways."""
        routes = self.get_routing_table()
        return [r for r in routes if r['destination'] == '0.0.0.0' and r['netmask'] == '0.0.0.0']
    
    def add_default_gateway(self, gateway, interface=None, metric=1):
        """Add an additional default gateway."""
        return self.add_static_route('0.0.0.0', '0.0.0.0', gateway, interface, metric)
    
    def remove_default_gateway(self, gateway):
        """Remove a default gateway."""
        return self.remove_static_route('0.0.0.0', '0.0.0.0', gateway)

class NetworkMonitor:
    """Efficient real-time network monitoring and statistics."""
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.monitoring = False
        self.monitor_thread = None
        self._last_stats = None
        self._last_time = 0
        self.init_database()
    
    def get_current_stats_fast(self):
        """Get current network statistics quickly."""
        try:
            import psutil
            
            # Get network I/O counters
            net_io = psutil.net_io_counters(pernic=True)
            total_stats = psutil.net_io_counters()
            
            current_time = time.time()
            
            # Calculate rates if we have previous data
            rates = {}
            if self._last_stats and self._last_time:
                time_diff = current_time - self._last_time
                if time_diff > 0:
                    rates = {
                        'bytes_sent_rate': (total_stats.bytes_sent - self._last_stats.bytes_sent) / time_diff,
                        'bytes_recv_rate': (total_stats.bytes_recv - self._last_stats.bytes_recv) / time_diff,
                        'packets_sent_rate': (total_stats.packets_sent - self._last_stats.packets_sent) / time_diff,
                        'packets_recv_rate': (total_stats.packets_recv - self._last_stats.packets_recv) / time_diff
                    }
            
            # Store for next calculation
            self._last_stats = total_stats
            self._last_time = current_time
            
            return {
                'total': {
                    'bytes_sent': total_stats.bytes_sent,
                    'bytes_recv': total_stats.bytes_recv,
                    'packets_sent': total_stats.packets_sent,
                    'packets_recv': total_stats.packets_recv,
                    'errors_in': total_stats.errin,
                    'errors_out': total_stats.errout,
                    **rates
                },
                'timestamp': current_time
            }
            
        except ImportError:
            # Fallback to Windows-specific method
            return self._get_stats_fallback()
        except Exception as e:
            return self._get_stats_fallback()
    
    def test_connectivity_fast(self, hosts=None, timeout=2):
        """Fast connectivity test."""
        if hosts is None:
            hosts = ['8.8.8.8', '1.1.1.1', 'google.com']
        
        results = []
        for host in hosts:
            try:
                start_time = time.time()
                
                # Use socket for faster testing
                if self._is_ip_address(host):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    try:
                        result = sock.connect_ex((host, 53))  # DNS port
                        success = result == 0
                        response_time = (time.time() - start_time) * 1000
                    finally:
                        sock.close()
                else:
                    # DNS resolution test
                    try:
                        socket.gethostbyname(host)
                        success = True
                        response_time = (time.time() - start_time) * 1000
                    except socket.gaierror:
                        success = False
                        response_time = timeout * 1000
                
                results.append({
                    'host': host,
                    'success': success,
                    'response_time': round(response_time, 1),
                    'error': None if success else 'Connection failed'
                })
                
            except Exception as e:
                results.append({
                    'host': host,
                    'success': False,
                    'response_time': 0,
                    'error': str(e)
                })
        
        return results
    
    def _is_ip_address(self, host):
        """Check if host is an IP address."""
        try:
            socket.inet_aton(host)
            return True
        except socket.error:
            return False
            
    def _get_stats_fallback(self):
        """Fallback method for getting basic network statistics."""
        return {
            'total': {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'errors_in': 0,
                'errors_out': 0
            },
            'timestamp': time.time()
        }
    
    def save_network_stats_async(self, stats_data):
        """Save network statistics asynchronously."""
        try:
            current_time = time.time()
            if current_time - self._last_time < 30:  # Only save every 30 seconds
                return True
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if 'total' in stats_data:
                total = stats_data['total']
                cursor.execute('''
                    INSERT INTO network_stats 
                    (adapter_name, bytes_sent, bytes_received, packets_sent, packets_received, errors_in, errors_out)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'Total',
                    total.get('bytes_sent', 0),
                    total.get('bytes_recv', 0),
                    total.get('packets_sent', 0),
                    total.get('packets_recv', 0),
                    total.get('errors_in', 0),
                    total.get('errors_out', 0)
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception:
            return False
    
    def init_database(self):
        """Initialize monitoring database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables for monitoring data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    adapter_name TEXT,
                    bytes_sent INTEGER,
                    bytes_received INTEGER,
                    packets_sent INTEGER,
                    packets_received INTEGER,
                    errors_in INTEGER,
                    errors_out INTEGER,
                    drops_in INTEGER,
                    drops_out INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target_host TEXT,
                    test_type TEXT,
                    success BOOLEAN,
                    response_time REAL,
                    details TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS speed_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    test_type TEXT,
                    download_speed REAL,
                    upload_speed REAL,
                    latency REAL,
                    server_info TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def start_monitoring(self, interval=30):
        """Start real-time network monitoring."""
        if self.monitoring:
            return False, "Monitoring already running"
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        return True, "Monitoring started"
    
    def stop_monitoring(self):
        """Stop network monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        return True, "Monitoring stopped"
    
    def _monitor_loop(self, interval):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Collect network statistics
                stats = self._collect_network_stats()
                self._save_network_stats(stats)
                
                # Perform connectivity tests
                if len(stats) > 0:  # Only test if we have active adapters
                    self._perform_connectivity_tests()
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def _collect_network_stats(self):
        """Collect current network statistics."""
        stats = []
        
        try:
            # Use PowerShell to get network adapter statistics
            ps_cmd = '''
            Get-NetAdapterStatistics | Select-Object Name, BytesSent, BytesReceived, 
            PacketsSent, PacketsReceived, InboundDiscardedPackets, OutboundDiscardedPackets |
            ConvertTo-Json
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if not isinstance(data, list):
                    data = [data]
                
                for adapter_stats in data:
                    stats.append({
                        'adapter_name': adapter_stats.get('Name', ''),
                        'bytes_sent': adapter_stats.get('BytesSent', 0),
                        'bytes_received': adapter_stats.get('BytesReceived', 0),
                        'packets_sent': adapter_stats.get('PacketsSent', 0),
                        'packets_received': adapter_stats.get('PacketsReceived', 0),
                        'errors_in': 0,  # Not available in basic stats
                        'errors_out': 0,
                        'drops_in': adapter_stats.get('InboundDiscardedPackets', 0),
                        'drops_out': adapter_stats.get('OutboundDiscardedPackets', 0)
                    })
            
        except Exception as e:
            print(f"Stats collection error: {e}")
        
        return stats
    
    def _save_network_stats(self, stats):
        """Save network statistics to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for stat in stats:
                cursor.execute('''
                    INSERT INTO network_stats 
                    (adapter_name, bytes_sent, bytes_received, packets_sent, packets_received,
                     errors_in, errors_out, drops_in, drops_out)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stat['adapter_name'], stat['bytes_sent'], stat['bytes_received'],
                    stat['packets_sent'], stat['packets_received'], stat['errors_in'],
                    stat['errors_out'], stat['drops_in'], stat['drops_out']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Stats save error: {e}")
    
    def _perform_connectivity_tests(self):
        """Perform periodic connectivity tests."""
        test_hosts = ['8.8.8.8', '1.1.1.1', 'google.com']
        
        for host in test_hosts:
            try:
                start_time = time.time()
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '3000', host],
                    capture_output=True, text=True
                )
                end_time = time.time()
                
                success = result.returncode == 0
                response_time = (end_time - start_time) * 1000 if success else None
                
                self._save_connectivity_test(host, 'ping', success, response_time, result.stdout)
                
            except Exception:
                self._save_connectivity_test(host, 'ping', False, None, 'Test failed')
    
    def _save_connectivity_test(self, host, test_type, success, response_time, details):
        """Save connectivity test result."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO connection_tests (target_host, test_type, success, response_time, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (host, test_type, success, response_time, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Connectivity test save error: {e}")
    
    def get_network_stats(self, adapter_name=None, hours=24):
        """Get network statistics for specified time period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            if adapter_name:
                cursor.execute('''
                    SELECT * FROM network_stats 
                    WHERE adapter_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (adapter_name, since))
            else:
                cursor.execute('''
                    SELECT * FROM network_stats 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (since,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Stats retrieval error: {e}")
            return []
    
    def get_connectivity_history(self, hours=24):
        """Get connectivity test history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT * FROM connection_tests 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Connectivity history error: {e}")
            return []
    
    def get_speed_test_history(self, days=7):
        """Get speed test history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM speed_tests 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Speed test history error: {e}")
            return []
    
    def save_speed_test(self, test_type, download_speed, upload_speed=None, latency=None, server_info=None):
        """Save speed test result."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO speed_tests (test_type, download_speed, upload_speed, latency, server_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (test_type, download_speed, upload_speed, latency, server_info))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Speed test save error: {e}")
            return False
    
    def cleanup_old_data(self, days=30):
        """Clean up old monitoring data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = datetime.now() - timedelta(days=days)
            
            cursor.execute('DELETE FROM network_stats WHERE timestamp < ?', (cutoff,))
            cursor.execute('DELETE FROM connection_tests WHERE timestamp < ?', (cutoff,))
            cursor.execute('DELETE FROM speed_tests WHERE timestamp < ?', (cutoff,))
            
            conn.commit()
            conn.close()
            
            return True, f"Cleaned up data older than {days} days"
            
        except Exception as e:
            return False, f"Cleanup error: {e}"