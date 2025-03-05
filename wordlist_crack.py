#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from termcolor import colored
import logging
import time
import signal

class WifiCrackingTool:
    def __init__(self):
        """Initialize the WiFi Cracking Tool"""
        self.setup_logging()
        self.check_dependencies()

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
        dependencies = ['aircrack-ng']
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
        """Allows the user to select a .cap file"""
        if not cap_files:
            self.logger.warning(colored("[!] No .cap files found in the directory or handshakes!", "red"))
            time.sleep(2)
            return None

        self.logger.info(colored("\n[+] Select a .cap file to analyze:", "yellow"))
        for idx, file in enumerate(cap_files, 1):
            print(f"{idx}. {file}")

        while True:
            try:
                choice = input(colored("\n[?] Choose a file (number) or 'q' to quit: ", "cyan")).strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(cap_files):
                    return cap_files[choice_num - 1]
                else:
                    self.logger.warning(colored("[!] Invalid number. Try again.", "red"))
            except ValueError:
                self.logger.warning(colored("[!] Please enter a valid number.", "red"))
    
    def get_wordlist(self):
        """Prompts the user to enter the wordlist path"""
        while True:
            wordlist = input(colored("\n[?] Enter the wordlist path (or 'q' to quit): ", "cyan")).strip()
            
            if wordlist.lower() == 'q':
                return None
            
            if os.path.exists(wordlist):
                return wordlist
            else:
                self.logger.warning(colored("[!] Wordlist not found! Try again.", "red"))

    def crack_wifi(self, cap_file, wordlist):
        processo = None
        try:
            if not os.path.exists(cap_file):
                print(colored(f"[ERROR] Capture file not found: {cap_file}", "red"))
                return False
            
            if not os.path.exists(wordlist):
                print(colored(f"[ERROR] Wordlist not found: {wordlist}", "red"))
                return False
            
            print(colored(f"[INFO] Starting Aircrack-ng\nCapture file: {cap_file}\nWordlist: {wordlist}", "yellow"))
            
            cmd = [
                "aircrack-ng",
                "-w", wordlist,   
                "-l", "found_password.txt",   
                cap_file
            ]
            
            print(colored("[+] Executing command: " + " ".join(cmd), "green"))
            print(colored("[*] Press Ctrl+C to interrupt the cracking process", "yellow"))
            
            # Disable SIGINT handling in the parent process during subprocess execution
            original_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
            
            processo = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                preexec_fn=os.setsid
            )
            
            # Restore original SIGINT handler
            signal.signal(signal.SIGINT, original_sigint)
            
            try:
                while True:
                    output = processo.stdout.readline()
                    if output == '' and processo.poll() is not None:
                        break
                    if output:
                        print(output.strip())
            except KeyboardInterrupt:
                print(colored("\n[*] Cracking process interrupted by user.", "yellow"))
                time.sleep(2)
                return False
            
            if os.path.exists("found_password.txt"):
                with open("found_password.txt", "r") as f:
                    password = f.read().strip()
                    print(colored(f"[SUCCESS] Password found: {password}", "green"))
                return True
            else:
                print(colored("[RESULT] No password found", "yellow"))
                return False
            
        except Exception as e:
            print(colored(f"[CRITICAL ERROR] {str(e)}", "red"))
            return False
        
        finally:
            if processo:
                try:
                    os.killpg(os.getpgid(processo.pid), signal.SIGKILL)
                except Exception:
                    pass
            
            if os.path.exists("found_password.txt"):
                os.remove("found_password.txt")
    def run(self, cap_file=None, wordlist=None):
        """Main execution method"""
        try:
            os.system("clear" if os.name == "posix" else "cls")
            print(colored("\n=== WiFi Cracking Tool ===", "blue"))
            
            if not cap_file:
                cap_files = self.list_cap_files()
                cap_file = self.select_cap_file(cap_files)
            
            if not cap_file:
                self.logger.warning("No capture file selected. Exiting.")
                return
            
            if not wordlist:
                wordlist = self.get_wordlist()
            
            if not wordlist:
                self.logger.warning("No wordlist selected. Exiting.")
                return
            
            self.crack_wifi(cap_file, wordlist)
        
        except KeyboardInterrupt:
            self.logger.info("\n[*] Operation cancelled by user.")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

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