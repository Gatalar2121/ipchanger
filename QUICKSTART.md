# Quick Start Guide

## 🚀 Get Started in 2 Minutes

### For End Users (Non-Developers)

1. **Download the Application**
   - Go to [Releases](https://github.com/Gatalar2121/ipchanger/releases)
   - Download `NetworkIPChanger.exe` from the latest release
   - No Python installation needed!

2. **Run the Application**
   - Right-click `NetworkIPChanger.exe`
   - Select "Run as administrator" 
   - Click "Yes" when Windows asks for permission

3. **Configure Your Network**
   - Select your network adapter from dropdown
   - Choose "DHCP" for automatic settings OR
   - Choose "Static IP" and enter your network details
   - Click "Apply" to save changes

4. **Save Your Profile**
   - After configuring, click "Save Profile"
   - Give it a name like "Home Network"
   - Use "Load Profile" to switch between configurations

### For Developers

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Gatalar2121/ipchanger.git
   cd ipchanger
   setup.bat
   ```

2. **Run from Source**
   ```bash
   python ipchanger.py
   ```

3. **Build Executable**
   ```bash
   build.bat
   ```

## ❓ Need Help?

- 📚 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/Gatalar2121/ipchanger/issues)
- 💡 [Request Features](https://github.com/Gatalar2121/ipchanger/issues/new/choose)

## ⚠️ Important Notes

- **Administrator privileges required** for network changes
- **Windows 10/11 only** (uses Windows netsh commands)
- **Backup your settings** before major network changes