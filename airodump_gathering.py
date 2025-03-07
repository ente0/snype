import sys
from termcolor import colored
from functions import (
    scan_networks_and_select_bssid
)

def run_airodump(interface=None):
    print(colored(f"[+] Starting network scanning on interface {interface}", 'cyan'))
    
    try:
        global bssid
        bssid = scan_networks_and_select_bssid(interface)
        
        if bssid:
            print(colored(f"[✓] BSSID {bssid} saved for future use", 'green'))
            return bssid
        else:
            print(colored("\n[!] No BSSID selected", 'yellow'))
            try:
                manual_bssid = input(colored("\nEnter target BSSID manually (or press Enter to skip): ", 'green'))
                if manual_bssid:
                    channel = input(colored("Enter channel (optional): ", 'green'))
                    essid = input(colored("Enter ESSID (optional): ", 'green'))
                    with open("selected_network.txt", "w") as f:
                        f.write(f"{manual_bssid},{channel},{essid}")
                    print(colored(f"[✓] BSSID {manual_bssid} saved for future use", 'green'))
                    return manual_bssid
                return None
            except KeyboardInterrupt:
                print(colored("\n\n[!] Manual input cancelled", 'yellow'))
                return None
    except KeyboardInterrupt:
        print(colored("\n\n[!] Network scanning cancelled", 'yellow'))
        return None

if __name__ == "__main__":
    try:
        interface = sys.argv[1] if len(sys.argv) > 1 else None
        result = run_airodump(interface)
        print(colored(f"\nOperation completed. BSSID selected: {result if result else 'None'}", 'cyan'))
    except KeyboardInterrupt:
        print(colored("\nExiting safely...", 'yellow'))
    except Exception as e:
        print(colored(f"\n[!] Error: {e}", 'red'))
    finally:
        sys.exit(0)