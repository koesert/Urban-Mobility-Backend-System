from managers.backup_manager import BackupManager


def handle_backup_menu(auth_service):
    """Handle backup operations menu"""
    backup_manager = BackupManager(auth_service)

    while True:
        choice = display_backup_menu(backup_manager)

        if choice == "1":
            backup_manager.create_backup()
        elif choice == "2":
            handle_restore_menu(backup_manager)
        elif choice == "3":
            list_and_show_backups(backup_manager)
        elif choice == "4":
            handle_restore_codes_menu(backup_manager)
        elif choice == "5":
            break
        else:
            print("Invalid choice! Please try again.")

        if choice in ["1", "2", "3", "4"]:
            input("\nPress Enter to continue...")


def display_backup_menu(backup_manager):
    """Display backup management menu"""
    user = backup_manager.auth.current_user
    if not user:
        print("Error: No user logged in!")
        return "5"

    print(f"\n--- BACKUP MANAGEMENT ({user['role'].replace('_', ' ').title()}) ---")

    menu_options = []
    option_num = 1

    # Create backup - available to super admin and system admin
    if backup_manager.can_create_backup():
        print(f"{option_num}. Create Backup")
        menu_options.append(option_num)
        option_num += 1

    # Restore backup - available to super admin directly, system admin with codes
    if backup_manager.can_restore_backup() or backup_manager.can_use_restore_code():
        print(f"{option_num}. Restore Backup")
        menu_options.append(option_num)
        option_num += 1

    # List backups - available to anyone who can create or restore
    if backup_manager.can_create_backup() or backup_manager.can_use_restore_code():
        print(f"{option_num}. View Backup Information")
        menu_options.append(option_num)
        option_num += 1

    # Manage restore codes - only super admin
    if backup_manager.can_manage_restore_codes():
        print(f"{option_num}. Manage Restore Codes")
        menu_options.append(option_num)
        option_num += 1

    print(f"{option_num}. Back to Main Menu")

    if not menu_options:
        print("Access denied: You don't have backup management permissions!")
        return "5"

    choice = input("\nSelect an option: ")
    return choice


def handle_restore_menu(backup_manager):
    """Handle restore backup submenu"""
    # List available backups
    backups = backup_manager.list_backups()

    if not backups:
        print("No backup files found.")
        return

    print("\n--- AVAILABLE BACKUPS ---")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup}")

    try:
        choice = int(input(f"\nSelect backup to restore (1-{len(backups)}): "))
        if 1 <= choice <= len(backups):
            selected_backup = backups[choice - 1]

            # Show backup information
            backup_manager.show_backup_info(selected_backup)

            # Check user permissions and get restore method
            if backup_manager.can_restore_backup():
                # Super admin - can restore directly
                print("\n🔑 Super Administrator Access - Direct Restore Available")
                use_code = input("Use restore code instead? (y/n): ").lower().strip()

                if use_code == "y":
                    restore_code = input("Enter restore code: ").strip()
                    backup_manager.restore_backup(selected_backup, restore_code)
                else:
                    backup_manager.restore_backup(selected_backup)

            elif backup_manager.can_use_restore_code():
                # System admin - requires restore code
                print("\n🔑 Restore Code Required")
                restore_code = input("Enter restore code: ").strip()
                backup_manager.restore_backup(selected_backup, restore_code)
            else:
                print("Access denied: You don't have permission to restore backups!")
        else:
            print("Invalid selection!")

    except ValueError:
        print("Please enter a valid number!")
    except KeyboardInterrupt:
        print("\nRestore cancelled.")


def list_and_show_backups(backup_manager):
    """List backups and show detailed information"""
    backups = backup_manager.list_backups()

    if not backups:
        print("No backup files found.")
        return

    print("\n--- AVAILABLE BACKUPS ---")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup}")

    try:
        choice = int(
            input(f"\nSelect backup for details (1-{len(backups)}, 0 for all): ")
        )

        if choice == 0:
            # Show brief info for all backups
            for backup in backups:
                backup_manager.show_backup_info(backup)
                print("-" * 50)
        elif 1 <= choice <= len(backups):
            # Show detailed info for selected backup
            selected_backup = backups[choice - 1]
            backup_manager.show_backup_info(selected_backup)
        else:
            print("Invalid selection!")

    except ValueError:
        print("Please enter a valid number!")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def handle_restore_codes_menu(backup_manager):
    """Handle restore codes management submenu"""
    if not backup_manager.can_manage_restore_codes():
        print("Access denied: Only Super Administrator can manage restore codes!")
        return

    while True:
        print("\n--- RESTORE CODES MANAGEMENT ---")
        print("1. Generate Restore Code")
        print("2. List Active Codes")
        print("3. Revoke Restore Code")
        print("4. Back to Backup Menu")

        choice = input("\nSelect an option: ")

        if choice == "1":
            generate_restore_code_menu(backup_manager)
        elif choice == "2":
            backup_manager.list_restore_codes()
        elif choice == "3":
            revoke_restore_code_menu(backup_manager)
        elif choice == "4":
            break
        else:
            print("Invalid choice! Please try again.")

        if choice in ["1", "2", "3"]:
            input("\nPress Enter to continue...")


def generate_restore_code_menu(backup_manager):
    """Handle restore code generation"""
    # List available backups
    backups = backup_manager.list_backups()

    if not backups:
        print("No backup files found. Create a backup first.")
        return

    print("\n--- SELECT BACKUP FOR RESTORE CODE ---")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup}")

    try:
        choice = int(input(f"\nSelect backup (1-{len(backups)}): "))
        if 1 <= choice <= len(backups):
            selected_backup = backups[choice - 1]
            backup_manager.generate_restore_code(selected_backup)
        else:
            print("Invalid selection!")

    except ValueError:
        print("Please enter a valid number!")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")


def revoke_restore_code_menu(backup_manager):
    """Handle restore code revocation"""
    # Show current codes first
    print("\n--- CURRENT RESTORE CODES ---")
    backup_manager.list_restore_codes()

    if not backup_manager.restore_codes:
        return

    code_to_revoke = input("\nEnter code to revoke (or Enter to cancel): ").strip()

    if code_to_revoke:
        backup_manager.revoke_restore_code(code_to_revoke)
    else:
        print("Operation cancelled.")


def create_backup_menu(auth_service):
    """Simple create backup function for main menu"""
    backup_manager = BackupManager(auth_service)

    if not backup_manager.can_create_backup():
        print("Access denied: You don't have permission to create backups!")
        return

    print("\n--- CREATE BACKUP ---")
    confirm = input("Create a backup of the current database? (y/n): ").lower().strip()

    if confirm == "y":
        backup_manager.create_backup()
    else:
        print("Backup creation cancelled.")


def restore_backup_menu(auth_service):
    """Simple restore backup function for main menu"""
    backup_manager = BackupManager(auth_service)

    if not (
        backup_manager.can_restore_backup() or backup_manager.can_use_restore_code()
    ):
        print("Access denied: You don't have permission to restore backups!")
        return

    # Redirect to full backup menu for restore operations
    handle_restore_menu(backup_manager)
