#!/usr/bin/env python3
"""
Network IP Changer - Professional Windows Network Configuration Tool

A modern GUI application for managing Windows network settings with support for:
- Static IP and DHCP configuration
- Network profile management
- Multi-language support (6 languages)
- Enterprise-ready features
- Automatic administrator privilege handling

Author: PyxSara
Version: 1.0.0
License: MIT License
Repository: https://github.com/PyxSara/ipchanger
"""

import sys, os, json, re, subprocess, ctypes
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QMessageBox, QFileDialog, QGroupBox,
    QRadioButton, QButtonGroup, QFormLayout, QListWidget, QListWidgetItem,
    QInputDialog, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QIcon

# Application Information
__version__ = "1.0.0"
__author__ = "PyxSara"
__license__ = "MIT"
__repository__ = "https://github.com/PyxSara/ipchanger"

APP_DIR = Path(__file__).resolve().parent
LOG_PATH = APP_DIR / "netconfig.log"
UNDO_PATH = APP_DIR / "netconfig_undo.json"
PROFILES_PATH = APP_DIR / "netconfig_profiles.json"
I18N_DIR = APP_DIR / "i18n"
ICON_PATH = APP_DIR / "ip.ico"

def elevate_if_needed():
    """Request admin privileges if not already elevated. Works on Windows Home and Pro."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        # If IsUserAnAdmin fails (e.g., on some Windows Home editions), assume not admin
        is_admin = False
    
    if not is_admin:
        try:
            # Build command line arguments
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
            
            # Try to elevate using ShellExecuteW with hidden window to prevent flashing
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script}" {params}', 
                None, 
                0  # SW_HIDE - Hide the window to prevent flashing
            )
            
            # If ShellExecuteW returns > 32, elevation was successful
            if ret > 32:
                sys.exit(0)
            else:
                # Elevation failed or was cancelled
                return False
        except Exception as e:
            # If elevation fails completely, continue but warn the user
            return False
    return True

def load_translations():
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

TRANSLATIONS = load_translations()
if "en" not in TRANSLATIONS:
    TRANSLATIONS["en"] = {"title":"Network Configurator","language":"Language:"}
RTL_LANGS = {"ar","fa","ku_sorani"}

CURRENT_LANG = "en"
CURRENT_TR = TRANSLATIONS.get(CURRENT_LANG, {})
IS_RTL = False

def tr(key):
    return CURRENT_TR.get(key, key)

def run_netsh(args):
    try:
        # Use CREATE_NO_WINDOW to prevent command window flashing
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        p = subprocess.run(
            ["netsh"] + args, 
            capture_output=True, 
            text=True, 
            shell=False,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def run_powershell(command):
    """Run PowerShell command without showing window."""
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
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def run_hidden_command(cmd_list):
    """Run any command without showing window."""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        p = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            shell=False,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def list_adapters():
    """Get all network adapters including WiFi, Ethernet, USB, and virtual adapters."""
    adapters = []
    
    # Method 1: Use netsh to get all interfaces
    rc, out, err = run_netsh(["interface", "show", "interface"])
    if rc == 0 and out:
        for line in out.splitlines()[3:]:  # Skip header lines
            parts = line.strip().split()
            if len(parts) >= 4:
                adapter_name = " ".join(parts[3:])
                # Filter out loopback and isatap interfaces
                if not any(x in adapter_name.lower() for x in ['loopback', 'isatap', 'teredo']):
                    adapters.append(adapter_name)
    
    # Method 2: Use PowerShell to get network adapters (more reliable for USB/WiFi)
    try:
        ps_command = "Get-NetAdapter | Where-Object {$_.Status -eq 'Up' -or $_.Status -eq 'Disconnected'} | Select-Object -ExpandProperty Name"
        rc2, out2, err2 = run_powershell(ps_command)
        if rc2 == 0 and out2:
            for line in out2.splitlines():
                adapter_name = line.strip()
                if adapter_name and adapter_name not in adapters:
                    # Filter out problematic entries
                    if not any(x in adapter_name.lower() for x in ['loopback', 'isatap', 'teredo']):
                        adapters.append(adapter_name)
    except Exception:
        pass
    
    # Method 3: Also try to get WiFi profiles which might reveal hidden WiFi adapters
    try:
        rc3, out3, err3 = run_netsh(["wlan", "show", "interfaces"])
        if rc3 == 0 and out3:
            for line in out3.splitlines():
                if line.strip().startswith("Name"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        wifi_name = parts[1].strip()
                        # Add WiFi adapter if not already in list
                        if wifi_name and wifi_name not in adapters:
                            adapters.append(wifi_name)
    except Exception:
        pass
    
    # Method 4: Use WMI to get network adapters (fallback method)
    try:
        # Get network adapters using WMI - more comprehensive than netsh
        wmi_cmd = [
            "wmic", "nic", "where", "NetEnabled=true", 
            "get", "Name,NetConnectionID", "/format:csv"
        ]
        
        rc4, out4, err4 = run_hidden_command(wmi_cmd)
        if rc4 == 0 and out4:
            lines = out4.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 3 and parts[2]:  # NetConnectionID exists
                    adapter_name = parts[2]
                    if adapter_name and adapter_name not in adapters:
                        # Filter out problematic entries
                        if not any(x in adapter_name.lower() for x in ['loopback', 'isatap', 'teredo']):
                            adapters.append(adapter_name)
    except Exception:
        pass
    
    # Method 5: Try PowerShell with more detailed adapter info for USB/external adapters
    try:
        ps_command_detailed = """
        Get-WmiObject -Class Win32_NetworkAdapter | 
        Where-Object {$_.NetConnectionID -ne $null -and $_.NetEnabled -eq $true} | 
        Select-Object -ExpandProperty NetConnectionID
        """
        rc5, out5, err5 = run_powershell(ps_command_detailed)
        if rc5 == 0 and out5:
            for line in out5.splitlines():
                adapter_name = line.strip()
                if adapter_name and adapter_name not in adapters:
                    # Filter out problematic entries
                    if not any(x in adapter_name.lower() for x in ['loopback', 'isatap', 'teredo']):
                        adapters.append(adapter_name)
    except Exception:
        pass
    
    # Remove duplicates and sort
    adapters = sorted(list(set(filter(None, adapters))))
    
    return adapters

def get_ipv4_settings(ifname):
    settings = {"mode":"unknown","ip":"","mask":"","gateway":"","dns":[]}
    escaped_name = escape_interface_name_for_config(ifname)
    rc,out,err = run_netsh(["interface","ip","show","config",f"name={escaped_name}"])
    if rc!=0: return settings
    for line in out.splitlines():
        l=line.strip()
        if l.startswith("DHCP enabled") and "Yes" in l:
            settings["mode"]="dhcp"
        if l.startswith("IP Address"):
            parts=l.split(":",1)
            if len(parts)>1: settings["ip"]=parts[1].strip()
        if l.startswith("Subnet Prefix"):
            m=re.search(r"mask\s+([\d\.]+)", l)
            if m: settings["mask"]=m.group(1)
        if l.startswith("Default Gateway"):
            parts=l.split(":",1)
            if len(parts)>1: settings["gateway"]=parts[1].strip()
    escaped_name_dns = escape_interface_name_for_config(ifname)
    rc2,out2,err2=run_netsh(["interface","ip","show","dns",f"name={escaped_name_dns}"])
    if rc2==0:
        dns=[]
        for ln in out2.splitlines():
            m=re.search(r"([\d]{1,3}(?:\.[\d]{1,3}){3})", ln)
            if m: dns.append(m.group(1))
        settings["dns"]=dns
    if settings["mode"]!="dhcp" and settings["ip"]:
        settings["mode"]="static"
    return settings

_ip_re = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
def is_valid_ip(addr):
    if not _ip_re.match(addr): return False
    return all(0<=int(p)<=255 for p in addr.split("."))

def escape_interface_name(ifname):
    """Properly escape interface names for netsh commands."""
    # Remove any existing quotes
    cleaned = ifname.strip('"\'')
    return cleaned  # Don't add quotes - netsh handles spaces differently

def escape_interface_name_for_config(ifname):
    """Escape interface names specifically for 'show config' commands."""
    cleaned = ifname.strip('"\'')
    # Only quote for show config commands
    if ' ' in cleaned or any(char in cleaned for char in ['(', ')', '&', '%', '$']):
        return f'"{cleaned}"'
    return cleaned

def get_interface_status(ifname):
    """Get the status of a network interface (Connected/Disconnected/Disabled)."""
    rc, out, err = run_netsh(["interface", "show", "interface"])
    if rc == 0 and out:
        for line in out.splitlines()[3:]:  # Skip header lines
            parts = line.strip().split()
            if len(parts) >= 4:
                interface_name = " ".join(parts[3:])
                if interface_name == ifname:
                    # Return status from second column
                    if len(parts) >= 2:
                        return parts[1]  # Connected, Disconnected, etc.
    return "Unknown"

def log_action(action, details=""):
    try:
        with open(LOG_PATH,"a",encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(sep=' ',timespec='seconds')}] {action} {details}\n")
    except Exception:
        pass

def save_undo(ifname):
    cfg = get_ipv4_settings(ifname)
    try:
        with open(UNDO_PATH,"w",encoding="utf-8") as f:
            json.dump({"interface":ifname,"cfg":cfg,"timestamp":datetime.now().isoformat()}, f, indent=2)
    except Exception:
        pass

def load_profiles():
    if not PROFILES_PATH.exists(): return {}
    try:
        with open(PROFILES_PATH,"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_profiles(p):
    try:
        with open(PROFILES_PATH,"w",encoding="utf-8") as f:
            json.dump(p,f,indent=2)
    except Exception:
        pass

def apply_configuration(ifname, cfg, record_undo=True):
    """Apply network configuration to an interface. Handles DHCP -> Static conversion properly."""
    if record_undo: save_undo(ifname)
    
    # Check interface status
    interface_status = get_interface_status(ifname)
    if interface_status == "Disabled":
        return False, f"Interface '{ifname}' is disabled. Please enable it in Network Connections first."
    
    if cfg.get("mode")=="dhcp":
        # Switching to DHCP mode
        escaped_name = escape_interface_name(ifname)
        # Try DHCP with name= syntax first
        rc,out,err = run_netsh(["interface","ip","set","address",f"name={escaped_name}","dhcp"])
        if rc!=0:
            # Try without name= prefix
            rc,out,err = run_netsh(["interface","ip","set","address",escaped_name,"dhcp"])
        
        if rc!=0: 
            if "elevation" in (err or out).lower() or "administrator" in (err or out).lower():
                return False, "Administrator privileges required. Please run as administrator to modify network settings."
            return False, f"Failed to set DHCP for IP: {err or out}"
        
        # Try DNS with name= syntax first
        rc2,out2,err2 = run_netsh(["interface","ip","set","dns",f"name={escaped_name}","dhcp"])
        if rc2!=0:
            # Try without name= prefix
            rc2,out2,err2 = run_netsh(["interface","ip","set","dns",escaped_name,"dhcp"])
        if rc2!=0: 
            if "elevation" in (err2 or out2).lower() or "administrator" in (err2 or out2).lower():
                return False, "Administrator privileges required. Please run as administrator to modify network settings."
            return False, f"Failed to set DHCP for DNS: {err2 or out2}"
        return True, tr("apply_confirm")
    
    # Static IP configuration
    ip=cfg.get("ip",""); mask=cfg.get("mask",""); gw=cfg.get("gateway",""); dns_list=cfg.get("dns",[]) or []
    if not (ip and mask): return False, tr("ip_mask_required")
    if not (is_valid_ip(ip) and is_valid_ip(mask)): return False, tr("invalid_ip_mask")
    
    # Try multiple netsh command formats for maximum compatibility
    success = False
    last_error = ""
    escaped_name = escape_interface_name(ifname)
    
    # Method 1: Modern netsh syntax with source=static
    cmd1 = ["interface", "ip", "set", "address", f"name={escaped_name}", "source=static", f"addr={ip}", f"mask={mask}"]
    if gw and is_valid_ip(gw):
        cmd1.extend([f"gateway={gw}", "gwmetric=1"])
    
    rc1, out1, err1 = run_netsh(cmd1)
    if rc1 == 0:
        success = True
    else:
        last_error = err1 or out1
        
        # Method 2: Alternative syntax without source parameter (no name= prefix)
        cmd2 = ["interface", "ip", "set", "address", escaped_name, "static", ip, mask]
        if gw and is_valid_ip(gw):
            cmd2.extend([gw, "1"])
        
        rc2, out2, err2 = run_netsh(cmd2)
        if rc2 == 0:
            success = True
        else:
            last_error = err2 or out2
            
            # Method 3: Try with interface index instead of name
            try:
                # Get interface index
                rc_idx, out_idx, _ = run_netsh(["interface", "ip", "show", "config"])
                interface_idx = None
                if rc_idx == 0:
                    lines = out_idx.splitlines()
                    for i, line in enumerate(lines):
                        if ifname in line and "Configuration for interface" in line:
                            # Extract interface index from line like 'Configuration for interface "Ethernet" (index: 12)'
                            import re
                            match = re.search(r'index:\s*(\d+)', line)
                            if match:
                                interface_idx = match.group(1)
                                break
                
                if interface_idx:
                    cmd3 = ["interface", "ip", "set", "address", interface_idx, "static", ip, mask]
                    if gw and is_valid_ip(gw):
                        cmd3.extend([gw, "1"])
                    
                    rc3, out3, err3 = run_netsh(cmd3)
                    if rc3 == 0:
                        success = True
                    else:
                        last_error = err3 or out3
            except:
                pass
            
            # Method 4: For disconnected interfaces, try forcing the configuration
            if not success:
                try:
                    # Try removing existing IP first, then setting new one
                    run_netsh(["interface", "ip", "delete", "address", f"name={escaped_name}", "all"])
                    
                    # Now try setting the static IP again with a slightly different approach
                    cmd4 = ["interface", "ip", "add", "address", f"name={escaped_name}", f"addr={ip}", f"mask={mask}"]
                    if gw and is_valid_ip(gw):
                        cmd4.append(f"gateway={gw}")
                    
                    rc4, out4, err4 = run_netsh(cmd4)
                    if rc4 == 0:
                        success = True
                    else:
                        last_error = f"Add address method failed: {err4 or out4}"
                except:
                    pass
    
    if not success:
        # Check if the error is due to elevation requirements
        if "elevation" in last_error.lower() or "administrator" in last_error.lower():
            return False, "Administrator privileges required. Please run as administrator to modify network settings."
        elif "invalid source parameter" in last_error.lower():
            return False, f"Invalid interface name or syntax error. Try refreshing the interface list."
        elif "not found" in last_error.lower() or "could not find" in last_error.lower():
            return False, f"Interface '{ifname}' not found. Try refreshing the interface list."
        elif interface_status == "Disconnected":
            # Special message for disconnected interfaces
            return False, f"Interface '{ifname}' is disconnected (no cable). The IP settings should still be configurable. Try:\n1. Connect the Ethernet cable\n2. Or try configuring anyway - settings may be saved for when cable is connected\n\nDetailed error: {last_error}"
        else:
            return False, f"Failed to set static IP: {last_error}"
    
    # Configure DNS servers
    if dns_list:
        # Set primary DNS - try with name= first, then without
        rc2,out2,err2 = run_netsh(["interface","ip","set","dns",f"name={escaped_name}","static",dns_list[0]])
        if rc2!=0:
            rc2,out2,err2 = run_netsh(["interface","ip","set","dns",escaped_name,"static",dns_list[0]])
        
        if rc2!=0: 
            if "elevation" in (err2 or out2).lower() or "administrator" in (err2 or out2).lower():
                return False, "Administrator privileges required. Please run as administrator to modify network settings."
            return False, f"Failed to set DNS: {err2 or out2}"
        
        # Add additional DNS servers
        for idx,dns in enumerate(dns_list[1:], start=2):
            if is_valid_ip(dns):
                # Try both syntaxes for additional DNS
                rc_add,_,_ = run_netsh(["interface","ip","add","dns",f"name={escaped_name}",dns,f"index={idx}"])
                if rc_add!=0:
                    run_netsh(["interface","ip","add","dns",escaped_name,dns,f"index={idx}"])
    else:
        # If no DNS specified, set to DHCP for DNS only
        rc_dhcp,_,_ = run_netsh(["interface","ip","set","dns",f"name={escaped_name}","dhcp"])
        if rc_dhcp!=0:
            run_netsh(["interface","ip","set","dns",escaped_name,"dhcp"])
    
    return True, tr("apply_confirm")

class NetConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("title"))
        if ICON_PATH.exists(): self.setWindowIcon(QIcon(str(ICON_PATH)))
        self._build_ui()
        self.refresh_adapters()
        self.refresh_profiles()
        self.update_current_info()

    def _build_ui(self):
        main = QHBoxLayout(self)
        left = QVBoxLayout()
        right = QVBoxLayout()
        main.addLayout(left,3); main.addLayout(right,2)
        top_row = QHBoxLayout(); left.addLayout(top_row)
        self.lbl_iface = QLabel(tr("network_interface")); top_row.addWidget(self.lbl_iface)
        self.cb_adapter = QComboBox(); self.cb_adapter.currentIndexChanged.connect(self.update_current_info); top_row.addWidget(self.cb_adapter)
        self.btn_refresh = QPushButton(tr("refresh_interfaces")); self.btn_refresh.clicked.connect(self.refresh_adapters); top_row.addWidget(self.btn_refresh)
        top_row.addSpacerItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        self.lbl_language = QLabel(tr("language")); top_row.addWidget(self.lbl_language)
        self.lang_cb = QComboBox(); self.lang_cb.addItems(sorted(TRANSLATIONS.keys())); self.lang_cb.setCurrentText(CURRENT_LANG); self.lang_cb.currentTextChanged.connect(self.change_language); top_row.addWidget(self.lang_cb)
        self.grp_current = QGroupBox(tr("current_settings")); left.addWidget(self.grp_current)
        cur_layout = QVBoxLayout(self.grp_current); self.info_text = QTextEdit(); self.info_text.setReadOnly(True); cur_layout.addWidget(self.info_text); self.status_lbl = QLabel(tr("ready")); cur_layout.addWidget(self.status_lbl)
        self.adapters_list = QListWidget(); self.adapters_list.setSelectionMode(QListWidget.MultiSelection); left.addWidget(QLabel(tr("apply_to_selected"))); left.addWidget(self.adapters_list)
        self.grp_profiles = QGroupBox(tr("profiles")); left.addWidget(self.grp_profiles); p_layout = QVBoxLayout(self.grp_profiles); self.profiles_list = QListWidget(); self.profiles_list.itemSelectionChanged.connect(self.on_profile_selected); p_layout.addWidget(self.profiles_list); p_layout.addWidget(QLabel(tr("profile_preview"))); self.profile_preview = QTextEdit(); self.profile_preview.setReadOnly(True); p_layout.addWidget(self.profile_preview)
        prof_btn_row = QHBoxLayout(); self.btn_save_profile = QPushButton(tr("save_profile")); self.btn_save_profile.clicked.connect(self.save_profile); self.btn_load_profile = QPushButton(tr("load_profile")); self.btn_load_profile.clicked.connect(self.load_profile); self.btn_delete_profile = QPushButton(tr("delete_profile")); self.btn_delete_profile.clicked.connect(self.delete_profile); prof_btn_row.addWidget(self.btn_save_profile); prof_btn_row.addWidget(self.btn_load_profile); prof_btn_row.addWidget(self.btn_delete_profile); p_layout.addLayout(prof_btn_row)
        prof_imp_row = QHBoxLayout(); self.btn_import_profiles = QPushButton(tr("import_profiles")); self.btn_import_profiles.clicked.connect(self.import_profiles); self.btn_export_profiles = QPushButton(tr("export_profiles")); self.btn_export_profiles.clicked.connect(self.export_profiles); prof_imp_row.addWidget(self.btn_import_profiles); prof_imp_row.addWidget(self.btn_export_profiles); p_layout.addLayout(prof_imp_row)
        self.grp_conf = QGroupBox(tr("configuration")); right.addWidget(self.grp_conf); form = QFormLayout(self.grp_conf)
        self.rb_group = QButtonGroup(); self.rb_dhcp = QRadioButton(tr("dhcp_option")); self.rb_static = QRadioButton(tr("static_option")); self.rb_group.addButton(self.rb_dhcp); self.rb_group.addButton(self.rb_static); self.rb_dhcp.setChecked(True); form.addRow(self.rb_dhcp); form.addRow(self.rb_static)
        self.lbl_ip = QLabel(tr("ip_address")); self.ip_edit = QLineEdit(); self.ip_edit.setPlaceholderText(tr("ip_address")); form.addRow(self.lbl_ip,self.ip_edit)
        self.lbl_mask = QLabel(tr("subnet_mask")); self.mask_edit = QLineEdit(); self.mask_edit.setPlaceholderText(tr("subnet_mask")); form.addRow(self.lbl_mask,self.mask_edit)
        self.lbl_gw = QLabel(tr("default_gateway")); self.gw_edit = QLineEdit(); self.gw_edit.setPlaceholderText(tr("default_gateway")); form.addRow(self.lbl_gw,self.gw_edit)
        self.lbl_dns = QLabel(tr("dns_servers")); self.dns_edit = QLineEdit(); self.dns_edit.setPlaceholderText(tr("dns_servers")); form.addRow(self.lbl_dns,self.dns_edit)
        self.btn_apply = QPushButton(tr("apply_configuration")); self.btn_apply.clicked.connect(self.on_apply); right.addWidget(self.btn_apply)
        right.addSpacerItem(QSpacerItem(20,20,QSizePolicy.Minimum,QSizePolicy.Expanding))
        self.btn_apply_to_selected = QPushButton(tr("apply_to_selected")); self.btn_apply_to_selected.clicked.connect(self.apply_profile_to_selected_adapters); right.addWidget(self.btn_apply_to_selected)
        self.btn_undo = QPushButton(tr("undo_last_change")); self.btn_undo.clicked.connect(self.on_undo); right.addWidget(self.btn_undo)
        self.btn_open_log = QPushButton(tr("open_log")); self.btn_open_log.clicked.connect(self.open_log); right.addWidget(self.btn_open_log)

    def change_language(self, lang):
        global CURRENT_LANG, CURRENT_TR, IS_RTL
        if lang not in TRANSLATIONS: lang="en"
        CURRENT_LANG = lang
        CURRENT_TR = TRANSLATIONS[lang]
        IS_RTL = lang in RTL_LANGS
        self.apply_translations()

    def apply_translations(self):
        self.setWindowTitle(tr("title"))
        self.lbl_iface.setText(tr("network_interface"))
        self.btn_refresh.setText(tr("refresh_interfaces"))
        self.lbl_language.setText(tr("language"))
        self.grp_current.setTitle(tr("current_settings"))
        self.status_lbl.setText(tr("ready"))
        self.grp_profiles.setTitle(tr("profiles"))
        self.btn_save_profile.setText(tr("save_profile"))
        self.btn_load_profile.setText(tr("load_profile"))
        self.btn_delete_profile.setText(tr("delete_profile"))
        self.btn_import_profiles.setText(tr("import_profiles"))
        self.btn_export_profiles.setText(tr("export_profiles"))
        self.profile_preview.setPlaceholderText(tr("profile_preview"))
        self.grp_conf.setTitle(tr("configuration"))
        self.rb_dhcp.setText(tr("dhcp_option"))
        self.rb_static.setText(tr("static_option"))
        self.lbl_ip.setText(tr("ip_address")); self.ip_edit.setPlaceholderText(tr("ip_address"))
        self.lbl_mask.setText(tr("subnet_mask")); self.mask_edit.setPlaceholderText(tr("subnet_mask"))
        self.lbl_gw.setText(tr("default_gateway")); self.gw_edit.setPlaceholderText(tr("default_gateway"))
        self.lbl_dns.setText(tr("dns_servers")); self.dns_edit.setPlaceholderText(tr("dns_servers"))
        self.btn_apply.setText(tr("apply_configuration"))
        self.btn_apply_to_selected.setText(tr("apply_to_selected"))
        self.btn_undo.setText(tr("undo_last_change"))
        self.btn_open_log.setText(tr("open_log"))
        direction = Qt.RightToLeft if IS_RTL else Qt.LeftToRight
        self.setLayoutDirection(direction)
        align = Qt.AlignRight if IS_RTL else Qt.AlignLeft
        for edit in (self.ip_edit,self.mask_edit,self.gw_edit,self.dns_edit,self.info_text,self.profile_preview):
            edit.setLayoutDirection(direction)
            if hasattr(edit,'setAlignment'):
                edit.setAlignment(align)
        self.refresh_adapters(); self.refresh_profiles(); self.update_current_info()

    def refresh_adapters(self):
        try:
            self.status_lbl.setText("Detecting adapters...")
            adapters = list_adapters()
            self.cb_adapter.clear()
            self.adapters_list.clear()
            
            if adapters:
                self.cb_adapter.addItems(adapters)
                for a in adapters: 
                    self.adapters_list.addItem(a)
                self.cb_adapter.setCurrentIndex(0)
                self.status_lbl.setText(f"Found {len(adapters)} adapter(s)")
            else:
                self.status_lbl.setText("No network adapters found")
                QMessageBox.warning(
                    self, 
                    "No Adapters Found", 
                    "No network adapters were detected. This might happen if:\n\n"
                    "• You're not running as administrator\n"
                    "• Network adapters are disabled\n"
                    "• Drivers are not properly installed\n\n"
                    "Try running as administrator or check Device Manager."
                )
        except Exception as e:
            self.status_lbl.setText("Error detecting adapters")
            QMessageBox.critical(self, "Error", f"Failed to detect adapters: {str(e)}")

    def update_current_info(self):
        if not self.cb_adapter.count(): self.info_text.setPlainText(""); self.status_lbl.setText(tr("ready")); return
        ifname=self.cb_adapter.currentText(); s=get_ipv4_settings(ifname)
        lines=[f"{tr('mode')} {s.get('mode')}"]
        if s.get('ip'): lines.append(f"{tr('ip')} {s.get('ip')}")
        if s.get('mask'): lines.append(f"{tr('mask')} {s.get('mask')}")
        if s.get('gateway'): lines.append(f"{tr('gateway')} {s.get('gateway')}")
        if s.get('dns'): lines.append(f"{tr('dns')} {', '.join(s.get('dns'))}")
        self.info_text.setPlainText("\n".join(lines))
        self.status_lbl.setText(f"{s.get('mode').upper()} - {s.get('ip') or 'no IP'}")
        self.ip_edit.setText(s.get('ip','')); self.mask_edit.setText(s.get('mask','')); self.gw_edit.setText(s.get('gateway','')); self.dns_edit.setText(", ".join(s.get('dns',[])))
        if s.get('mode')=='dhcp': self.rb_dhcp.setChecked(True)
        else: self.rb_static.setChecked(True)

    def refresh_profiles(self):
        p = load_profiles(); self.profiles_list.clear()
        for name in sorted(p.keys()): self.profiles_list.addItem(QListWidgetItem(name))

    def on_profile_selected(self):
        it=self.profiles_list.currentItem()
        if not it: self.profile_preview.clear(); return
        p=load_profiles().get(it.text(),{}); self.profile_preview.setPlainText(json.dumps(p,indent=2))

    def save_profile(self):
        name,ok=QInputDialog.getText(self,tr("profiles"),tr("save_profile"))
        if not ok or not name: return
        profile={"mode":"dhcp" if self.rb_dhcp.isChecked() else "static","ip":self.ip_edit.text().strip(),"mask":self.mask_edit.text().strip(),"gateway":self.gw_edit.text().strip(),"dns":[d.strip() for d in self.dns_edit.text().split(",") if d.strip()]}
        profiles=load_profiles(); profiles[name]=profile; save_profiles(profiles); self.refresh_profiles(); QMessageBox.information(self,tr("success"),tr("profile_saved").format(name))

    def load_profile(self):
        it=self.profiles_list.currentItem()
        if not it: QMessageBox.warning(self,tr("failed"),tr("select_profile")); return
        p=load_profiles().get(it.text()); 
        if not p: QMessageBox.warning(self,tr("failed"),tr("select_profile")); return
        self.rb_dhcp.setChecked(p.get("mode","dhcp")=="dhcp"); self.ip_edit.setText(p.get("ip","")); self.mask_edit.setText(p.get("mask","")); self.gw_edit.setText(p.get("gateway","")); self.dns_edit.setText(", ".join(p.get("dns",[])))

    def delete_profile(self):
        it=self.profiles_list.currentItem()
        if not it: QMessageBox.warning(self,tr("failed"),tr("select_profile")); return
        name=it.text(); profiles=load_profiles()
        if name in profiles: del profiles[name]; save_profiles(profiles); self.refresh_profiles(); QMessageBox.information(self,tr("success"),tr("profile_deleted").format(name))

    def import_profiles(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("import_profiles"), str(APP_DIR), "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profiles = load_profiles()
            profiles.update(data)
            save_profiles(profiles)
            self.refresh_profiles()
            QMessageBox.information(self, tr("success"), tr("imported"))
        except Exception as e:
            QMessageBox.critical(self, tr("failed"), str(e))

    def export_profiles(self):
        path,_=QFileDialog.getSaveFileName(self,tr("export_profiles"),str(APP_DIR/"profiles_export.json"),"JSON Files (*.json)")
        if not path: return
        try:
            profiles=load_profiles();
            with open(path,"w",encoding="utf-8") as f: json.dump(profiles,f,indent=2)
            QMessageBox.information(self,tr("success"),tr("exported"))
        except Exception as e:
            QMessageBox.critical(self,tr("failed"),str(e))

    def apply_profile_to_selected_adapters(self):
        it=self.profiles_list.currentItem()
        if not it: QMessageBox.warning(self,tr("failed"),tr("select_profile")); return
        profile=load_profiles().get(it.text()); 
        if not profile: QMessageBox.warning(self,tr("failed"),tr("select_profile")); return
        selected=[i.text() for i in self.adapters_list.selectedItems()]
        if not selected: QMessageBox.warning(self,tr("failed"),tr("no_adapter")); return
        errors=[]
        for ifname in selected:
            ok,msg=apply_configuration(ifname,profile,record_undo=True)
            if not ok: errors.append(f"{ifname}: {msg}")
            else: log_action("APPLY_PROFILE",f"{ifname} <- {it.text()}")
        if errors: QMessageBox.critical(self,tr("failed"),"\n".join(errors))
        else: QMessageBox.information(self,tr("success"),tr("apply_confirm"))
        self.update_current_info()

    def on_apply(self):
        if not self.cb_adapter.count(): QMessageBox.warning(self,tr("failed"),tr("no_adapter")); return
        ifname=self.cb_adapter.currentText(); cfg={"mode":"dhcp" if self.rb_dhcp.isChecked() else "static"}
        if cfg["mode"]=="static": cfg["ip"]=self.ip_edit.text().strip(); cfg["mask"]=self.mask_edit.text().strip(); cfg["gateway"]=self.gw_edit.text().strip()
        cfg["dns"]=[d.strip() for d in self.dns_edit.text().split(",") if d.strip()]
        ok,msg=apply_configuration(ifname,cfg,record_undo=True)
        if ok: log_action("APPLY",f"{ifname} {cfg}"); QMessageBox.information(self,tr("success"),tr("apply_confirm"))
        else: QMessageBox.critical(self,tr("failed"),f"{tr('error_run_netsh')}: {msg}")
        self.update_current_info()

    def on_undo(self):
        if not UNDO_PATH.exists(): QMessageBox.information(self,tr("undo_last_change"),tr("undo_no_backup")); return
        try:
            with open(UNDO_PATH,"r",encoding="utf-8") as f: data=json.load(f)
            ifname=data.get("interface"); cfg=data.get("cfg",{})
            apply_configuration(ifname,cfg,record_undo=False); QMessageBox.information(self,tr("success"),tr("undo_done")); self.update_current_info()
        except Exception as e:
            QMessageBox.critical(self,tr("failed"),str(e))

    def open_log(self):
        if LOG_PATH.exists(): 
            try:
                # Use subprocess to open log file without flashing
                subprocess.run(['notepad.exe', str(LOG_PATH)], 
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             startupinfo=None)
            except:
                # Fallback to os.startfile if notepad fails
                try:
                    os.startfile(str(LOG_PATH))
                except:
                    QMessageBox.information(self, tr("open_log"), "Could not open log file")
        else: 
            QMessageBox.information(self, tr("open_log"), tr("ready"))

def main():
    # Try to elevate privileges
    elevation_success = elevate_if_needed()
    
    app=QApplication(sys.argv); app.setApplicationName("Network Configurator")
    if ICON_PATH.exists(): app.setWindowIcon(QIcon(str(ICON_PATH)))
    
    global CURRENT_LANG, CURRENT_TR, IS_RTL
    sys_lang = QLocale.system().name()[:2]
    if sys_lang in TRANSLATIONS: CURRENT_LANG=sys_lang
    else: CURRENT_LANG="en"
    CURRENT_TR = TRANSLATIONS.get(CURRENT_LANG, {})
    IS_RTL = CURRENT_LANG in RTL_LANGS
    
    w=NetConfigUI()
    
    # Show warning if not running as admin
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
            "2. Right-click on the program file or launcher.bat\n"
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

if __name__=="__main__":
    main()