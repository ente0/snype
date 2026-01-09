import subprocess
import sys
import time
import os
from termcolor import colored
from functions import clear_screen
import shutil

def show_deauth_terminal_warning():
    """
    Display a warning message informing the user to open a new terminal for deauthentication
    with a header that adapts to the terminal width
    """
    import shutil
    from termcolor import colored

    try:
        terminal_width = shutil.get_terminal_size().columns
    except Exception:
        terminal_width = 70  
    
    header = "!" * terminal_width
    
    print(colored(header, 'yellow'))
    
    title = "IMPORTANT WARNING"
    padding = " " * ((terminal_width - len(title)) // 2)
    print(colored(f"{padding}{title}", 'yellow', attrs=['bold']))
    
    print(colored(header, 'yellow'))
    
    print(colored("\n[!] This terminal is now dedicated to monitoring traffic.", 'yellow'))
    print(colored("[!] To perform deauthentication attacks:", 'yellow'))
    
    instructions = [
        "KEEP THIS TERMINAL RUNNING",
        "Open a new terminal window",
        "Run the deauth script with: python3 deauth_attack.py"
    ]
    
    for i, instruction in enumerate(instructions, 1):
        print(colored(f" [{i}]. {instruction}", 'red'))
    
    print(colored("\n[!] Closing this monitoring session will stop packet capture!", 'red', attrs=['bold']))
    
    print(colored(header, 'yellow'))
    
    continue_prompt = input(colored("\nPress Enter to continue with monitoring or Ctrl+C to cancel...", 'green'))
    return

def run_targeted_airodump(interface=None, mac=None, channel=None):
    if not mac or not channel:
        try:
            with open("selected_network.txt", "r") as f:
                content = f.read().strip()
                parts = content.split(',')
                
                if len(parts) >= 3:
                    saved_bssid, saved_channel, saved_essid = parts[0], parts[1], parts[2]
                    
                    if not mac:
                        mac = saved_bssid
                    if not channel:
                        channel = saved_channel
        except FileNotFoundError:
            print(colored("[!] No network configuration file found.", 'red'))
            return False
        except Exception as e:
            print(colored(f"[!] Error reading network configuration: {e}", 'red'))
            return False
    
    if not interface:
        print(colored("[!] ERROR: No interface specified", 'red'))
        time.sleep(2)
        return False
    
    if not mac:
        print(colored("[!] ERROR: No target BSSID specified. Run reconnaissance first.", 'red'))
        time.sleep(2)
        return False
    
    if channel:
        channel_option = str(channel)
    else:
        print(colored("[!] WARNING: No channel specified, scanning might be less efficient", 'yellow'))
        channel_option = None
    
    print(colored(f"[+] Starting targeted monitoring on {mac} " +
                  (f"(channel {channel}) " if channel else "") +
                  f"using {interface}", 'cyan'))
    print(colored("[i] Press Ctrl+C to stop monitoring", 'yellow'))
    
    show_deauth_terminal_warning()
    
    subprocess.run(["sudo", "airmon-ng", "check", "kill"], capture_output=True)
    
    try:
        cmd = ["sudo", "airodump-ng", "--ignore-negative-one", "-w", "eapol", "--output-format", "pcap"]
        if channel_option:
            cmd.extend(["-c", channel_option])
        cmd.extend(["--bssid", mac, interface])

        process = subprocess.Popen(cmd)

        try:
            process.wait()
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
        
        return True
    
    except Exception as e:
        print(colored(f"\n[!] Error: {e}", 'red'))
        time.sleep(2)
        return False

if __name__ == "__main__":
    try:
        clear_screen()
        interface = sys.argv[1] if len(sys.argv) > 1 else None
        mac = sys.argv[2] if len(sys.argv) > 2 else None
        channel = sys.argv[3] if len(sys.argv) > 3 else None
        
        success = run_targeted_airodump(interface, mac, channel)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print(colored("\nExiting safely...", 'yellow'))
        sys.exit(0)