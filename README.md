<!--
<p align="center">
  <img src=""/>
</p>
-->
<p align="center">
  <img src="https://img.shields.io/github/license/ente0/snype">
  <img src="https://img.shields.io/badge/language-python-green" alt="Language: Python">
  <img src="https://img.shields.io/badge/dependencies-aircrack--ng-green" alt="Dependencies">
  <a href="https://github.com/ente0/snype/releases">
    <img src="https://img.shields.io/badge/release-v1.0.0-blue" alt="Version">
  </a>
</p>

<div align="center">
  
# snype: WPA Handshake Capture Utility

### **A streamlined command-line interface for aircrack-ng that simplifies wireless network reconnaissance and handshake capture through an intuitive menu system.**

</div>

> [!CAUTION]
> This tool is provided for educational and legitimate security testing purposes only. The author assumes no responsibility for any damages or legal consequences arising from the use of this tool. Always obtain explicit authorization before performing any network assessments. Unauthorized use is strictly prohibited and may violate local, national, and international laws.

---

## 🚀 Features

- **User-Friendly Interface**: Interactive menu for all wireless monitoring operations
- **Deauthentication Module**: Targeted client disconnection to facilitate handshake capture
- **Automated Monitoring**: Simplified packet capture with minimal configuration
- **Real-Time Feedback**: Live monitoring of capture progress and device status
- **Seamless Integration**: Works with standard aircrack-ng suite tools and hashcat for later cracking

## 📋 Requirements

### System Requirements

- Linux-based operating system
- Wireless adapter supporting monitor mode
- Python 3.6 or higher
- sudo/root privileges

### Dependencies

- hcxtools and hcxdumptool
- aircrack-ng suite (airmon-ng, airodump-ng, aireplay-ng)
- Python packages: termcolor

## 🔧 Installation

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/ente0/snype.git
cd snype
```

### Distribution-Specific Installation Commands

<details>
<summary>Click to expand installation commands</summary>

#### Debian/Ubuntu
```bash
sudo apt update && sudo apt install -y aircrack-ng python3 python3-pip python3-termcolor hcxtools hcxdumptool
```

#### Fedora
```bash
sudo dnf install -y aircrack-ng python3 python3-pip python3-termcolor hcxtools hcxdumptool
```

#### Arch Linux/Manjaro
```bash
sudo pacman -S aircrack-ng python python-pip python-termcolor hcxtools hcxdumptool
```
</details>

## 📖 Usage Guide

### Basic Workflow

1. **Reconnaissance**: Scan for available networks
2. **Target Selection**: Choose a network to monitor
3. **Monitoring**: Capture packets including handshakes
4. **Deauthentication**: Force clients to reconnect to capture handshakes
5. **Cracking**: Use wordlist to attempt password recovery

## 🎬 Walkthrough

### Step-by-Step Usage Guide

#### 1. Interface Configuration
- Select and configure wireless interfaces for monitoring and injection
- Activate monitor mode for your wireless adapter
<p align="center">
  <img src="https://github.com/user-attachments/assets/dd9cf807-412a-457c-9e71-82c090e36402" alt="Interface Configuration">
</p>


#### 2. Network Scanning
- Initiate network reconnaissance
- Discover available wireless networks
- View detailed network information
<p align="center">
  <img src="https://github.com/user-attachments/assets/15c3c3ce-1fb6-43ea-b4ae-331e9f088633" alt="Network Scanning">
</p>


#### 3. Target Selection
- Choose specific target network
- View network details and client information
<p align="center">
  <img src="https://github.com/user-attachments/assets/6c6e4d32-755a-438c-a2f7-f038d10b7286" alt="Access Point Selection">
</p>


#### 4. Detailed Target Information
- Analyze selected network's characteristics
- Prepare for targeted monitoring and attacks
<p align="center">
  <img src="https://github.com/user-attachments/assets/34224c95-4fab-4549-9807-d2118590ab04" alt="Target Details">
</p>


#### 5. Deauthentication Setup
- Dual-terminal approach for monitoring and injection
- Carefully orchestrate client disconnection
- Capture WPA handshake
<p align="center">
  <img src="https://github.com/user-attachments/assets/8b813b9c-2bc1-4179-968b-99ac2c7ffc52" alt="Deauthentication Process">
</p>


#### 6. Handshake Capture
- Successfully capture WPA handshake
- Generate compatible files for:
  - Hashcat (.hc22000)
  - Aircrack-ng (.cap)
<p align="center">
  <img src="https://github.com/user-attachments/assets/220f5001-13f3-4c7f-b215-f22d2002c418" alt="Handshake Capture">
</p>


#### 7. Cracking Preparation
- Review captured handshake files
- Prepare for password recovery
<p align="center">
  <img src="https://github.com/user-attachments/assets/3dad9376-a6d4-4b6f-81cb-d0c7fcf5a492" alt="Cracking Preparation">
</p>


#### 8. Wordlist Cracking
- Select appropriate wordlist
- Initiate password recovery process
- View cracking progress and results
<p align="center">
  <img src="https://github.com/user-attachments/assets/935cf6c2-25c2-424a-abca-892a4ba5e53e" alt="Wordlist Cracking">
</p>



## 🔓 Recommended Password Recovery: hashCrack

### Why Use hashCrack?

For advanced password cracking capabilities, we highly recommend integrating Snype with [hashCrack](https://github.com/ente0/hashCrack), a companion tool designed to enhance your password recovery workflow.

#### Key Features of hashCrack
- Advanced hashcat wrapper
- Multiple cracking strategies
- Extensive wordlist management
- Automated cracking profiles
- Support for various hash types

### Seamless Workflow Integration

1. **Capture Handshake with Snype**
   - Use Snype to capture WPA handshakes
   - Generate .hc22000 or .cap files

2. **Crack with hashCrack**
   ```bash
   # Direct integration
   hashcrack captured_handshake.hc22000
   ```

### Benefits
- Faster cracking performance
- More sophisticated attack modes
- Comprehensive wordlist handling
- Simplified cracking process

<p align="center">
  <a href="https://github.com/ente0/hashCrack">
    <img src="https://img.shields.io/badge/Check%20out-hashCrack-blue?style=for-the-badge&logo=github" alt="hashCrack Repository">
  </a>
</p>

> [!NOTE]
> Always ensure you have proper authorization before attempting any password recovery.


## 🔍 Troubleshooting

<details>
<summary>Common Issues and Solutions</summary>

### Interface Not Found
- Ensure your wireless adapter is properly connected
- Check if the adapter supports monitor mode: `iw list`
- Try using the exact interface name from `ifconfig` or `ip a`

### Permission Denied
- Run the tool with sudo privileges
- Ensure you have proper permissions for the wireless devices

### No Networks Found
- Verify the adapter is in monitor mode
- Try changing the adapter channel manually
- Check if the wireless adapter supports the required frequencies

### Deauthentication Not Working
- Ensure you're within range of the target network
- Some devices may have protections against deauthentication
- Try increasing the number of deauth packets sent
</details>

## 📚 Educational Resources

- [4-Way Handshake Explanation](https://notes.networklessons.com/security-wpa-4-way-handshake)
- [Radiotap Introduction](https://www.radiotap.org/)
- [Aircrack-ng Documentation](https://wiki.aircrack-ng.org/)

## 📝 License

This project is licensed under the GPL-3.0 - see the LICENSE file for details.

## 🤝 Support

- [Report Issues](https://github.com/ente0/hashCrack/issues)
- Contact: [enteo.dev@protonmail.com](mailto:enteo.dev@protonmail.com)

## 🔗 Related Projects

- [hashCrack](https://github.com/ente0/hashCrack)
- [hashcat-defaults](https://github.com/ente0/hashcat-defaults)
- [wpa2-wordlists](https://github.com/kennyn510/wpa2-wordlists)
- [paroleitaliane](https://github.com/napolux/paroleitaliane)
- [SecLists](https://github.com/danielmiessler/SecLists)