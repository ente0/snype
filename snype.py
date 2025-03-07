#!/usr/bin/env python3
import sys
import time
import subprocess
from termcolor import colored
from header_title import (
    show_menu1,
    show_menu2
)

try:
    from snype import (
        clear_screen,
        get_saved_interface_info,
        get_saved_network_info,
        define_ifaces,
        flush_services,
        scan_networks_and_select_bssid,
        handle_option,
        clear_config_files,
        convert_eapol,
        delete_cap_files,
        delete_essidlist_files,
        cleanup_essidlist_files,
        check_and_convert_cap_files,
        select_primary_interface,
        select_secondary_interface,
        auto_convert_latest_cap_file,
        view_saved_passwords  
    )
except ImportError:

    from functions import (
        clear_screen,
        get_saved_interface_info,
        get_saved_network_info,
        define_ifaces,
        flush_services,
        scan_networks_and_select_bssid,
        handle_option,
        clear_config_files,
        convert_eapol,
        delete_cap_files,
        delete_essidlist_files,
        cleanup_essidlist_files,
        check_and_convert_cap_files,
        select_primary_interface,
        select_secondary_interface,
        auto_convert_latest_cap_file,
        view_saved_passwords
    )

def main():
    clear_screen() 
    cleanup_essidlist_files()
    check_and_convert_cap_files()
    iface1, iface2 = get_saved_interface_info()
    network_info = get_saved_network_info()
    bssid = network_info[0] if network_info and network_info[0] else None
    channel = network_info[1] if network_info and network_info[1] else None

    while True:
        if not iface1:
            clear_screen()
            user_option = show_menu1()
            
            if user_option.lower() == "q":
                print(colored("Exiting snype...", 'yellow'))
                sys.exit(0)
            
            elif user_option == "1":
                clear_screen()
                iface1 = select_primary_interface()
            
            elif user_option == "2":
                clear_screen()
                if iface1:
                    iface2 = select_secondary_interface(iface1)
                else:
                    print(colored("[!] Select primary interface first.", 'red'))
                    time.sleep(1)
            
            else:
                print(colored("Invalid option. Please try again.", 'red'))
                time.sleep(1)
                clear_screen()
        else:
            clear_screen() 
            check_and_convert_cap_files()
            user_option = show_menu2()
            if user_option.lower() == "q":
                print(colored("Exiting snype...", 'yellow'))
                sys.exit(0)
            elif user_option == "4":
                try:
                    subprocess.run(["python3", "wordlist_crack.py"], 
                        check=True, 
                        capture_output=False)
                except KeyboardInterrupt:
                    print(colored("\n[!] Operation cancelled by user.", 'yellow'))
                    input("Press Enter to return to the menu...")
                clear_screen()
            elif user_option == "5":
                clear_screen()
                view_saved_passwords()
                input("\nPress Enter to return to the menu...")
                clear_screen()
            elif user_option == "6":
                clear_screen()  
                flush_services()
            elif user_option == "7":
                bssid = scan_networks_and_select_bssid(iface1)
                clear_screen() 
            elif user_option == "8":
                clear_screen()  
                iface1, iface2 = define_ifaces()
            elif user_option == "9":
                clear_config_files()
                iface1, iface2 = None, None
                bssid = None
                clear_screen() 
            elif user_option == "10":
                convert_eapol()
                clear_screen() 
            elif user_option == "11":
                delete_cap_files()
                clear_screen() 
            elif user_option == "12":
                delete_essidlist_files()
                clear_screen()  
            elif user_option in ["1", "2"]:
                handle_option(user_option, iface1, iface2, bssid)
                clear_screen() 
            elif user_option == "3":
                bssid = get_saved_network_info
                if not bssid:
                    print(colored("[!] No target BSSID selected. Select a target first.", 'red'))
                    time.sleep(2)
                    clear_screen()
                else:
                    subprocess.run(["python3", "deauth_attack.py"])
                    clear_screen()


            if user_option in ["5", "6"]:
                iface1, iface2 = get_saved_interface_info()
                network_info = get_saved_network_info()
                bssid = network_info[0] if network_info and network_info[0] else None
                channel = network_info[1] if network_info and network_info[1] else None

if __name__ == "__main__":
    auto_convert_latest_cap_file()
    main()