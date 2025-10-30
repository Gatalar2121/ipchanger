#!/usr/bin/env python3
"""Enhanced GUI for Network IP Changer v2.0.0."""

import json
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QLocale
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
        QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
        QProgressBar, QSplitter, QTreeWidget, QTreeWidgetItem,
        QCheckBox, QSpinBox, QMessageBox, QFileDialog, QListWidget,
        QRadioButton, QButtonGroup, QInputDialog, QHeaderView
    )
    from PySide6.QtGui import QFont, QIcon, QPixmap
except ImportError as exc:
    raise SystemExit("PySide6 is required to run the enhanced GUI.") from exc

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    matplotlib_available = True
except ImportError:
    matplotlib_available = False
    plt = None
    FigureCanvas = None
    Figure = None

from ipchanger_enhanced import (
    PROFILES_PATH,
    get_adapter_config,
    list_adapters,
    log_message,
    run_netsh,
    set_language,
    tr,
    __version__,
    NetworkTester,
)

I18N_DIR = Path(__file__).parent / "i18n"
TRANSLATIONS: dict[str, dict[str, str]] = {}
CURRENT_LANG = "en"


def load_languages() -> None:
    """Load translation files and detect the system language."""

    TRANSLATIONS.clear()
    TRANSLATIONS["en"] = {
        "title": "Network IP Changer v2.0.0",
        "language": "Language:",
        "network_interface": "Network Interface:",
        "refresh_interfaces": "Refresh Interfaces",
        "network_configuration": "Network Configuration",
        "network_testing": "Network Testing",
        "network_monitoring": "Network Monitoring",
        "start_monitoring": "Start Monitoring",
        "stop_monitoring": "Stop Monitoring",
        "current_statistics": "Current Statistics",
        "connectivity_status": "Connectivity Status",
        "bytes_sent": "Bytes Sent:",
        "bytes_received": "Bytes Received:",
        "packets_sent": "Packets Sent:",
        "packets_received": "Packets Received:"
    }

    if I18N_DIR.exists():
        for lang_file in I18N_DIR.glob("*.json"):
            try:
                lang_code = lang_file.stem
                with lang_file.open("r", encoding="utf-8") as fh:
                    TRANSLATIONS[lang_code] = json.load(fh)
            except Exception as exc:
                print(f"Failed to load language {lang_file}: {exc}")

    try:
        system_locale = QLocale.system().name()[:2]
        if system_locale in TRANSLATIONS:
            global CURRENT_LANG
            CURRENT_LANG = system_locale
    except Exception:
        pass


def tr_gui(key: str, default: Optional[str] = None) -> str:
    """Translate GUI text with fallbacks to English and shared translations."""

    if default is None:
        default = key

    lang_map = TRANSLATIONS.get(CURRENT_LANG, {})
    if key in lang_map:
        return lang_map[key]

    fallback_map = TRANSLATIONS.get("en", {})
    if key in fallback_map:
        return fallback_map[key]

    try:
        translated = tr(key)
        if translated and translated != key:
            return translated
    except Exception:
        pass

    return default


load_languages()


class NetworkMonitorThread(QThread):
    """Background thread that gathers network statistics safely."""

    stats_updated = Signal(dict)
    connectivity_updated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.stats_history: deque[dict[str, object]] = deque(maxlen=30)
        self.last_connectivity = 0.0
        self.psutil_available = self._check_psutil()

    def _check_psutil(self) -> bool:
        try:
            import psutil  # noqa: F401
            return True
        except ImportError:
            return False

    def run(self) -> None:
        self.running = True
        self.stats_history.clear()
        self.last_connectivity = 0.0

        while self.running:
            try:
                stats = self.get_safe_stats()
                if stats:
                    self.stats_history.append(stats)
                    gui_stats = {
                        "timestamp": stats.get("timestamp"),
                        "bytes_sent": int(stats.get("bytes_sent", 0)),
                        "bytes_received": int(stats.get("bytes_received", 0)),
                        "packets_sent": int(stats.get("packets_sent", 0)),
                        "packets_received": int(stats.get("packets_received", 0)),
                        "history": list(self.stats_history),
                    }
                    try:
                        self.stats_updated.emit(gui_stats)
                    except RuntimeError:
                        pass

                current_time = time.time()
                if current_time - self.last_connectivity > 15:
                    try:
                        connectivity = self.test_simple_connectivity()
                        if connectivity:
                            try:
                                self.connectivity_updated.emit(connectivity)
                            except RuntimeError:
                                pass
                    except Exception:
                        pass
                    self.last_connectivity = current_time

                self._sleep_with_checks(5000)
            except Exception:
                self._sleep_with_checks(5000)

    def _sleep_with_checks(self, total_ms: int) -> None:
        step = 100
        iterations = max(1, total_ms // step)
        for _ in range(iterations):
            if not self.running:
                break
            self.msleep(step)

    def get_safe_stats(self) -> dict[str, object]:
        timestamp = datetime.now().strftime("%H:%M:%S")

        if self.psutil_available:
            try:
                import psutil

                net_io = psutil.net_io_counters()
                return {
                    "timestamp": timestamp,
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_received": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_received": net_io.packets_recv,
                }
            except Exception as exc:
                print(f"psutil error: {exc}")

        return self.get_dummy_stats(timestamp)

    def get_dummy_stats(self, timestamp: Optional[str] = None) -> dict[str, object]:
        import random

        return {
            "timestamp": timestamp or datetime.now().strftime("%H:%M:%S"),
            "bytes_sent": random.randint(1_000_000, 5_000_000),
            "bytes_received": random.randint(2_000_000, 8_000_000),
            "packets_sent": random.randint(1_000, 5_000),
            "packets_received": random.randint(2_000, 8_000),
        }

    def test_simple_connectivity(self) -> dict[str, dict[str, object]]:
        import socket

        results: dict[str, dict[str, object]] = {}

        for host, ip in [("google.com", "8.8.8.8"), ("cloudflare", "1.1.1.1")]:
            try:
                start_time = time.time()
                socket.create_connection((ip, 53), timeout=2)
                response_time = (time.time() - start_time) * 1000
                results[host] = {"success": True, "time": response_time}
            except Exception:
                results[host] = {"success": False, "time": 0}

        results.setdefault("8.8.8.8", results.get("google.com", {"success": False, "time": 0}))
        results.setdefault("1.1.1.1", results.get("cloudflare", {"success": False, "time": 0}))
        return results

    def stop(self) -> None:
        self.running = False
        if self.isRunning():
            self.wait(3000)

class NetworkChart(QWidget):
    """Network statistics chart widget."""
    
    def __init__(self):
        super().__init__()
        self.figure = None
        self.canvas = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize chart UI."""
        layout = QVBoxLayout()
        
        if matplotlib_available:
            self.figure = Figure(figsize=(8, 4))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
            
            # Initialize with empty chart
            self.update_chart([])
        else:
            label = QLabel("Matplotlib not available - install for charts")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        
        self.setLayout(layout)
    
    def update_chart(self, data):
        """Update chart with new data."""
        if not matplotlib_available or not self.figure:
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if data and len(data) > 0:
                # Plot network statistics safely
                times = []
                bytes_sent = []
                bytes_received = []
                
                for d in data:
                    if isinstance(d, dict):
                        times.append(d.get('timestamp', ''))
                        # Convert to KB for better readability
                        bytes_sent.append(d.get('bytes_sent', 0) / 1024)
                        bytes_received.append(d.get('bytes_received', 0) / 1024)
                
                if len(times) > 0:
                    ax.plot(times, bytes_sent, label=tr_gui("chart_kb_sent", "KB Sent"), color='blue', marker='o', markersize=2)
                    ax.plot(times, bytes_received, label=tr_gui("chart_kb_received", "KB Received"), color='green', marker='s', markersize=2)
                    ax.set_title(tr_gui("chart_traffic_title", "Network Traffic Over Time"))
                    ax.set_xlabel(tr_gui("chart_axis_time", "Time"))
                    ax.set_ylabel(tr_gui("chart_axis_data", "Data (KB)"))
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    # Format x-axis labels to avoid crowding
                    if len(times) > 10:
                        step = max(1, len(times) // 5)  # Show max 5 labels
                        ax.set_xticks(range(0, len(times), step))
                        ax.set_xticklabels([times[i] for i in range(0, len(times), step)])
                    
                    # Rotate x-axis labels
                    for label in ax.get_xticklabels():
                        label.set_rotation(45)
                        label.set_fontsize(8)
                else:
                    ax.text(0.5, 0.5, tr_gui("chart_no_valid_data", "No valid data"), ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(tr_gui("chart_statistics_title", "Network Statistics"))
            else:
                ax.text(0.5, 0.5, tr_gui("chart_waiting", "Waiting for data..."), ha='center', va='center', transform=ax.transAxes)
                ax.set_title(tr_gui("chart_statistics_title", "Network Statistics"))
                ax.grid(True, alpha=0.3)
            
            # Adjust layout to prevent label cutoff
            self.figure.tight_layout()
            
        except Exception as e:
            print(f"Chart rendering error: {e}")
            # Create a simple error chart
            try:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Chart Error: {str(e)[:50]}...', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Chart Error')
            except:
                pass
        
        self.canvas.draw()

class OriginalNetworkTab(QWidget):
    """Original v1.0.0 compatible network configuration tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_profiles()
    
    def init_ui(self):
        """Initialize the original interface."""
        layout = QVBoxLayout()
        
        # Interface selection
        self.interface_group = QGroupBox()
        interface_layout = QFormLayout()
        
        self.interface_label = QLabel()
        self.interface_combo = QComboBox()
        interface_layout.addRow(self.interface_label, self.interface_combo)
        
        self.refresh_btn = QPushButton()
        interface_layout.addRow(QLabel(""), self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh_interfaces)
        
        self.interface_group.setLayout(interface_layout)
        
        # Current settings display
        self.current_group = QGroupBox()
        current_layout = QVBoxLayout()
        self.current_text = QTextEdit()
        self.current_text.setMaximumHeight(100)
        self.current_text.setReadOnly(True)
        current_layout.addWidget(self.current_text)
        self.current_group.setLayout(current_layout)
        
        # Configuration section
        self.config_group = QGroupBox()
        config_layout = QFormLayout()
        
        # DHCP/Static selection
        self.dhcp_radio = QRadioButton()
        self.static_radio = QRadioButton()
        self.dhcp_radio.setChecked(True)  # Default to DHCP
        
        # Static IP fields
        self.ip_edit = QLineEdit()
        self.mask_edit = QLineEdit()
        self.gateway_edit = QLineEdit()
        self.dns_edit = QLineEdit()
        
        # Set default values
        self.mask_edit.setText("255.255.255.0")
        self.dns_edit.setText("8.8.8.8, 8.8.4.4")
        
        config_layout.addRow(QLabel(""), self.dhcp_radio)
        config_layout.addRow(QLabel(""), self.static_radio)
        
        self.ip_label = QLabel()
        self.mask_label = QLabel()
        self.gateway_label = QLabel()
        self.dns_label = QLabel()
        config_layout.addRow(self.ip_label, self.ip_edit)
        config_layout.addRow(self.mask_label, self.mask_edit)
        config_layout.addRow(self.gateway_label, self.gateway_edit)
        config_layout.addRow(self.dns_label, self.dns_edit)
        
        self.config_group.setLayout(config_layout)
        
        # Apply button
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_configuration)
        
        # Profile management
        self.profile_group = QGroupBox()
        profile_layout = QVBoxLayout()
        
        profile_buttons_layout = QHBoxLayout()
        self.save_profile_btn = QPushButton()
        self.load_profile_btn = QPushButton()
        self.delete_profile_btn = QPushButton()
        
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.load_profile_btn.clicked.connect(self.load_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        
        profile_buttons_layout.addWidget(self.save_profile_btn)
        profile_buttons_layout.addWidget(self.load_profile_btn)
        profile_buttons_layout.addWidget(self.delete_profile_btn)
        
        self.import_profiles_btn = QPushButton()
        self.export_profiles_btn = QPushButton()
        self.import_profiles_btn.clicked.connect(self.import_profiles)
        self.export_profiles_btn.clicked.connect(self.export_profiles)

        profile_transfer_layout = QHBoxLayout()
        profile_transfer_layout.addWidget(self.import_profiles_btn)
        profile_transfer_layout.addWidget(self.export_profiles_btn)

        self.profile_list = QListWidget()
        self.profile_list.currentItemChanged.connect(self.update_profile_preview)
        self.profile_preview_label = QLabel()
        self.profile_preview = QTextEdit()
        self.profile_preview.setReadOnly(True)
        self.profile_preview.setMinimumHeight(90)

        profile_layout.addWidget(self.profile_list)
        profile_layout.addLayout(profile_buttons_layout)
        profile_layout.addLayout(profile_transfer_layout)
        profile_layout.addWidget(self.profile_preview_label)
        profile_layout.addWidget(self.profile_preview)
        self.profile_group.setLayout(profile_layout)
        
        # Add all sections to main layout
        layout.addWidget(self.interface_group)
        layout.addWidget(self.current_group)
        layout.addWidget(self.config_group)
        layout.addWidget(self.apply_btn)
        layout.addWidget(self.profile_group)
        
        self.setLayout(layout)
        
        # Connect signals
        self.interface_combo.currentTextChanged.connect(self.show_current_config)
        self.dhcp_radio.toggled.connect(self.toggle_static_fields)

        # Apply initial translations
        self.refresh_language()
        
    def refresh_language(self):
        """Refresh localized strings for classic tab."""
        self.interface_group.setTitle(tr_gui("network_interface", "Network Interface"))
        self.interface_label.setText(tr_gui("network_interface", "Network Interface:"))
        self.refresh_btn.setText(tr_gui("refresh_interfaces", "Refresh Interfaces"))
        
        self.current_group.setTitle(tr_gui("current_settings", "Current Settings"))
        self.config_group.setTitle(tr_gui("configuration", "Configuration"))
        self.dhcp_radio.setText(tr_gui("dhcp_option", "Obtain IP automatically (DHCP)"))
        self.static_radio.setText(tr_gui("static_option", "Use the following IP address"))
        self.ip_label.setText(tr_gui("ip_address", "IP Address:"))
        self.mask_label.setText(tr_gui("subnet_mask", "Subnet Mask:"))
        self.gateway_label.setText(tr_gui("default_gateway", "Default Gateway:"))
        self.dns_label.setText(tr_gui("dns_servers", "DNS Servers:"))
        self.apply_btn.setText(tr_gui("apply_configuration", "Apply"))
        
        self.profile_group.setTitle(tr_gui("profiles", "Profiles"))
        self.save_profile_btn.setText(tr_gui("save_profile", "Save Profile"))
        self.load_profile_btn.setText(tr_gui("load_profile", "Load Profile"))
        self.delete_profile_btn.setText(tr_gui("delete_profile", "Delete Profile"))
        self.import_profiles_btn.setText(tr_gui("import_profiles", "Import Profiles"))
        self.export_profiles_btn.setText(tr_gui("export_profiles", "Export Profiles"))
        self.profile_preview_label.setText(tr_gui("profile_preview", "Profile Preview"))
        self.profile_preview.setPlaceholderText(tr_gui("profile_preview", "Profile Preview"))

        # Initial setup
        self.refresh_interfaces()
        self.toggle_static_fields()
    
    def refresh_interfaces(self):
        """Refresh network interfaces list."""
        self.interface_combo.clear()
        adapters = list_adapters()
        
        for adapter in adapters:
            self.interface_combo.addItem(adapter["name"])
        
        if adapters:
            self.show_current_config()
    
    def show_current_config(self):
        """Display current configuration of selected adapter."""
        adapter_name = self.interface_combo.currentText()
        if not adapter_name:
            return
        
        config = get_adapter_config(adapter_name)
        
        yes_text = tr_gui("yes", "Yes")
        no_text = tr_gui("no", "No")
        not_configured = tr_gui("not_configured", "Not configured")
        dhcp_label = tr_gui("dhcp_enabled", "DHCP Enabled:")
        header = tr_gui("current_config_header", "Current Configuration for '{0}':").format(adapter_name)
        ip_label = tr_gui("ip_address", "IP Address:")
        mask_label = tr_gui("subnet_mask", "Subnet Mask:")
        gateway_label = tr_gui("default_gateway", "Default Gateway:")
        dns_label = tr_gui("dns_servers", "DNS Servers:")

        dns_value = ', '.join(config.get('dns', [])) or not_configured
        info_lines = [
            header,
            f"{dhcp_label} {yes_text if config['dhcp'] else no_text}",
            f"{ip_label} {config.get('ip', not_configured)}",
            f"{mask_label} {config.get('mask', not_configured)}",
            f"{gateway_label} {config.get('gateway', not_configured)}",
            f"{dns_label} {dns_value}"
        ]

        self.current_text.setPlainText("\n".join(info_lines))
        
        # Update form fields with current values
        if not config['dhcp']:
            self.static_radio.setChecked(True)
            self.ip_edit.setText(config.get('ip', ''))
            self.mask_edit.setText(config.get('mask', '255.255.255.0'))
            self.gateway_edit.setText(config.get('gateway', ''))
            self.dns_edit.setText(', '.join(config.get('dns', [])))
        else:
            self.dhcp_radio.setChecked(True)
    
    def toggle_static_fields(self):
        """Enable/disable static IP fields based on selection."""
        static_selected = self.static_radio.isChecked()
        
        self.ip_edit.setEnabled(static_selected)
        self.mask_edit.setEnabled(static_selected)
        self.gateway_edit.setEnabled(static_selected)
        self.dns_edit.setEnabled(static_selected)
    
    def apply_configuration(self):
        """Apply network configuration."""
        adapter_name = self.interface_combo.currentText()
        if not adapter_name:
            QMessageBox.warning(self, tr("failed"), tr("no_adapter"))
            return
        
        try:
            if self.dhcp_radio.isChecked():
                # Apply DHCP configuration
                rc1, out1, err1 = run_netsh(["interface", "ip", "set", "address", f'name="{adapter_name}"', "dhcp"])
                rc2, out2, err2 = run_netsh(["interface", "ip", "set", "dns", f'name="{adapter_name}"', "dhcp"])
                
                if rc1 == 0 and rc2 == 0:
                    QMessageBox.information(self, tr("success"), tr("ready"))
                    log_message(f"DHCP configured for {adapter_name}")
                    self.show_current_config()
                else:
                    QMessageBox.critical(self, tr("failed"), f"Configuration failed: {err1 or err2}")
                    log_message(f"DHCP configuration failed: {err1 or err2}", "ERROR")
            
            else:
                # Apply static configuration
                ip = self.ip_edit.text().strip()
                mask = self.mask_edit.text().strip()
                gateway = self.gateway_edit.text().strip()
                dns_text = self.dns_edit.text().strip()
                
                if not ip:
                    QMessageBox.warning(self, tr("failed"), "IP address is required for static configuration")
                    return
                
                # Apply IP configuration
                cmd = ["interface", "ip", "set", "address", f'name="{adapter_name}"', "static", ip]
                if mask:
                    cmd.append(mask)
                if gateway:
                    cmd.append(gateway)
                
                rc, out, err = run_netsh(cmd)
                
                if rc == 0:
                    # Apply DNS if provided
                    if dns_text:
                        dns_servers = [dns.strip() for dns in dns_text.split(',')]
                        for i, dns_server in enumerate(dns_servers):
                            if dns_server:
                                dns_cmd = ["interface", "ip", "set", "dns", f'name="{adapter_name}"']
                                if i == 0:
                                    dns_cmd.extend(["static", dns_server])
                                else:
                                    dns_cmd.extend(["static", dns_server, f"index={i+1}"])
                                
                                run_netsh(dns_cmd)
                    
                    QMessageBox.information(self, tr("success"), tr("ready"))
                    log_message(f"Static IP {ip} configured for {adapter_name}")
                    self.show_current_config()
                else:
                    QMessageBox.critical(self, tr("failed"), f"Configuration failed: {err}")
                    log_message(f"Static IP configuration failed: {err}", "ERROR")
        
        except Exception as e:
            QMessageBox.critical(self, tr("failed"), f"Unexpected error: {str(e)}")
            log_message(f"Configuration error: {str(e)}", "ERROR")
    
    def load_profiles(self):
        """Load saved profiles into the list."""
        self.profile_list.clear()
        
        try:
            if PROFILES_PATH.exists():
                import json
                with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                for profile_name in profiles.keys():
                    self.profile_list.addItem(profile_name)

                if profiles:
                    self.profile_list.setCurrentRow(0)
                else:
                    self.profile_preview.clear()
            else:
                self.profile_preview.clear()
        except Exception:
            pass
    
    def save_profile(self):
        """Save current configuration as a profile."""
        adapter_name = self.interface_combo.currentText()
        if not adapter_name:
            QMessageBox.warning(self, tr("failed"), tr("no_adapter"))
            return
        
        profile_name, ok = QInputDialog.getText(self, tr("save_profile"), "Profile name:")
        if not ok or not profile_name:
            return
        
        try:
            # Get current configuration
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
                import json
                with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            
            # Add new profile
            profiles[profile_name] = profile
            
            # Save profiles
            import json
            with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2)
            
            QMessageBox.information(self, tr("success"), f"Profile '{profile_name}' saved")
            log_message(f"Profile '{profile_name}' saved")
            self.load_profiles()
            
        except Exception as e:
            QMessageBox.critical(self, tr("failed"), f"Failed to save profile: {str(e)}")
            log_message(f"Failed to save profile '{profile_name}': {str(e)}", "ERROR")
    
    def import_profiles(self):
        """Import profiles from a JSON file."""
        default_dir = str(PROFILES_PATH.parent)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr_gui("import_profiles", "Import Profiles"),
            default_dir,
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                incoming = json.load(fh)
            if not isinstance(incoming, dict):
                raise ValueError("Invalid profile file format")

            existing = {}
            if PROFILES_PATH.exists():
                with open(PROFILES_PATH, "r", encoding="utf-8") as fh:
                    existing = json.load(fh)

            existing.update(incoming)
            with open(PROFILES_PATH, "w", encoding="utf-8") as fh:
                json.dump(existing, fh, indent=2)

            self.load_profiles()
            QMessageBox.information(self, tr("success"), tr("imported"))
        except Exception as exc:
            QMessageBox.critical(self, tr("failed"), str(exc))

    def export_profiles(self):
        """Export profiles to a JSON file."""
        default_path = str(PROFILES_PATH.parent / "profiles_export.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr_gui("export_profiles", "Export Profiles"),
            default_path,
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            profiles_data = {}
            if PROFILES_PATH.exists():
                with open(PROFILES_PATH, "r", encoding="utf-8") as fh:
                    profiles_data = json.load(fh)

            with open(file_path, "w", encoding="utf-8") as fh:
                json.dump(profiles_data, fh, indent=2)

            QMessageBox.information(self, tr("success"), tr("exported"))
        except Exception as exc:
            QMessageBox.critical(self, tr("failed"), str(exc))

    def update_profile_preview(self, current, _previous=None):
        """Display details of the selected profile."""
        if not current:
            self.profile_preview.clear()
            return

        profile_name = current.text()
        if not profile_name:
            self.profile_preview.clear()
            return

        try:
            profiles = {}
            if PROFILES_PATH.exists():
                import json
                with open(PROFILES_PATH, 'r', encoding='utf-8') as fh:
                    profiles = json.load(fh)
            profile = profiles.get(profile_name)
            if not profile:
                self.profile_preview.clear()
                return

            mode_text = tr_gui("dhcp_option", "Obtain IP automatically (DHCP)") if profile.get("mode") == "dhcp" else tr_gui("static_option", "Use the following IP address")
            ip_text = profile.get("ip") or tr_gui("not_configured", "Not configured")
            mask_text = profile.get("mask") or tr_gui("not_configured", "Not configured")
            gateway_text = profile.get("gateway") or tr_gui("not_configured", "Not configured")
            dns_entries = profile.get("dns", [])
            dns_text = ", ".join(dns_entries) if dns_entries else tr_gui("not_configured", "Not configured")

            details = [
                f"{tr_gui('profiles', 'Profiles')}: {profile_name}",
                f"{tr_gui('mode', 'Mode:')} {mode_text}",
                f"{tr_gui('ip_address', 'IP Address:')} {ip_text}",
                f"{tr_gui('subnet_mask', 'Subnet Mask:')} {mask_text}",
                f"{tr_gui('default_gateway', 'Default Gateway:')} {gateway_text}",
                f"{tr_gui('dns_servers', 'DNS Servers:')} {dns_text}",
            ]

            self.profile_preview.setPlainText("\n".join(details))
        except Exception as exc:
            self.profile_preview.setPlainText(str(exc))

    def load_profile(self):
        """Load selected profile."""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, tr("failed"), "Please select a profile")
            return
        
        profile_name = current_item.text()
        
        try:
            if not PROFILES_PATH.exists():
                QMessageBox.warning(self, tr("failed"), "No profiles file found")
                return
            
            import json
            with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            
            if profile_name not in profiles:
                QMessageBox.warning(self, tr("failed"), f"Profile '{profile_name}' not found")
                return
            
            profile = profiles[profile_name]
            
            # Apply profile to form
            if profile.get('mode') == 'dhcp':
                self.dhcp_radio.setChecked(True)
            else:
                self.static_radio.setChecked(True)
                self.ip_edit.setText(profile.get('ip', ''))
                self.mask_edit.setText(profile.get('mask', ''))
                self.gateway_edit.setText(profile.get('gateway', ''))
                dns_list = profile.get('dns', [])
                self.dns_edit.setText(', '.join(dns_list) if dns_list else '')
            
            QMessageBox.information(self, tr("success"), f"Profile '{profile_name}' loaded")
            
        except Exception as e:
            QMessageBox.critical(self, tr("failed"), f"Failed to load profile: {str(e)}")
    
    def delete_profile(self):
        """Delete selected profile."""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, tr("failed"), "Please select a profile")
            return
        
        profile_name = current_item.text()
        
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import json
                with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                if profile_name in profiles:
                    del profiles[profile_name]
                    
                    with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
                        json.dump(profiles, f, indent=2)
                    
                    QMessageBox.information(self, tr("success"), f"Profile '{profile_name}' deleted")
                    self.load_profiles()
                
            except Exception as e:
                QMessageBox.critical(self, tr("failed"), f"Failed to delete profile: {str(e)}")

class NetworkTestingTab(QWidget):
    """Network testing and diagnostics tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize testing interface."""
        layout = QVBoxLayout()
        
        # Quick tests section
        self.quick_group = QGroupBox()
        quick_layout = QHBoxLayout()
        
        self.ping_btn = QPushButton()
        self.speed_btn = QPushButton()
        self.dns_btn = QPushButton()
        self.connectivity_btn = QPushButton()
        
        self.ping_btn.clicked.connect(self.run_ping_test)
        self.speed_btn.clicked.connect(self.run_speed_test)
        self.dns_btn.clicked.connect(self.run_dns_test)
        self.connectivity_btn.clicked.connect(self.run_connectivity_test)
        
        quick_layout.addWidget(self.ping_btn)
        quick_layout.addWidget(self.speed_btn)
        quick_layout.addWidget(self.dns_btn)
        quick_layout.addWidget(self.connectivity_btn)
        self.quick_group.setLayout(quick_layout)
        
        # Results display
        self.results_group = QGroupBox()
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        self.results_group.setLayout(results_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        layout.addWidget(self.quick_group)
        layout.addWidget(self.results_group)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        self.refresh_language()
    
    def run_ping_test(self):
        """Run ping connectivity test."""
        self.results_text.append("=== Ping Test Started ===")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Test common hosts
        test_hosts = ["8.8.8.8", "1.1.1.1", "google.com", "cloudflare.com"]
        
        for host in test_hosts:
            self.results_text.append(f"Testing {host}...")
            result = NetworkTester.ping_host(host, count=3)
            
            if result["success"]:
                lost = result.get("packets_lost", 0)
                avg_time = result.get("avg_time", 0)
                self.results_text.append(f"  ✅ {3-lost}/3 packets successful, avg {avg_time}ms")
            else:
                self.results_text.append(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        
        self.progress_bar.setVisible(False)
        self.results_text.append("=== Ping Test Complete ===\n")
    
    def run_speed_test(self):
        """Run network speed test."""
        self.results_text.append("=== Speed Test Started ===")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        results = NetworkTester.speed_test_basic()
        
        successful_tests = [r for r in results if r["success"]]
        if successful_tests:
            avg_speed = sum(r["speed_mbps"] for r in successful_tests) / len(successful_tests)
            self.results_text.append(f"Average download speed: {avg_speed:.2f} Mbps")
            
            for result in results:
                if result["success"]:
                    self.results_text.append(f"  {result['size_mb']:.1f}MB file: {result['speed_mbps']:.2f} Mbps")
                else:
                    self.results_text.append(f"  Test failed: {result.get('error', 'Unknown error')}")
        else:
            self.results_text.append("All speed tests failed")
        
        self.progress_bar.setVisible(False)
        self.results_text.append("=== Speed Test Complete ===\n")
    
    def run_dns_test(self):
        """Run DNS resolution test."""
        self.results_text.append("=== DNS Test Started ===")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        test_domains = ["google.com", "cloudflare.com", "github.com"]
        dns_servers = ["System DNS", "8.8.8.8", "1.1.1.1", "208.67.222.222"]
        
        for domain in test_domains:
            self.results_text.append(f"Testing {domain}:")
            
            for dns_server in dns_servers:
                if dns_server == "System DNS":
                    result = NetworkTester.test_dns_resolution(domain)
                else:
                    result = NetworkTester.test_dns_resolution(domain, dns_server)
                
                if result["success"]:
                    self.results_text.append(f"  {dns_server}: {result['resolution_time']:.2f}ms")
                else:
                    self.results_text.append(f"  {dns_server}: Failed")
        
        self.progress_bar.setVisible(False)
        self.results_text.append("=== DNS Test Complete ===\n")
    
    def run_connectivity_test(self):
        """Run comprehensive connectivity test."""
        self.results_text.append("=== Full Connectivity Test Started ===")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Run all tests
        self.run_ping_test()
        self.run_dns_test()
        # Skip speed test in full test to save time
        
        self.results_text.append("=== Full Connectivity Test Complete ===\n")
        self.progress_bar.setVisible(False)
    
    def refresh_language(self):
        """Refresh all labels with current language."""
        self.quick_group.setTitle(tr_gui("quick_tests", "Quick Tests"))
        self.results_group.setTitle(tr_gui("test_results", "Test Results"))
        self.ping_btn.setText(tr_gui("ping_test", "Ping Test"))
        self.speed_btn.setText(tr_gui("speed_test", "Speed Test"))
        self.dns_btn.setText(tr_gui("dns_test", "DNS Test"))
        self.connectivity_btn.setText(tr_gui("connectivity_test", "Full Connectivity Test"))

class MonitoringTab(QWidget):
    """Real-time network monitoring tab."""
    
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
        self.stats_group = None
        self.conn_group = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize monitoring interface."""
        layout = QVBoxLayout()
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton(tr_gui("start_monitoring", "Start Monitoring"))
        self.stop_btn = QPushButton(tr_gui("stop_monitoring", "Stop Monitoring"))
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        # Statistics display
        self.stats_group = QGroupBox(tr_gui("current_statistics", "Current Statistics"))
        stats_layout = QFormLayout()
        
        self.bytes_sent_label = QLabel("0")
        self.bytes_received_label = QLabel("0")
        self.packets_sent_label = QLabel("0")
        self.packets_received_label = QLabel("0")
        
        # Create label widgets for row labels so we can update them
        self.bytes_sent_row_label = QLabel(tr_gui("bytes_sent", "Bytes Sent:"))
        self.bytes_received_row_label = QLabel(tr_gui("bytes_received", "Bytes Received:"))
        self.packets_sent_row_label = QLabel(tr_gui("packets_sent", "Packets Sent:"))
        self.packets_received_row_label = QLabel(tr_gui("packets_received", "Packets Received:"))
        
        stats_layout.addRow(self.bytes_sent_row_label, self.bytes_sent_label)
        stats_layout.addRow(self.bytes_received_row_label, self.bytes_received_label)
        stats_layout.addRow(self.packets_sent_row_label, self.packets_sent_label)
        stats_layout.addRow(self.packets_received_row_label, self.packets_received_label)
        
        self.stats_group.setLayout(stats_layout)
        
        # Chart
        self.chart = NetworkChart()
        
        # Connectivity status
        self.conn_group = QGroupBox(tr_gui("connectivity_status", "Connectivity Status"))
        conn_layout = QFormLayout()
        
        self.unknown_status_text = tr_gui("status_unknown", "Unknown")
        self.google_label = QLabel(tr_gui("connectivity_google", "Google:"))
        self.dns_label = QLabel(tr_gui("connectivity_dns", "DNS (8.8.8.8):"))
        self.cloudflare_label = QLabel(tr_gui("connectivity_cloudflare", "Cloudflare:"))
        self.google_status = QLabel(self.unknown_status_text)
        self.dns_status = QLabel(self.unknown_status_text)
        self.cloudflare_status = QLabel(self.unknown_status_text)
        
        conn_layout.addRow(self.google_label, self.google_status)
        conn_layout.addRow(self.dns_label, self.dns_status)
        conn_layout.addRow(self.cloudflare_label, self.cloudflare_status)
        
        self.conn_group.setLayout(conn_layout)
        
        # Layout arrangement
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.stats_group)
        top_layout.addWidget(self.conn_group)
        
        layout.addLayout(control_layout)
        layout.addLayout(top_layout)
        layout.addWidget(self.chart)
        
        self.setLayout(layout)
        self.refresh_language()
    
    def start_monitoring(self):
        """Start network monitoring."""
        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        if not self.monitor_thread:
            self.monitor_thread = NetworkMonitorThread()
            self.monitor_thread.stats_updated.connect(self.update_stats)
            self.monitor_thread.connectivity_updated.connect(self.update_connectivity)

        if self.monitor_thread and not self.monitor_thread.isRunning():
            self.monitor_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_monitoring(self):
        """Stop network monitoring."""
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.deleteLater()
            self.monitor_thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def update_stats(self, stats):
        """Update statistics display and chart."""
        try:
            # Update text labels safely
            self.bytes_sent_label.setText(f"{stats.get('bytes_sent', 0):,}")
            self.bytes_received_label.setText(f"{stats.get('bytes_received', 0):,}")
            self.packets_sent_label.setText(f"{stats.get('packets_sent', 0):,}")
            self.packets_received_label.setText(f"{stats.get('packets_received', 0):,}")
            
            # Update chart with history data safely
            history = stats.get('history', [])
            if history and len(history) > 0:
                try:
                    self.chart.update_chart(history)
                    if hasattr(self.chart, 'canvas') and self.chart.canvas:
                        self.chart.canvas.draw()
                except Exception as chart_error:
                    print(f"Chart update error: {chart_error}")
        except Exception as update_error:
            print(f"Stats update error: {update_error}")
    
    def update_connectivity(self, connectivity):
        """Update connectivity status."""
        google_status = connectivity.get('google.com', {})
        if google_status.get('success'):
            self.google_status.setText(f"✅ {google_status.get('time', 0):.1f}ms")
        else:
            self.google_status.setText(f"❌ {tr_gui('failed', 'Failed')}")
        
        dns_status = connectivity.get('8.8.8.8', {})
        if dns_status.get('success'):
            self.dns_status.setText(f"✅ {dns_status.get('time', 0):.1f}ms")
        else:
            self.dns_status.setText(f"❌ {tr_gui('failed', 'Failed')}")
        
        cloudflare_status = connectivity.get('1.1.1.1', {})
        if cloudflare_status.get('success'):
            self.cloudflare_status.setText(f"✅ {cloudflare_status.get('time', 0):.1f}ms")
        else:
            self.cloudflare_status.setText(f"❌ {tr_gui('failed', 'Failed')}")
    
    def refresh_language(self):
        """Refresh all labels with current language."""
        self.start_btn.setText(tr_gui("start_monitoring", "Start Monitoring"))
        self.stop_btn.setText(tr_gui("stop_monitoring", "Stop Monitoring"))
        if self.stats_group:
            self.stats_group.setTitle(tr_gui("current_statistics", "Current Statistics"))
        if self.conn_group:
            self.conn_group.setTitle(tr_gui("connectivity_status", "Connectivity Status"))
        
        # Update form row labels
        self.bytes_sent_row_label.setText(tr_gui("bytes_sent", "Bytes Sent:"))
        self.bytes_received_row_label.setText(tr_gui("bytes_received", "Bytes Received:"))
        self.packets_sent_row_label.setText(tr_gui("packets_sent", "Packets Sent:"))
        self.packets_received_row_label.setText(tr_gui("packets_received", "Packets Received:"))

        # Update connectivity labels and placeholder statuses
        self.google_label.setText(tr_gui("connectivity_google", "Google:"))
        self.dns_label.setText(tr_gui("connectivity_dns", "DNS (8.8.8.8):"))
        self.cloudflare_label.setText(tr_gui("connectivity_cloudflare", "Cloudflare:"))

        previous_unknown = getattr(self, "unknown_status_text", "Unknown")
        new_unknown = tr_gui("status_unknown", "Unknown")
        self.unknown_status_text = new_unknown

        if self.google_status.text() in ("", previous_unknown):
            self.google_status.setText(new_unknown)
        if self.dns_status.text() in ("", previous_unknown):
            self.dns_status.setText(new_unknown)
        if self.cloudflare_status.text() in ("", previous_unknown):
            self.cloudflare_status.setText(new_unknown)

class EnhancedNetworkGUI(QMainWindow):
    """Enhanced main window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the enhanced GUI."""
        self.setWindowTitle(tr_gui("title", f"Network IP Changer Enhanced v{__version__}"))
        self.setMinimumSize(900, 700)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Language selection at the top
        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        self.lang_label = QLabel(tr_gui("language", "Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(sorted(TRANSLATIONS.keys()))
        self.lang_combo.setCurrentText(CURRENT_LANG)
        self.lang_combo.currentTextChanged.connect(self.change_language)
        
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.network_tab = OriginalNetworkTab()
        self.testing_tab = NetworkTestingTab()
        self.monitoring_tab = MonitoringTab()
        
        self.tab_widget.addTab(self.network_tab, tr_gui("network_configuration", "Network Configuration"))
        self.tab_widget.addTab(self.testing_tab, tr_gui("network_testing", "Network Testing"))
        self.tab_widget.addTab(self.monitoring_tab, tr_gui("network_monitoring", "Network Monitoring"))
        
        layout.addLayout(lang_layout)
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        # Set application icon if available
        if Path("ip.ico").exists():
            self.setWindowIcon(QIcon("ip.ico"))
    
    def change_language(self, lang_code):
        """Change the application language."""
        global CURRENT_LANG
        if lang_code not in TRANSLATIONS:
            lang_code = "en"
            try:
                block = self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentText(lang_code)
            finally:
                self.lang_combo.blockSignals(block)
        CURRENT_LANG = lang_code
        try:
            set_language(CURRENT_LANG)
        except Exception:
            pass
        
        # Update window title
        self.setWindowTitle(tr_gui("title", f"Network IP Changer Enhanced v{__version__}"))
        self.lang_label.setText(tr_gui("language", "Language:"))
        
        # Update tab titles
        self.tab_widget.setTabText(0, tr_gui("network_configuration", "Network Configuration"))
        self.tab_widget.setTabText(1, tr_gui("network_testing", "Network Testing"))
        self.tab_widget.setTabText(2, tr_gui("network_monitoring", "Network Monitoring"))
        
        # Refresh all tab labels
        try:
            self.monitoring_tab.refresh_language()
        except AttributeError:
            pass
        
        try:
            self.testing_tab.refresh_language() 
        except AttributeError:
            pass

        try:
            self.network_tab.refresh_language()
        except AttributeError:
            pass

def create_enhanced_gui():
    """Create and return the enhanced GUI."""
    return EnhancedNetworkGUI()

if __name__ == "__main__":
    # Test the enhanced GUI
    app = QApplication(sys.argv)
    window = create_enhanced_gui()
    window.show()
    sys.exit(app.exec())