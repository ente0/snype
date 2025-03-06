import sys

from termcolor import colored
from functions import (
    scan_networks_and_select_bssid
)
def run_airodump(interface=None):

    print(colored(f"[+] Starting network scanning on interface {interface}", 'cyan'))
    
    global bssid
    bssid = scan_networks_and_select_bssid(interface)
    
    if bssid:
        print(colored(f"[✓] BSSID {bssid} saved for future use", 'green'))
        return bssid
    else:
        print(colored("\n[!] No BSSID selected", 'yellow'))
        
        manual_bssid = input(colored("\nEnter target BSSID manually (or press Enter to skip): ", 'green'))
        if manual_bssid:
            channel = input(colored("Enter channel (optional): ", 'green'))
            essid = input(colored("Enter ESSID (optional): ", 'green'))
            
            with open("selected_network.txt", "w") as f:
                f.write(f"{manual_bssid},{channel},{essid}")
            
            print(colored(f"[✓] BSSID {manual_bssid} saved for future use", 'green'))
            return manual_bssid
    
    return None

if __name__ == "__main__":
    try:
        interface = sys.argv[1] if len(sys.argv) > 1 else None
        run_airodump(interface)
    except KeyboardInterrupt:
        print(colored("\nExiting safely...", 'yellow'))
        sys.exit(0)