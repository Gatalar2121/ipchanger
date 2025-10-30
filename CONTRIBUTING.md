# Contributing to Network IP Changer

Thank you for your interest in contributing to Network IP Changer! This document provides guidelines and information for developers who want to contribute to the project.

## Table of Contents
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style Guidelines](#code-style-guidelines)
- [Adding New Languages](#adding-new-languages)
- [Building the Application](#building-the-application)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Development Setup

### Prerequisites
- Windows 10/11 (required for testing network functionality)
- Python 3.7 or later
- Git for version control
- Administrator privileges (for testing network changes)

### Initial Setup
1. Fork the repository on GitHub
2. Clone your fork to your local machine:
   ```bash
   git clone https://github.com/yourusername/ipchanger.git
   cd ipchanger
   ```
3. Run the setup script to install dependencies:
   ```bash
   setup.bat
   ```
   Or manually install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Development Environment
- **Recommended IDE**: Visual Studio Code, PyCharm, or any Python-compatible editor
- **Required Extensions/Plugins**: Python language support, Git integration
- **Testing**: Always test with administrator privileges to ensure network functionality works

## Project Structure

```
ipchanger/
├── ipchanger.py              # Main application (750+ lines)
├── requirements.txt          # Python dependencies
├── NetworkIPChanger.spec     # PyInstaller configuration
├── setup.bat                 # Development setup script
├── build.bat                 # Build script for executable
├── *.json                    # Pre-configured network profiles
├── i18n/                     # Internationalization files
│   ├── en.json              # English (base language)
│   ├── ar.json              # Arabic (RTL)
│   ├── fa.json              # Persian (RTL)
│   ├── ku.json              # Kurdish
│   ├── ku_sorani.json       # Kurdish Sorani (RTL)
│   └── tr.json              # Turkish
└── docs/                     # Documentation files
```

### Key Components

#### Main Application (`ipchanger.py`)
- **GUI Framework**: PySide6 (Qt6 bindings)
- **Network Operations**: Windows netsh commands via subprocess
- **Internationalization**: JSON-based translation system
- **Profile Management**: JSON file storage for network configurations

#### Configuration Files
- **Profile Templates**: Pre-built network configurations for common scenarios
- **Language Files**: Complete UI translations with RTL support
- **Build Configuration**: PyInstaller spec file for executable creation

## Code Style Guidelines

### Python Code Standards
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Maximum line length: 100 characters
- Use type hints where applicable

### Example Code Style
```python
def configure_network_adapter(adapter_name: str, config: dict) -> bool:
    """Configure network adapter with provided settings.
    
    Args:
        adapter_name: Name of the network adapter to configure
        config: Dictionary containing IP configuration
        
    Returns:
        True if configuration successful, False otherwise
        
    Raises:
        NetworkError: If adapter not found or configuration invalid
    """
    try:
        # Implementation here
        return True
    except Exception as e:
        log_error(f"Configuration failed: {e}")
        return False
```

### GUI Code Guidelines
- Use descriptive widget names
- Group related UI elements logically
- Maintain consistent spacing and alignment
- Implement proper error handling for user interactions
- Ensure RTL language support in layouts

## Adding New Languages

### Translation Process
1. Create a new JSON file in the `i18n/` directory (e.g., `es.json` for Spanish)
2. Copy the structure from `i18n/en.json`
3. Translate all string values to the target language
4. Add the language code to the appropriate lists in `ipchanger.py`

### Language File Structure
```json
{
  "title": "Network Configurator",
  "network_interface": "Network Interface:",
  "refresh_interfaces": "Refresh Interfaces",
  // ... more translations
}
```

### RTL Language Support
For right-to-left languages (Arabic, Hebrew, Persian, etc.):
1. Add the language code to `RTL_LANGS` set in `ipchanger.py`
2. Test layout alignment and text direction
3. Ensure all UI elements are properly mirrored

### Testing Translations
- Test all UI elements with the new language
- Verify text fits within UI elements (some languages need more space)
- Test RTL layout for proper alignment
- Validate special characters and encoding

## Building the Application

### Development Build
For testing during development:
```bash
python ipchanger.py
```

### Production Build
To create a standalone executable:
```bash
# Using the build script (recommended)
build.bat

# Or manually with PyInstaller
pip install pyinstaller
pyinstaller NetworkIPChanger.spec
```

### Build Configuration
The `NetworkIPChanger.spec` file contains:
- Application metadata and icon
- File inclusion rules (i18n, icons, etc.)
- Windows-specific settings (UAC admin request)
- Executable optimization settings

### Testing Builds
- Test the executable on clean Windows systems
- Verify all language files are included
- Check administrator privilege elevation
- Test network functionality with various adapters

## Testing

### Manual Testing Checklist
- [ ] Application starts without errors
- [ ] Administrator privilege request works
- [ ] All network adapters are detected
- [ ] Static IP configuration applies correctly
- [ ] DHCP configuration works
- [ ] Profile save/load functionality
- [ ] Undo functionality restores previous settings
- [ ] All languages display correctly
- [ ] RTL languages have proper layout
- [ ] Import/export profile functionality
- [ ] Error handling for invalid inputs
- [ ] Logging system captures operations

### Test Environment
- **Primary**: Windows 10/11 with multiple network adapters
- **Secondary**: Windows systems with different language settings
- **Network Configs**: Test with various IP ranges and DNS settings

### Safety Considerations
- Always backup current network settings before testing
- Test in a controlled environment (not production networks)
- Have a way to restore network connectivity if tests fail
- Document any permanent changes made during testing

## Submitting Changes

### Pull Request Process
1. Create a feature branch from main:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes following the coding guidelines
3. Test thoroughly on Windows systems
4. Update documentation if needed
5. Commit with descriptive messages:
   ```bash
   git commit -m "Add support for IPv6 configuration"
   ```
6. Push to your fork and create a pull request

### Commit Message Guidelines
- Use imperative mood ("Add feature" not "Added feature")
- Limit first line to 50 characters
- Provide detailed description if necessary
- Reference issue numbers when applicable

### Code Review Process
- All changes require review before merging
- Address reviewer feedback promptly
- Ensure CI checks pass (if implemented)
- Update documentation for user-facing changes

## Reporting Issues

### Bug Reports
When reporting bugs, please include:
- Windows version and edition
- Python version (if running from source)
- Exact error messages or unexpected behavior
- Steps to reproduce the issue
- Network adapter types being used
- Application logs if available

### Feature Requests
For new features:
- Describe the use case and benefits
- Provide mockups or examples if applicable
- Consider internationalization requirements
- Discuss potential implementation approaches

### Security Issues
For security-related issues:
- Do not post publicly initially
- Email maintainers directly
- Provide detailed reproduction steps
- Allow time for assessment and fixes

## Development Best Practices

### Network Programming
- Always handle network operation failures gracefully
- Provide clear error messages for users
- Log all network changes for debugging
- Validate IP addresses and network parameters
- Test with various network adapter types

### GUI Development
- Maintain responsive UI during network operations
- Use threading for long-running operations
- Provide visual feedback for user actions
- Ensure keyboard navigation works
- Test with different Windows themes and scaling

### Internationalization
- Never hardcode user-visible strings
- Use translation keys consistently
- Test with languages that have different text lengths
- Consider cultural differences in UI conventions
- Ensure proper encoding for all supported languages

## Resources

### Documentation
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Windows Netsh Documentation](https://docs.microsoft.com/en-us/windows-server/networking/technologies/netsh/)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)

### Tools
- [Qt Designer](https://doc.qt.io/qt-6/qtdesigner-manual.html) for UI design
- [Python Black](https://black.readthedocs.io/) for code formatting
- [Pylint](https://pylint.org/) for code analysis

### Community
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and community interaction
- Pull Requests for code contributions

---

Thank you for contributing to Network IP Changer! Your efforts help make network configuration easier for users worldwide.