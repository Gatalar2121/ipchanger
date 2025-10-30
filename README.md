# Network IP Changer v2.0.0

A comprehensive Windows network configuration tool with enhanced GUI and CLI interfaces that allows users to easily switch between different network profiles, manage VPN connections, monitor network performance, and configure advanced networking features. Features multi-language support and enterprise-ready functionality.

## 🚀 Features

### Core Functionality
- **Quick Network Profile Switching**: Save and switch between multiple network configurations instantly
- **Static IP Configuration**: Set custom IP addresses, subnet masks, gateways, and DNS servers
- **DHCP Support**: Easy toggle between static and automatic IP assignment
- **Network Interface Detection**: Automatically detects all available network adapters (Ethernet, WiFi, USB, etc.)
- **Undo Functionality**: Revert to previous network settings with one click

### 🆕 New in v2.0.0
- **Command-Line Interface**: Full CLI support with interactive and batch modes
- **Enhanced Tabbed GUI**: Professional interface with organized feature tabs
- **Network Testing Suite**: Comprehensive connectivity, speed, and DNS testing
- **VPN Profile Management**: Create, manage, and connect to VPN profiles using Windows RASDIAL
- **Advanced Routing**: Static route configuration and management
- **Real-Time Monitoring**: Network traffic monitoring with charts and statistics
- **Network Adapter Control**: Enable/disable network adapters programmatically
- **Batch Configuration**: Apply settings from JSON/CSV files to multiple adapters

### Advanced Features
- **Multi-Language Support**: Available in English, Arabic, Persian, Kurdish (Sorani), Kurdish, and Turkish
- **Right-to-Left (RTL) Language Support**: Proper UI layout for Arabic and Persian languages
- **Profile Management**: Import/export network profiles for easy sharing and backup
- **Pre-configured Networks**: Common router and enterprise network templates included
- **Comprehensive Logging**: Detailed operation logs with timestamps
- **Administrator Privilege Handling**: Automatic elevation request with user-friendly error messages

### Enterprise Ready
- **Automation Support**: CLI interface for scripting and automated deployments
- **Monitoring Dashboard**: Real-time network performance monitoring with SQLite database
- **VPN Integration**: Enterprise VPN profile management and connection automation
- **Batch Operations**: Apply settings to multiple interfaces from configuration files
- **Profile Templates**: Pre-built configurations for common enterprise scenarios
- **Silent Operation**: Hidden command execution to prevent UI flickering
- **Robust Error Handling**: Graceful handling of network operation failures

## 📋 Requirements

- **Operating System**: Windows 10/11 (Windows Home and Pro supported)
- **Python**: 3.7+ (for running from source)
- **Administrator Privileges**: Required for modifying network settings

### Dependencies
- PySide6 6.0.0+

## 🛠️ Installation

### Option 1: Download Pre-built Executables (Recommended)
1. Download from the [Releases](../../releases) page:
   - `NetworkIPChanger_v2.0.0.exe` - Full enhanced GUI + CLI features
   - `NetworkIPChanger_CLI_v2.0.0.exe` - CLI-only version for servers
   - `NetworkIPChanger_v1_compatible.exe` - Original v1.0.0 interface
2. Right-click the executable and select "Run as administrator"
3. The application will automatically request administrator privileges

### Option 2: Run from Source
1. Clone this repository:
   ```bash
   git clone https://github.com/Gatalar2121/ipchanger.git
   cd ipchanger
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python ipchanger.py
   ```

### Option 3: Build from Source
1. Follow steps 1-2 from "Run from Source"
2. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
3. Build the executable:
   ```bash
   pyinstaller NetworkIPChanger.spec
   ```
4. The executable will be created in the `dist` folder

## 🖥️ Usage

### GUI Usage
1. **Launch the application** as administrator (required for network changes)
2. **Select Network Interface**: Choose your network adapter from the dropdown
3. **Configure Settings**:
   - Choose between DHCP (automatic) or static IP configuration
   - For static IP: Enter IP address, subnet mask, gateway, and DNS servers
4. **Apply Configuration**: Click "Apply" to save changes

### 🆕 CLI Usage

**Interactive CLI Mode:**
```bash
NetworkIPChanger_v2.0.0.exe --cli
```

**Quick Commands:**
```bash
# List all network adapters
NetworkIPChanger_v2.0.0.exe list-adapters

# Test network connectivity
NetworkIPChanger_v2.0.0.exe test-connectivity

# Configure adapter to DHCP
NetworkIPChanger_v2.0.0.exe configure --adapter "Wi-Fi" --dhcp

# Configure static IP
NetworkIPChanger_v2.0.0.exe configure --adapter "Ethernet" --static --ip 192.168.1.100 --gateway 192.168.1.1

# Monitor network for 60 seconds
NetworkIPChanger_v2.0.0.exe monitor --duration 60

# Show help
NetworkIPChanger_v2.0.0.exe --help
```

**Batch Configuration:**
```bash
# Apply configuration from file
NetworkIPChanger_CLI_v2.0.0.exe batch-configure --file network_config.json

# Configure multiple adapters
NetworkIPChanger_CLI_v2.0.0.exe batch-configure --csv adapters.csv
```

### Profile Management
1. **Save Profile**: Configure your settings and click "Save Profile" to store the configuration
2. **Load Profile**: Select a saved profile and click "Load Profile" to apply those settings
3. **Import/Export**: Use the import/export buttons to share profiles between computers
4. **Delete Profile**: Remove unwanted profiles from your saved list

### Undo Changes
- Click "Undo Last Change" to revert to the previous network configuration
- The application automatically backs up settings before making changes

## 🌍 Language Support

The application supports the following languages with automatic system language detection:

- **English** (en) - Default
- **العربية** (ar) - Arabic with RTL support
- **فارسی** (fa) - Persian with RTL support  
- **کوردی** (ku) - Kurdish
- **کوردی سۆرانی** (ku_sorani) - Kurdish Sorani with RTL support
- **Türkçe** (tr) - Turkish

Language files are located in the `i18n/` directory and can be easily modified or extended.

## 📁 File Structure

```
ipchanger/
├── ipchanger.py              # Main application file
├── requirements.txt          # Python dependencies
├── NetworkIPChanger.spec     # PyInstaller build configuration
├── common_networks.json      # Pre-configured home network profiles
├── sample_profiles.json      # Sample network configurations
├── enterprise_profiles.json  # Enterprise network templates
└── i18n/                    # Internationalization files
    ├── en.json              # English translations
    ├── ar.json              # Arabic translations
    ├── fa.json              # Persian translations
    ├── ku.json              # Kurdish translations
    ├── ku_sorani.json       # Kurdish Sorani translations
    └── tr.json              # Turkish translations
```

## 🔧 Configuration Files

### Profile JSON Format
```json
{
  "Profile Name": {
    "mode": "static",              // "static" or "dhcp"
    "ip": "192.168.1.100",        // IP address (static mode only)
    "mask": "255.255.255.0",      // Subnet mask (static mode only)
    "gateway": "192.168.1.1",     // Default gateway (static mode only)
    "dns": ["8.8.8.8", "8.8.4.4"] // DNS servers (static mode only)
  }
}
```

## ⚠️ Important Notes

- **Administrator privileges are required** for modifying network settings
- The application will automatically request elevation on startup
- Network changes are applied immediately and affect system connectivity
- Always test configurations in a safe environment first
- Keep backups of working network configurations

## 🐛 Troubleshooting

### Common Issues

**"Administrator Rights Required" Error**
- Solution: Right-click the executable and select "Run as administrator"
- Alternative: Run Command Prompt as administrator, then launch the program

**"Network change failed" Error**
- Check that the network adapter name is correct
- Verify IP address format (e.g., 192.168.1.100)
- Ensure subnet mask is valid (e.g., 255.255.255.0)
- Confirm gateway is on the same network

**Interface Not Found**
- Click "Refresh Interfaces" to update the adapter list
- Check that the network adapter is enabled in Network Settings
- Try disconnecting and reconnecting the network cable/WiFi

### Log Files
- Application logs are stored in `netconfig.log`
- Undo backup information is saved in `netconfig_undo.json`
- User profiles are stored in `netconfig_profiles.json`

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Test thoroughly on Windows systems
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔄 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and changes.

## 📧 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your Windows version, Python version (if applicable), and error messages

## 🙏 Acknowledgments

- Built with PySide6 for modern Qt-based GUI
- Multi-language support inspired by international user needs
- Network configuration powered by Windows netsh commands
- Enterprise features designed for IT professionals

---

**⚠️ Disclaimer**: This tool modifies system network settings. Use at your own risk. Always backup your current network configuration before making changes. Test in a controlled environment first.
