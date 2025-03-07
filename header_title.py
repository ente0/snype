import shutil
from termcolor import colored
from functions import check_and_convert_cap_files, load_found_passwords, show_status_info, print_header
def print_snype_title():
    terminal_width = shutil.get_terminal_size().columns
    
    ascii_art = [
  "  _____ ____   __ __  ____   ___ ",
 r" / ___/|    \ |  |  ||    \ /  _]",
 r"(   \_ |  _  ||  |  ||  o  )  [_ ",
 r" \__  ||  |  ||  ~  ||   _/    _]",
 r" /  \ ||  |  ||___, ||  | |   [_ ",
 r" \    ||  |  ||     ||  | |     |",
 r"  \___||__|__||____/ |__| |_____|",
  "",
  "For more information, visit: https://github.com/ente0/snype",

    ]
    
    print("\n")
    for line in ascii_art:
        padding = (terminal_width - len(line)) // 2
        colored_line = colored(line, 'blue')
        print(" " * padding + colored_line)
    print("\n")

def show_menu1():
    terminal_width = shutil.get_terminal_size().columns
    separator = "=" * terminal_width

    print_snype_title()
    
    print(colored(separator, 'cyan'))
    print(colored(f"   Welcome to snype!", 'cyan', attrs=['bold']))
    
    hc22000_files, cap_files, processed_cap_files = check_and_convert_cap_files()

    if hc22000_files:
        print(colored(f"\n [✓] {len(hc22000_files)} .hc22000 file(s) generated:", 'green', attrs=['bold']))
        for file in hc22000_files:
            print(colored(f" - {file}", 'green'))

    if cap_files:
        print(colored(f" [✓] {len(cap_files)} .cap file(s) found:", 'green', attrs=['bold']))
        for file in cap_files:
            print(colored(f" - {file}", 'green'))
    
    found_passwords, file_exists = load_found_passwords()
    if found_passwords:
        print(colored(f" [✓] {len(found_passwords)} network password(s) found:", 'green', attrs=['bold']))
        for ssid, data in found_passwords.items():
            if isinstance(data, dict):  
                print(colored(f" - {ssid}: {data['password']}", 'green'))
            else:  
                print(colored(f" - {ssid}: {data}", 'green'))

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

    print_snype_title()

    print(colored(separator, 'cyan'))
    print(colored(f" Welcome to snype!", 'cyan', attrs=['bold']))


    hc22000_files, cap_files, processed_cap_files = check_and_convert_cap_files()

    if hc22000_files:
        print(colored(f"\n [✓] {len(hc22000_files)} .hc22000 file(s) generated:", 'green', attrs=['bold']))
        for file in hc22000_files:
            print(colored(f" - {file}", 'green'))

    if cap_files:
        print(colored(f" [✓] {len(cap_files)} .cap file(s) found:", 'green', attrs=['bold']))
        for file in cap_files:
            print(colored(f" - {file}", 'green'))
    
    found_passwords = load_found_passwords()
    if found_passwords:
        print(colored(f" [✓] {len(found_passwords)} network password(s) found:", 'green', attrs=['bold']))
        for ssid, data in found_passwords.items():
            if isinstance(data, dict):  
                print(colored(f" - {ssid}: {data['password']}", 'green'))
            else:  
                print(colored(f" - {ssid}: {data}", 'green'))


    status_info = show_status_info()
    if status_info:
        print_header(status_info,"cyan","=")

    options = [
        f"{colored('[1]', 'cyan', attrs=['bold'])} Network Scanning",
        f"{colored('[2]', 'cyan', attrs=['bold'])} Monitor Target Traffic",
        f"{colored('[3]', 'cyan', attrs=['bold'])} Deauthentication Attack",
        f"{colored('[4]', 'cyan', attrs=['bold'])} Wordlist Cracking",
        f"{colored('[5]', 'cyan', attrs=['bold'])} View found keys",

    ]

    utility_options = [
        f"{colored('[6]', 'magenta', attrs=['bold'])} Flush Services",
        f"{colored('[7]', 'magenta', attrs=['bold'])} Change Target BSSID",
        f"{colored('[8]', 'magenta', attrs=['bold'])} Modify Interfaces",
        f"{colored('[9]', 'magenta', attrs=['bold'])} Clear Configuration",
        f"{colored('[10]', 'magenta', attrs=['bold'])} Convert EAPOL to hc22000",
        f"{colored('[11]', 'magenta', attrs=['bold'])} Delete Capture Files",
        f"{colored('[12]', 'magenta', attrs=['bold'])} Clear ESSID Lists",
    ]

    print(colored("\n ATTACK MODULES:", 'blue', attrs=['bold']))
    print("\n " + "\n ".join(options))
    print("\n" + colored(dash_separator, 'cyan'))
    print(colored("\n UTILITY FUNCTIONS:", 'magenta', attrs=['bold']))
    print("\n " + "\n ".join(utility_options))
    print(colored("\n" + separator, 'magenta'))

    user_option2 = input(colored("\nEnter option (1-12, Q to quit): ", 'cyan', attrs=['bold'])).strip().lower()
    return user_option2