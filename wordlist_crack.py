import os
import sys
import subprocess
import argparse
from termcolor import colored
import logging
import time
import signal
import re
import shutil
from functions import(
    check_and_convert_cap_files, view_saved_passwords, save_password, load_found_passwords, print_header
)

class WifiCrackingTool:
    def __init__(self):
        """Initialize the WiFi Cracking Tool"""
        self.setup_logging()
        self.check_dependencies()
        self.found_passwords = {} 
        self.term_width = shutil.get_terminal_size().columns

    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def check_dependencies(self):
        """Check if required tools are installed"""
        dependencies = ['aircrack-ng', 'hcxpcapngtool']
        for tool in dependencies:
            try:
                subprocess.run([tool, '--help'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL, 
                               check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.error(f"{tool} is not installed. Please install it.")
                sys.exit(1)

    def list_cap_files(self):
        """Find all .cap files in the current directory and handshakes subdirectory"""
        try:
            current_dir_files = [f for f in os.listdir() if f.endswith(".cap")]
            
            handshakes_dir = "handshakes"
            handshakes_files = []
            
            if os.path.exists(handshakes_dir) and os.path.isdir(handshakes_dir):
                for root, dirs, files in os.walk(handshakes_dir):
                    handshakes_files.extend([
                        os.path.join(root, f) for f in files if f.endswith(".cap")
                    ])
            
            all_cap_files = current_dir_files + handshakes_files
            
            return all_cap_files
        except PermissionError:
            self.logger.error("Permission denied when listing files.")
            return []
        except Exception as e:
            self.logger.error(f"Error listing .cap files: {e}")
            return []

    def select_cap_file(self, cap_files):
        """Select a .cap file from the available list"""
        if not cap_files:
            self.logger.warning(colored("[!] No .cap files found in the directory or handshakes!", "red"))
            time.sleep(2)
            return None
        print("\n")
        print_header("SELECT CAPTURE FILE", "yellow","-")
        for idx, file in enumerate(cap_files, 1):
            print(f"{colored(f'[{idx}]', 'yellow')} {file}")

        try:
            while True:
                choice = input(colored("\n[?] Choose a file (number) or 'q' to quit: ", "cyan")).strip()
                
                if choice.lower() == 'q':
                    return None
                
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(cap_files):
                        return cap_files[choice_num - 1]
                    else:
                        self.logger.warning(colored("[!] Invalid number. Try again.", "red"))
                except ValueError:
                    self.logger.warning(colored("[!] Please enter a valid number.", "red"))
        except KeyboardInterrupt:
            return None

    def get_wordlist(self):
        """Prompts the user to enter the wordlist path with a default location"""
        default_dir = "/usr/share/wordlists"
        
        print("\n")
        print_header("SELECT WORDLIST", "yellow","-")
        print(colored(f"Default:", 'yellow') + colored(str(default_dir), 'white'))
        
        try:
            dir_input = input(colored("Enter directory path (or press Enter for default): ", "green")).strip()
            
            wordlist_dir = dir_input if dir_input else default_dir
            
            if not os.path.isdir(wordlist_dir):
                self.logger.warning(colored(f"[!] Directory {wordlist_dir} not found! Try again.", "red"))
                return None
            
            wordlist_files = [
                f for f in os.listdir(wordlist_dir) 
                if os.path.isfile(os.path.join(wordlist_dir, f)) 
                and (f.endswith('.txt') or f.endswith('.lst'))
            ]
            
            if not wordlist_files:
                self.logger.warning(colored("[!] No wordlist files found in this directory!", "red"))
                return None
            
            print("\n")
            print_header("AVAILABLE WORDLISTS", "yellow","-")
            for idx, file in enumerate(wordlist_files, 1):
                print(f"{colored(f'[{idx}]', 'yellow')} {file}")
            
            try:
                default_wordlist="rockyou.txt"
                file_choice = input(colored("\n[?] Choose a wordlist (number) or press Enter for default (rockyou.txt): ", "cyan")).strip()

                if not file_choice:
                    if default_wordlist in wordlist_files:
                        return os.path.join(wordlist_dir, default_wordlist)
                    else:
                        print(colored(f"[!] Default wordlist '{default_wordlist}' not found!", "red"))
                        return None
                else:
                    # User entered a number, try to use that wordlist
                    try:
                        choice_num = int(file_choice)
                        if 1 <= choice_num <= len(wordlist_files):
                            selected_file = wordlist_files[choice_num - 1]
                            full_path = os.path.join(wordlist_dir, selected_file)
                            return full_path
                        else:
                            self.logger.warning(colored("[!] Invalid number. Try again.", "red"))
                            return None
                    except ValueError:
                        self.logger.warning(colored("[!] Please enter a valid number.", "red"))
                        return None
            except KeyboardInterrupt:
                return None
        
        except KeyboardInterrupt:
            return None
        except Exception as e:
            self.logger.error(colored(f"[!] Error in wordlist selection: {e}", "red"))
            return None
        
    def extract_ssid(self, cap_file):
        """Extract SSID from the capture file using aircrack-ng"""
        try:
            cmd = f"aircrack-ng {cap_file} | awk '/WPA \\(/ {{for (i=3; i<NF-2; i++) printf \"%s%s\", (i>3 ? \"_\" : \"\"), $i; print \"\"}}'"
            
            process = subprocess.Popen(
                cmd, 
                shell=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(colored(f"[!] Failed to extract SSID: {stderr}", "red"))
                return None
            
            lines = stdout.strip().split('\n')
            if lines and lines[0]:
                ssid = lines[0].strip()
                self.logger.info(colored(f"[+] Extracted SSID: {ssid}", "green"))
                return ssid
            else:
                self.logger.warning(colored("[!] No SSID found in the capture file", "yellow"))
                return None
            
        except Exception as e:
            self.logger.error(colored(f"[!] Error extracting SSID: {e}", "red"))
            return None
    
    def crack_wifi(self, cap_file, wordlist):
        process = None
        password_found = False
        password = None
        network_ssid = None
        success_message = ""
        
        try:
            if not os.path.exists(cap_file):
                print(colored(f"[ERROR] Capture file not found: {cap_file}", "red"))
                return False
            
            if not os.path.exists(wordlist):
                print(colored(f"[ERROR] Wordlist not found: {wordlist}", "red"))
                return False
            
            network_ssid = self.extract_ssid(cap_file)
            
            print("\n")
            print_header("CRACKING WIFI PASSWORD", "yellow","-")
            print(colored("[INFO] Starting Aircrack-ng", "yellow"))
            print(colored("Capture file: ", 'yellow') + cap_file)
            if network_ssid:
                print(colored("Network SSID: ", 'yellow') + network_ssid)
            print(colored("Wordlist: ", 'yellow') + wordlist)
            print(colored("\n[*] Cracking will start in:", "green"))
            for i in range(3, 0, -1):
                print(colored(f"{i}...", "cyan"))
                time.sleep(1)
            
            cmd = [
                "aircrack-ng",
                "-w", wordlist,   
                cap_file
            ]
            

            print(colored("[+] Executing command: " + " ".join(cmd), "green"))
            print(colored("[*] Press Ctrl+C to interrupt the cracking process", "yellow"))
            
            original_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                preexec_fn=os.setsid
            )
            
            signal.signal(signal.SIGINT, original_sigint)
            
            output_buffer = []
            
            try:
                for line in iter(process.stdout.readline, ''):
                    output_buffer.append(line.strip())
                    print(line.strip())
                    
                    if not network_ssid:
                        ssid_match = re.search(r'BSSID\s+ESSID\s+(\S+)', line)
                        if ssid_match:
                            network_ssid = ssid_match.group(1).strip()
                    
                    key_match = re.search(r"KEY FOUND!\s*\[\s*(.+?)\s*\]", line)
                    if key_match:
                        password = key_match.group(1).strip()
                        password_found = True
                        
                process.wait()
                
            except KeyboardInterrupt:
                return False
                
            if password_found and password:
                success_message = "\n" + "=" * self.term_width + "\n"
                success_message += colored(f"[SUCCESS] PASSWORD FOUND: {password}\n", "green")
                
                if network_ssid:
                    save_password(network_ssid, password, cap_file)
                    
                success_message += "=" * self.term_width + "\n"
                
                os.system("clear" if os.name == "posix" else "cls")
                print_header("CRACKING COMPLETE", "green","=")
            
                last_lines = output_buffer[-10:] if len(output_buffer) > 10 else output_buffer
                print("\n".join(last_lines))
                
                print(success_message)
                return True
            else:
                print(colored("[RESULT] No password found", "yellow"))
                return False
            
        except Exception as e:
            print(colored(f"[CRITICAL ERROR] {str(e)}", "red"))
            return False
        
        finally:
            if process:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    pass

    def find_files_in_directory(self, directory, extensions):
        """Find files with specific extensions in a directory"""
        found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    found_files.append(os.path.join(root, file))
        return found_files

    def run(self, cap_file=None, wordlist=None):
        """Main execution method"""
        try:
            os.system("clear" if os.name == "posix" else "cls")
            print_header("WiFi Cracking Tool", "blue")
            
            hc22000_files, existing_cap_files, processed_files = check_and_convert_cap_files()
            
            if processed_files:
                print(colored(f"\n[+] Processed {len(processed_files)} new .cap files.", "green"))
                time.sleep(1)


            
            while True:
                try:
                    os.system("clear" if os.name == "posix" else "cls")
                    self.term_width = shutil.get_terminal_size().columns 
                    
                    print_header("WiFi Cracking Tool", "blue")

                    found_passwords, file_exists = load_found_passwords()
                    if found_passwords:
                        print(colored(f" [✓] {len(found_passwords)} network password(s) found:", 'green', attrs=['bold']))
                        for ssid, data in found_passwords.items():
                            if isinstance(data, dict):  
                                print(colored(f" - {ssid}: {data['password']}", 'green'))
                            else:  
                                print(colored(f" - {ssid}: {data}", 'green'))
                    print_header("MAIN MENU", "yellow", char="-")
                    
                    menu_options = [
                        f"{colored('[1]', 'yellow', attrs=['bold'])} Crack WiFi password",
                        f"{colored('[2]', 'yellow', attrs=['bold'])} View saved passwords",
                        f"{colored('[3]', 'yellow', attrs=['bold'])} Check and convert CAP files",
                        f"{colored('[Q]', 'yellow', attrs=['bold'])} Quit"
                    ]
                    
                    max_option_length = max(len(option) for option in menu_options)
                    padding = (self.term_width - max_option_length) // 2
                    
                    for option in menu_options:
                        print(" " * padding + colored(option, "cyan"))
                    
                    print(colored("-" * self.term_width, "yellow"))
                    
                    choice = input(colored("\n[?] Choose an option (1-3 or Q): ", "cyan")).strip()
                    
                    if choice == "1":
                        if not cap_file:
                            cap_files = self.list_cap_files()
                            cap_file = self.select_cap_file(cap_files)
                        
                        if not cap_file:
                            time.sleep(1)
                            cap_file = None  
                            continue
                        
                        if not wordlist:
                            wordlist = self.get_wordlist()
                        
                        if not wordlist:
                            time.sleep(1)
                            wordlist = None  
                            continue
                        
                        success = self.crack_wifi(cap_file, wordlist)
                        
                        cap_file = None
                        wordlist = None
                        
                        try:
                            input(colored("\n[*] Press Enter to return to the menu...", "cyan"))
                        except KeyboardInterrupt:
                            pass
                        
                    elif choice == "2":
                        view_saved_passwords()
                        try:
                            input(colored("\n[*] Press Enter to return to the menu...", "cyan"))
                        except KeyboardInterrupt:
                            pass
                        
                    elif choice == "3":
                        hc22000_files, existing_cap_files, processed_files = check_and_convert_cap_files()
                        
                        if processed_files:
                            print(colored(f"\n[+] Processed {len(processed_files)} new .cap files.", "green"))
                        else:
                            print(colored(f"\n[*] No new .cap files to process.", "yellow"))
                            
                        print(colored(f"[INFO] Found {len(existing_cap_files)} .cap files and {len(hc22000_files)} .hc22000 files in the handshakes directory.", "cyan"))
                        
                        try:
                            input(colored("\n[*] Press Enter to return to the menu...", "cyan"))
                        except KeyboardInterrupt:
                            pass

                    elif choice.strip().lower() == "q":
                        print_header("GOODBYE!", "green")
                        print(colored("\n[*] Exiting the WiFi Cracking Tool. Goodbye!", "green"))
                        break
                        
                    else:
                        print(colored("\n[!] Invalid option. Please try again.", "red"))
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    continue
        
        except KeyboardInterrupt:
            print_header("INTERRUPTED", "yellow","=")
            print(colored("\n[*] Program interrupted by user. Exiting...", "yellow"))
            sys.exit(0)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            sys.exit(1)

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="WiFi Password Cracking Tool")
    parser.add_argument("-c", "--cap", help="Specify the .cap file")
    parser.add_argument("-w", "--wordlist", help="Specify the wordlist path")
    return parser.parse_args()

def main():
    """Entry point of the application"""
    args = parse_arguments()
    cracker = WifiCrackingTool()
    
    cracker.run(args.cap, args.wordlist)

if __name__ == "__main__":
    main()