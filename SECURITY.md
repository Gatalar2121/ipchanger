# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Active support  |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Network IP Changer, please follow these steps:

### For Security Issues:

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead:
1. **Email**: Send details to the repository owner
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fixes (if any)

### What to Expect:
- **Response Time**: Within 48 hours
- **Assessment**: We'll evaluate the issue within 1 week
- **Fix Timeline**: Critical issues within 2 weeks, others in next release
- **Credit**: You'll be credited in the security advisory (if desired)

### Security Best Practices:

#### For Users:
- ✅ Always run as administrator (required for network changes)
- ✅ Download only from official GitHub releases
- ✅ Verify file integrity if concerned
- ✅ Keep Windows updated
- ✅ Use antivirus software

#### For Developers:
- ✅ Review code changes carefully
- ✅ Validate all user inputs
- ✅ Follow secure coding practices
- ✅ Test administrator privilege handling
- ✅ Ensure network commands are properly escaped

### Known Security Considerations:

1. **Administrator Privileges**: Required for network configuration
   - This is necessary for Windows netsh commands
   - Application requests elevation transparently
   - No privilege escalation vulnerabilities known

2. **Network Command Execution**: Uses subprocess with controlled inputs
   - All user inputs are validated
   - Commands use specific parameter lists
   - No shell injection vulnerabilities known

3. **File Operations**: Profile import/export functionality
   - JSON files only, no executable content
   - Proper input validation on imported profiles
   - Files stored in user-accessible locations

### Scope:

This security policy covers:
- The main application (`ipchanger.py`)
- Build configuration (`NetworkIPChanger.spec`)
- Network configuration functionality
- Profile management features

Out of scope:
- Third-party dependencies (PySide6, Python runtime)
- Operating system vulnerabilities
- Network infrastructure security

## Security Updates

Security updates will be released as:
- **Critical**: Emergency patch releases (v1.0.x)
- **Important**: Included in next minor release
- **Moderate**: Included in regular releases

Users will be notified through:
- GitHub security advisories
- Release notes
- Repository announcements

Thank you for helping keep Network IP Changer secure!