import os
import sys
import time
import subprocess
import shutil
from importlib import resources
from pathlib import Path
from datetime import datetime
from termcolor import colored

default_scripts = os.path.expanduser("~/snype")

def save_interface_config(primary_interface, secondary_interface=None):
    """
    Save interface configuration to a file
    
    Args:
    - primary_interface: Name of the primary interface
    - secondary_interface: Name of the secondary interface (optional)
    """
    if secondary_interface is None:
        secondary_interface = primary_interface
    
    try:
        with open("interface_config.txt", "w") as f:
            f.write(f"{primary_interface},{secondary_interface}")
        print(colored(f"[✓] Interfaces saved: Primary={primary_interface}, Secondary={secondary_interface}", 'green'))
    except Exception as e:
        print(colored(f"[!] Error saving interface configuration: {e}", 'red'))

def select_primary_interface():
    """
    Select and validate the primary wireless interface for monitoring
    
    Returns:
    - Primary interface name or None if invalid
    """
    print(colored("\nAvailable interfaces:", 'yellow'))
    subprocess.run(["iwconfig"], capture_output=False)
    
    print(colored("\n[+] Select primary interface:", 'green'))
    iface1 = input(colored("Primary interface (for monitoring): ", 'green')).strip()
    
    try:
        subprocess.run(["iwconfig", iface1], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        save_interface_config(iface1)
        
        return iface1
    
    except subprocess.CalledProcessError:
        print(colored("[!] Primary interface not found. Please try again.", 'red'))
        time.sleep(2)
        return None

def select_secondary_interface(primary_interface=None):
    """
    Select and validate the secondary wireless interface for injection
    
    Args:
    - primary_interface: Optional primary interface to use as default
    
    Returns:
    - Secondary interface name or None if invalid
    """
    print(colored("\n[+] Select secondary interface:", 'green'))
    iface2 = input(colored("Secondary interface (for injection, leave empty to use same): ", 'green')).strip()
    
    if not iface2 and primary_interface:
        iface2 = primary_interface
        print(colored(f"[i] Using {primary_interface} for both monitoring and injection", 'yellow'))
    
    try:
        subprocess.run(["iwconfig", iface2], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        save_interface_config(primary_interface or iface2, iface2)
        
        return iface2
    
    except subprocess.CalledProcessError:
        print(colored("[!] Secondary interface not found. Please try again.", 'red'))
        time.sleep(2)
        return None

def define_ifaces():
    """
    Wrapper function to maintain backwards compatibility
    Combines primary and secondary interface selection
    
    Returns:
    - Tuple of (primary interface, secondary interface) or (None, None) if invalid
    """
    iface1 = select_primary_interface()
    if not iface1:
        return None, None
    
    iface2 = select_secondary_interface(iface1)
    if not iface2:
        return None, None
    
    return iface1, iface2
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_saved_interface_info():
    """Get saved interface information if available"""
    if os.path.exists("interface_config.txt"):
        try:
            with open("interface_config.txt", "r") as f:
                content = f.read().strip().split(',')
                if len(content) >= 2:
                    return content[0], content[1]
                return content[0], content[0]
        except Exception:
            pass
    return None, None

def get_saved_network_info():
    """Get saved network (BSSID) information if available"""
    try:
        if os.path.exists("selected_network.txt"):
            with open("selected_network.txt", "r") as f:
                content = f.read().strip()
                parts = content.split(',')
                if len(parts) >= 3:
                    bssid, channel, essid = parts[0], parts[1], parts[2]
                    
                    if ':' in bssid and len(bssid.split(':')) == 6:
                        return bssid, channel, essid
                    
                    print(colored("[!] Invalid network configuration. Removing config file.", 'red'))
                    os.remove("selected_network.txt")
                    return None, None, None
                else:
                    print(colored("[!] Incomplete network configuration. Removing config file.", 'red'))
                    os.remove("selected_network.txt")
                    return None, None, None
        
        return None, None, None
    
    except Exception as e:
        print(colored(f"[!] Error reading network configuration: {e}", 'red'))
        if os.path.exists("selected_network.txt"):
            os.remove("selected_network.txt")
        return None, None, None

def show_status_info():
    """Generate status information string for interfaces and target"""
    iface1, iface2 = get_saved_interface_info()
    bssid, channel, essid = get_saved_network_info()

    status = []
    if iface1:
        status.append(f"Monitor: {colored(iface1, 'green')}")
        if iface2 and iface2 != iface1:
            status.append(f"Inject: {colored(iface2, 'green')}")

    if bssid:
        target_info = f"Target: {colored(bssid, 'yellow')}"
        if channel:
            target_info += f" (Ch: {colored(channel, 'yellow')})"
        status.append(target_info)
        if essid:
            status.append(f"ESSID: {colored(essid, 'yellow')}")
    
    return "   " + " | ".join(status) if status else ""


def show_menu1():
    terminal_width = shutil.get_terminal_size().columns
    separator = "=" * terminal_width

    ascii_art = """
    
                         _____ ____   __ __  ____   ___ 
                        / ___/|    \ |  |  ||    \ /  _]
                       (   \_ |  _  ||  |  ||  o  )  [_ 
                        \__  ||  |  ||  ~  ||   _/    _]
                        /  \ ||  |  ||___, ||  | |   [_ 
                        \    ||  |  ||     ||  | |     |
                         \___||__|__||____/ |__| |_____|

            For more information, visit: https://github.com/ente0/snype
    """
    print(colored(ascii_art, 'cyan'))
    print(colored(separator, 'cyan'))
    print(colored(f"   Welcome to snype!", 'cyan', attrs=['bold']))
    
    status_info = show_status_info()
    if status_info:
        print(status_info)
    
    print(colored(separator, 'cyan'))

    options = [
        f"{colored('[1]', 'cyan', attrs=['bold'])} Set 1st interface",
        f"{colored('[2]', 'cyan', attrs=['bold'])} Set 2nd interface (optional)",
    ]
    print("\n   " + "\n   ".join(options))

    print(colored("\n" + separator, 'cyan'))

    user_option1 = input(colored("\nEnter option (1-2, Q to quit): ", 'cyan', attrs=['bold'])).strip().lower()

    return user_option1


def show_menu2():
    terminal_width = shutil.get_terminal_size().columns
    separator = "=" * terminal_width
    dash_separator = "-" * terminal_width

    ascii_art = """
    
                         _____ ____   __ __  ____   ___ 
                        / ___/|    \ |  |  ||    \ /  _]
                       (   \_ |  _  ||  |  ||  o  )  [_ 
                        \__  ||  |  ||  ~  ||   _/    _]
                        /  \ ||  |  ||___, ||  | |   [_ 
                        \    ||  |  ||     ||  | |     |
                         \___||__|__||____/ |__| |_____|

            For more information, visit: https://github.com/ente0/snype
    """
    print(colored(ascii_art, 'cyan'))
    print(colored(separator, 'cyan'))
    print(colored(f"   Welcome to snype!", 'cyan', attrs=['bold']))
    
    hc22000_files, cap_files, processed_cap_files = check_and_convert_cap_files()    
    #if processed_cap_files:
    #    print(colored(f"   [*] Processing {len(processed_cap_files)} .cap file(s) in background", 'yellow'))
    
    if hc22000_files:
        print(colored(f"   [✓] {len(hc22000_files)} .hc22000 file(s) generated:", 'green'))
        for file in hc22000_files:
            print(colored(f"       - {file}", 'green'))
    
    if cap_files:
        print(colored(f"   [✓] {len(cap_files)} .cap file(s) found:", 'green'))
        for file in cap_files:
            print(colored(f"       - {file}", 'green'))

    print(colored(separator, 'cyan'))

    status_info = show_status_info()
    if status_info:
        print(status_info)
    
    print(colored(separator, 'cyan'))

    options = [
        f"{colored('[1]', 'cyan', attrs=['bold'])} Network Scanning",
        f"{colored('[2]', 'cyan', attrs=['bold'])} Monitor Target Traffic",
        f"{colored('[3]', 'cyan', attrs=['bold'])} Deauthentication Attack",
        f"{colored('[4]', 'cyan', attrs=['bold'])} Wordlist Cracking",
    ]

    utility_options = [
        f"{colored('[5]', 'magenta', attrs=['bold'])} Flush Services",
        f"{colored('[6]', 'magenta', attrs=['bold'])} Change Target BSSID",
        f"{colored('[7]', 'magenta', attrs=['bold'])} Modify Interfaces",
        f"{colored('[8]', 'magenta', attrs=['bold'])} Clear Configuration",
        f"{colored('[9]', 'magenta', attrs=['bold'])} Convert EAPOL to hc22000",
        f"{colored('[10]', 'magenta', attrs=['bold'])} Delete Capture Files",
        f"{colored('[11]', 'magenta', attrs=['bold'])} Clear ESSID Lists",
    ]


    print(colored("\n ATTACK MODULES:", 'blue', attrs=['bold']))
    print("\n " + "\n ".join(options))
    print("\n" + colored(dash_separator, 'cyan'))
    print(colored("\n UTILITY FUNCTIONS:", 'magenta', attrs=['bold']))
    print("\n " + "\n ".join(utility_options))
    
    print(colored("\n" + separator, 'magenta'))

    user_option2 = input(colored("\nEnter option (1-11, Q to quit): ", 'cyan', attrs=['bold'])).strip().lower()

    return user_option2

def get_package_script_path(script_name):
    """
    Find the path to the script, checking multiple possible locations
    """
    potential_paths = [
        os.path.join(os.path.dirname(__file__), script_name),  # Current directory
        os.path.join(os.path.dirname(__file__), 'scripts', script_name),  # scripts subdirectory
        os.path.join(os.path.expanduser('~'), 'snype', script_name),  # User's home directory
        script_name 
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"Script {script_name} not found in expected locations")

def handle_option(option, iface1=None, iface2=None, channel=None, selected_bssid=None):
    """
    Handle different menu options by executing corresponding scripts
    """
    script_map = {
        "1": "airodump_gathering.py",
        "2": "airodump_target.py",
        "3": "deauth_attack.py",
    }
    
    print("...", flush=True)
    
    if option.lower() == "q":
        print(colored("Done! Exiting...", 'yellow'))
        sys.exit(0)
    
    if option == "5":
        iface1, iface2 = get_saved_interface_info()
        new_bssid = scan_networks_and_select_bssid(iface1)
        if new_bssid:
            print(colored(f"[✓] Target BSSID updated to: {new_bssid}", 'green'))
        return
    
    if option == "6":
        new_iface1, new_iface2 = define_ifaces()
        if new_iface1:
            print(colored(f"[✓] Interfaces updated: Primary={new_iface1}, Secondary={new_iface2 or new_iface1}", 'green'))
        return
    
    if option == "7":
        clear_config_files()
        return
    
    if option == "4":
        flush_services()
        return
    
    if option == "8":
        convert_eapol()
        return
    
    if option == "9":
        delete_cap_files()
        return
    
    if option == "10":
        delete_essidlist_files()
        return
    
    script_name = script_map.get(option)
    if not script_name:
        print(colored("Invalid option. Please try again.", 'red'))
        return
    
    try:
        if option == "3" and (not selected_bssid or not iface1):
            print(colored("[!] Missing BSSID or interface for deauthentication attack.", 'red'))
            print(colored("Please select a target network and interface first.", 'yellow'))
            time.sleep(2)
            return
        
        script_path = get_package_script_path(script_name)
        print(colored(f'Executing {script_path}', 'green'))
        time.sleep(1)
        
        python_cmd = "python3"
        cmd = f'{python_cmd} "{script_path}"'
        
        if iface1:
            cmd += f' "{iface1}"'
        
        if iface2 and option == "3":
            cmd += f' "{iface2}"'
        
        if selected_bssid and option in ["2", "3"]:
            cmd += f' "{selected_bssid}"'
        
        if channel and option in ["2", "3"]:
            cmd += f' "{channel}"'
        
        result = os.system(cmd)
        
        #if result != 0:
        #    print(colored(f"Script execution failed with exit code {result}", 'red'))
    
    except FileNotFoundError as e:
        print(colored(f"Error: {e}", 'red'))
        print(colored("Ensure the script exists in the expected locations.", 'yellow'))
    
    except Exception as e:
        print(colored(f"Unexpected error: {e}", 'red'))
    
    input("Press Enter to return to the menu...")

def clear_config_files():
    """Clear configuration files (selected_network.txt and interface_config.txt)"""
    try:
        files_to_remove = ["selected_network.txt", "interface_config.txt"]
        removed_files = []
        
        for file in files_to_remove:
            if os.path.exists(file):
                os.remove(file)
                removed_files.append(file)
        
        if removed_files:
            print(colored(f"[✓] Configuration files cleared: {', '.join(removed_files)}", 'green'))
        else:
            print(colored("[i] No configuration files found to clear.", 'yellow'))
    except Exception as e:
        print(colored(f"[!] Error clearing configuration files: {e}", 'red'))
    
    time.sleep(2)


def animate_text(text, delay):
    for i in range(len(text) + 1):
        clear_screen()
        print(text[:i], end="", flush=True)
        time.sleep(delay)


def get_package_script_path(script_name: str) -> Path:
    try:
        package_path = resources.files('snype') / script_name
        
        if not package_path.exists():
            raise FileNotFoundError(f"Script {script_name} not found in package")
        
        return package_path
    except (ImportError, AttributeError):
        import pkg_resources
        package_path = pkg_resources.resource_filename('snype', f'{script_name}')
        
        if not os.path.exists(package_path):
            raise FileNotFoundError(f"Script {script_name} not found in package")
        
        return Path(package_path)

def define_logs(session):
    home_dir = os.path.expanduser("~")
    log_dir = os.path.join(home_dir, ".snype", "logs", session)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def flush_services():
    """Flush networking services and reset interfaces to managed mode"""
    print(colored("[+] Flushing networking services and resetting interfaces...", 'yellow'))

    iface1, iface2 = get_saved_interface_info()
    
    try:

        print(colored("[-] Killing interfering processes...", 'yellow'))
        subprocess.run(["sudo", "airmon-ng", "check", "kill"], capture_output=True)
        
        print(colored(f"[-] Resetting {iface1} to managed mode...", 'yellow'))
        subprocess.run(["sudo", "ifconfig", iface1, "down"], capture_output=True)
        subprocess.run(["sudo", "iw", "dev", iface1, "set", "type", "managed"], capture_output=True)
        subprocess.run(["sudo", "ifconfig", iface1, "up"], capture_output=True)
        
        if iface2:
            print(colored(f"[-] Resetting {iface2} to managed mode...", 'yellow'))
            subprocess.run(["sudo", "ifconfig", iface2, "down"], capture_output=True)
            subprocess.run(["sudo", "iw", "dev", iface2, "set", "type", "managed"], capture_output=True)
            subprocess.run(["sudo", "ifconfig", iface2, "up"], capture_output=True)

        print(colored("[-] Restarting network services...", 'yellow'))
        subprocess.run(["sudo", "systemctl", "restart", "wpa_supplicant"], capture_output=True)
        subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], capture_output=True)
        
        time.sleep(2)
        print(colored("[✓] Services flushed and interfaces reset successfully", 'green'))
        
        return iface1, iface2
        
    except Exception as e:
        print(colored(f"[!] Error during operation: {e}", 'red'))
        time.sleep(1)
        return None, None


def scan_networks_and_select_bssid(interface):
    """Run airodump-ng and allow user to select a BSSID"""
    import tempfile
    
    if not interface:
        print(colored("[!] No interface selected. Please define interfaces first.", 'red'))
        time.sleep(2)
        return None
    
    clear_screen()
    print(colored("[+] Scanning networks with airodump-ng", 'cyan'))
    print(colored("[i] Press Ctrl+C ", 'yellow') + 
      colored("TWO TIMES", 'yellow', attrs=['bold']) + 
      colored(" when you've found the target network", 'yellow'))
    time.sleep(2)
    tmp_file = tempfile.NamedTemporaryFile(delete=False).name
    
    try:
        subprocess.run(["sudo", "airmon-ng", "check", "kill"], capture_output=True)
        
        process = subprocess.Popen(["sudo", "airodump-ng", "-w", tmp_file, "--output-format", "csv", interface])
        
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            
        csv_file = f"{tmp_file}-01.csv"
        if not os.path.exists(csv_file):
            print(colored("[!] No networks were captured.", 'red'))
            time.sleep(2)
            return None
            
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        station_index = next((i for i, line in enumerate(lines) if "Station MAC" in line), len(lines))
        
        bssid_lines = [line.strip() for line in lines[1:station_index] if line.strip() and "BSSID" not in line]
        
        if not bssid_lines:
            print(colored("[!] No networks found.", 'red'))
            time.sleep(2)
            return None
            
        clear_screen()
        print(colored("[+] Select Target Network:", 'green'))
        print(colored("=" * 70, 'cyan'))
        print(colored("ID  BSSID              CH  PWR  ESSID", 'cyan'))
        print(colored("-" * 70, 'cyan'))
        
        for i, line in enumerate(bssid_lines):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 14: 
                bssid = parts[0]
                channel = parts[3]
                power = parts[8]
                essid = parts[13].strip()
                print(colored(f"{i:<3} {bssid:<18} {channel:<3} {power:<4} {essid}", 'blue'))
        
        try:
            selection = int(input(colored("\nEnter network ID to select: ", 'green')))
            if 0 <= selection < len(bssid_lines):
                parts = [part.strip() for part in bssid_lines[selection].split(',')]
                selected_bssid = parts[0]
                channel = parts[3]
                essid = parts[13].strip()
                print(colored(f"[✓] Selected: BSSID={selected_bssid}, CH={channel}, ESSID={essid}", 'green'))
                
                with open("selected_network.txt", "w") as f:
                    f.write(f"{selected_bssid},{channel},{essid}")
                
                time.sleep(2)
                return selected_bssid
            else:
                print(colored("[!] Invalid selection.", 'red'))
                time.sleep(2)
                return None
        except ValueError:
            print(colored("[!] Invalid input. Please enter a number.", 'red'))
            time.sleep(2)
            return None
            
    finally:
        for ext in ["-01.csv", "-01.kismet.csv", "-01.kismet.netxml", "-01.cap"]:
            try:
                if os.path.exists(f"{tmp_file}{ext}"):
                    os.remove(f"{tmp_file}{ext}")
            except Exception:
                pass

def delete_cap_files():
    """Delete capture files in the current directory"""
    print(colored("[+] Deleting capture files...", 'yellow'))
    try:
        confirm = input(colored("Are you sure you want to delete all .cap files in the current directory? (y/n): ", 'cyan'))
        
        if confirm.lower() != 'y':
            print(colored("Operation cancelled.", 'yellow'))
            time.sleep(2)
            return
        
        cap_files = [f for f in os.listdir('.') if f.endswith('.cap')]
        
        if not cap_files:
            print(colored("No .cap files found in the current directory.", 'yellow'))
            time.sleep(2)
            return
        
        print(colored("The following files will be deleted:", 'yellow'))
        for file in cap_files:
            print(colored(f" - {file}", 'cyan'))
        
        final_confirm = input(colored("Proceed with deletion? (y/n): ", 'cyan'))
        
        if final_confirm.lower() != 'y':
            print(colored("Operation cancelled.", 'yellow'))
            time.sleep(2)
            return
        
        deleted_count = 0
        for file in cap_files:
            try:
                os.remove(file)
                deleted_count += 1
            except Exception as e:
                print(colored(f"[!] Failed to delete {file}: {e}", 'red'))
        
        print(colored(f"[✓] Successfully deleted {deleted_count} capture files.", 'green'))
        time.sleep(2)
    except Exception as e:
        print(colored(f"[!] Error during operation: {e}", 'red'))
        time.sleep(2)

def delete_essidlist_files():
    """Delete all essidlist files in the current directory, handshakes directory, and ESSID subdirectories"""
    print(colored("[+] Searching for essidlist files to delete...", 'yellow'))
    
    try:
        current_dir_files = [f for f in os.listdir('.') if f.startswith('essidlist_') and f.endswith('.txt')]
        
        handshakes_files = []
        if os.path.exists('handshakes') and os.path.isdir('handshakes'):
            main_dir_files = [os.path.join('handshakes', f) for f in os.listdir('handshakes') 
                              if f.startswith('essidlist_') and f.endswith('.txt')]
            handshakes_files.extend(main_dir_files)
            
            for subdir in os.listdir('handshakes'):
                subdir_path = os.path.join('handshakes', subdir)
                if os.path.isdir(subdir_path):
                    subdir_files = [os.path.join(subdir_path, f) for f in os.listdir(subdir_path) 
                                    if f.startswith('essidlist_') and f.endswith('.txt')]
                    handshakes_files.extend(subdir_files)
        
        total_files = len(current_dir_files) + len(handshakes_files)
        
        if total_files == 0:
            print(colored("[!] No essidlist files found.", 'yellow'))
            time.sleep(2)
            return
        
        confirm = input(colored(f"[?] Found {total_files} essidlist files. Delete them? [y/N]: ", 'cyan')).lower()
        
        if confirm != 'y':
            print(colored("[!] Operation cancelled.", 'yellow'))
            time.sleep(2)
            return
        
        for file in current_dir_files:
            try:
                os.remove(file)
                print(colored(f"[✓] Deleted: {file}", 'green'))
            except Exception as e:
                print(colored(f"[!] Error deleting {file}: {e}", 'red'))
               
        for file in handshakes_files:
            try:
                os.remove(file)
                print(colored(f"[✓] Deleted: {file}", 'green'))
            except Exception as e:
                print(colored(f"[!] Error deleting {file}: {e}", 'red'))
                
        print(colored(f"[+] Successfully deleted {total_files} essidlist files.", 'green'))
        time.sleep(2)
        
    except Exception as e:
        print(colored(f"[!] Error while deleting essidlist files: {e}", 'red'))
        time.sleep(2)
        
def check_and_convert_cap_files():
    """
    Check for .cap files and convert them to hc22000 format in the background.
    Returns:
    - A list of existing hc22000 files in the handshakes folder
    - A list of existing .cap files in the handshakes folder
    - A list of .cap files that were processed
    """
    def find_files_in_directory(directory, extensions):
        found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    found_files.append(os.path.join(root, file))
        return found_files

    cap_files = [f for f in os.listdir('.') if f.endswith('.cap')]
    handshakes_dir = "handshakes"
    
    if not os.path.exists(handshakes_dir):
        return [], [], []

    if not cap_files:
        existing_hc22000_files = find_files_in_directory(handshakes_dir, ['.hc22000'])
        existing_cap_files = find_files_in_directory(handshakes_dir, ['.cap'])
        return existing_hc22000_files, existing_cap_files, []

    hc22000_files = []
    processed_cap_files = []
    
    try:
        cleanup_essidlist_files() 
    except NameError:
        pass

    for cap_file in cap_files:
        try:
            base_name = os.path.splitext(cap_file)[0]
            hc22000_file = f"{base_name}.hc22000"
            essidlist = os.path.join(handshakes_dir, f"essidlist_{int(time.time())}.txt")
            
            conversion_cmd = [
                'hcxpcapngtool',
                '-o', hc22000_file,
                '-E', essidlist,
                cap_file
            ]
            
            subprocess.run(conversion_cmd, capture_output=True)
            processed_cap_files.append(cap_file)

            if os.path.exists(hc22000_file) and os.path.getsize(hc22000_file) > 0:
                if os.path.exists(essidlist):
                    with open(essidlist, 'r') as f:
                        essids = [line.strip() for line in f if line.strip()]
                    
                    for essid in essids:
                        safe_essid = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in essid)
                        network_dir = os.path.join(handshakes_dir, safe_essid)
                        os.makedirs(network_dir, exist_ok=True)
                        
                        dest_hc22000 = os.path.join(network_dir, hc22000_file)
                        shutil.move(hc22000_file, dest_hc22000)
                        
                        dest_cap = os.path.join(network_dir, cap_file)
                        shutil.move(cap_file, dest_cap)
                        
                    if os.path.exists(essidlist):
                        os.remove(essidlist)

        except Exception as e:
            print(f"Error processing {cap_file}: {e}")

    existing_hc22000_files = find_files_in_directory(handshakes_dir, ['.hc22000'])
    existing_cap_files = find_files_in_directory(handshakes_dir, ['.cap'])
    
    return existing_hc22000_files, existing_cap_files, processed_cap_files

def auto_convert_latest_cap_file():
    """
    Automatically convert the most recent .cap file to hc22000 format without user input
    Moves both .cap and .hc22000 files to network-specific directories
    
    Returns:
    - Path to the generated hc22000 file
    - Name of the processed .cap file
    """
    def find_latest_cap_file():
        """
        Find the most recent .cap file based on modification time
        """
        cap_files = [f for f in os.listdir('.') if f.endswith('.cap')]
        if not cap_files:
            return None
        latest_cap_file = max(
            cap_files,
            key=lambda f: os.path.getmtime(f)
        )
        return latest_cap_file

    handshakes_dir = "handshakes"
    os.makedirs(handshakes_dir, exist_ok=True)
    
    cap_file = find_latest_cap_file()
    if not cap_file:
        return None, None
    
    try:
        base_name = os.path.splitext(cap_file)[0]
        hc22000_file = f"{base_name}.hc22000"
        essidlist = os.path.join(handshakes_dir, f"essidlist_{int(time.time())}.txt")
        
        conversion_cmd = [
            'hcxpcapngtool',
            '-o', hc22000_file,
            '-E', essidlist,
            cap_file
        ]
        
        subprocess.run(conversion_cmd, capture_output=True, check=True)
        
        if os.path.exists(hc22000_file) and os.path.getsize(hc22000_file) > 0:
            if os.path.exists(essidlist):
                with open(essidlist, 'r') as f:
                    essids = [line.strip() for line in f if line.strip()]
                
                for essid in essids:
                    safe_essid = "".join(
                        c if c.isalnum() or c in ['-', '_'] else '_'
                        for c in essid
                    )
                    network_dir = os.path.join(handshakes_dir, safe_essid)
                    os.makedirs(network_dir, exist_ok=True)
                    
                    dest_hc22000 = os.path.join(network_dir, os.path.basename(hc22000_file))
                    shutil.move(hc22000_file, dest_hc22000)
                    
                    dest_cap = os.path.join(network_dir, os.path.basename(cap_file))
                    shutil.move(cap_file, dest_cap)
                    
                    hc22000_file = dest_hc22000
                    cap_file = dest_cap
            
            if os.path.exists(essidlist):
                os.remove(essidlist)
            
            return hc22000_file, cap_file
    
    except Exception as e:
        print(f"Error converting {cap_file}: {e}")
        return None, None

def convert_eapol():
    """Convert EAPOL packets to hashcat format with graceful interrupt handling"""
    print(colored("[+] Converting EAPOL packets to hashcat format...", "yellow"))
    
    try:
        cap_files = [f for f in os.listdir('.') if f.endswith('.cap')]
        handshakes_dir = "handshakes"
        
        if not cap_files:
            print(colored("[!] No .cap files found in the current directory.", "red"))
            time.sleep(2)
            return
        
        print(colored("Convert:", "cyan"))
        print("(1) Single file")
        print("(2) Multiple files")
        print("(3) All .cap files in directory")
        
        while True:
            try:
                choice = input(colored("Enter option (1/2/3, Q to quit): ", "green")).strip().lower()
                
                if choice == 'q':
                    return
                
                choice = int(choice)
                
                if choice not in [1, 2, 3]:
                    print(colored("[!] Invalid option. Please choose 1, 2, or 3.", "red"))
                    continue
                
                break
            except ValueError:
                print(colored("[!] Please enter a valid number.", "red"))
        
        if choice == 1:
            print(colored("\nAvailable .cap files:", "yellow"))
            for idx, file in enumerate(cap_files, 1):
                print(f"{idx}. {file}")
            
            while True:
                try:
                    file_choice = input(colored("Select file number (Q to quit): ", "cyan")).strip().lower()
                    
                    if file_choice == 'q':
                        return
                    
                    file_choice = int(file_choice)
                    
                    if 1 <= file_choice <= len(cap_files):
                        selected_file = cap_files[file_choice - 1]
                        cap_files = [selected_file]
                        break
                    else:
                        print(colored("[!] Invalid file number.", "red"))
                except ValueError:
                    print(colored("[!] Please enter a valid number.", "red"))
        
        elif choice == 2:
            print(colored("\nAvailable .cap files:", "yellow"))
            for idx, file in enumerate(cap_files, 1):
                print(f"{idx}. {file}")
            
            selected_files = []
            while True:
                try:
                    files_choice = input(colored("Enter file numbers separated by comma (Q to quit): ", "cyan")).strip().lower()
                    
                    if files_choice == 'q':
                        return
                    
                    selected_indices = [int(x.strip()) for x in files_choice.split(',')]
                    
                    if all(1 <= idx <= len(cap_files) for idx in selected_indices):
                        selected_files = [cap_files[idx-1] for idx in selected_indices]
                        cap_files = selected_files
                        break
                    else:
                        print(colored("[!] Invalid file numbers.", "red"))
                except ValueError:
                    print(colored("[!] Please enter valid numbers.", "red"))
        
        os.makedirs(handshakes_dir, exist_ok=True)
        
        for cap_file in cap_files:
            try:
                base_name = os.path.splitext(cap_file)[0]
                hc22000_file = os.path.join(handshakes_dir, f"{base_name}.hc22000")
                essidlist = os.path.join(handshakes_dir, f"essidlist_{int(time.time())}.txt")
                
                conversion_cmd = [
                    'hcxpcapngtool',
                    '-o', hc22000_file,
                    '-E', essidlist,
                    cap_file
                ]
                
                print(colored(f"\n[*] Converting {cap_file}...", "green"))
                subprocess.run(conversion_cmd, check=True, capture_output=True)
                
                print(colored(f"[+] Converted {cap_file} successfully!", "green"))
            
            except subprocess.CalledProcessError as e:
                print(colored(f"[!] Error converting {cap_file}: {e}", "red"))
        
        print(colored("\n[+] Conversion completed!", "green"))
        time.sleep(2)
    
    except KeyboardInterrupt:
        print(colored("\n[*] Conversion process interrupted.", "yellow"))
        time.sleep(2)
    
    except Exception as e:
        print(colored(f"[!] An unexpected error occurred: {e}", "red"))
        time.sleep(2)

def cleanup_essidlist_files():
    """Automatically delete all essidlist files in the current directory and handshakes directory"""
    try:
        current_dir_files = [f for f in os.listdir('.') if f.startswith('essidlist_') and f.endswith('.txt')]
        handshakes_files = []
        
        if os.path.exists('handshakes') and os.path.isdir('handshakes'):
            main_dir_files = [os.path.join('handshakes', f) for f in os.listdir('handshakes') 
                              if f.startswith('essidlist_') and f.endswith('.txt')]
            handshakes_files.extend(main_dir_files)
            
            for subdir in os.listdir('handshakes'):
                subdir_path = os.path.join('handshakes', subdir)
                if os.path.isdir(subdir_path):
                    subdir_files = [os.path.join(subdir_path, f) for f in os.listdir(subdir_path) 
                                    if f.startswith('essidlist_') and f.endswith('.txt')]
                    handshakes_files.extend(subdir_files)
        
        for file in current_dir_files:
            try:
                os.remove(file)
            except Exception:
                pass
        
        for file in handshakes_files:
            try:
                os.remove(file)
            except Exception:
                pass
    except Exception:
        pass