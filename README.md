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

### Command Examples

```bash
# Start the tool
python snype.py

# When prompted, select:
# 1. Network Scanning
# 2. Monitor Target Traffic
# 3. Deauthentication Attack
# 4. Wordlist Cracking
```

### Wordlist Cracking

The fourth menu option allows you to:
- Select a previously captured handshake
- Choose a wordlist
- Attempt password recovery using aircrack-ng

Ensure you have:
- Valid .cap handshake capture file
- Prepared wordlist file
<!--
## 🎬 Demo
-->
<p align="center">
  <video src="" />
</p>

## 🧰 Advanced Usage

### Handshake Capture Techniques

- **Passive Monitoring**: Wait for natural handshakes (slower but stealthier)
- **Active Deauthentication**: Force client reconnections to capture handshakes quickly
- **Targeted Deauthentication**: Focus on specific high-value clients

<!--
### Integration with hashCrack
-->


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