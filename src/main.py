from auth import AuthenticationService
from utils import RoleManager
from managers.travelers_manager import TravelersManager
from managers.user_manager import UserManager
from scooter import manage_scooters_menu


class UrbanMobilitySystem:
    def __init__(self):
        self.auth = AuthenticationService()
        self.role_manager = RoleManager(self.auth)
        self.travelers_manager = TravelersManager(self.auth)
        self.user_manager = UserManager(self.auth)
        self.running = True

    def display_welcome(self):
        """Display welcome message"""
        print("=" * 50)
        print("    Urban Mobility Backend System")
        print("=" * 50)

    def display_login_menu(self):
        """Display login interface"""
        try:
            print("\n--- LOGIN ---")
            username = input("Username: ")
            password = input("Password: ")

            if self.auth.login(username, password):
                user = self.auth.get_current_user()
                # Add safety check even though login succeeded
                if user:
                    print(
                        f"\nWelcome, {user['first_name']} {user['last_name']}!")
                    print(f"Role: {user['role'].replace('_', ' ').title()}")
                    return True
                else:
                    print("Login error occurred!")
                    return False
            else:
                print("Invalid username or password!")
                return False
        except KeyboardInterrupt:
            print("\n\nExiting...")
            self.running = False
            return False

    def display_main_menu(self):
        """Display main menu based on user role"""
        user = self.auth.get_current_user()

        # Add safety check for None user
        if not user:
            print("Error: No user logged in!")
            self.auth.logout()  # Reset session
            return []

        permissions = self.role_manager.get_available_permissions()

        print(
            f"\n--- MAIN MENU ({user['role'].replace('_', ' ').title()}) ---")

        menu_options = []
        option_num = 1

        # Build menu based on permissions
        if "manage_system_administrators" in permissions:
            menu_options.append((option_num, "Manage System Administrators"))
            option_num += 1

        if "manage_service_engineers" in permissions:
            menu_options.append((option_num, "Manage Service Engineers"))
            option_num += 1

        if "manage_travelers" in permissions:
            menu_options.append((option_num, "Manage Travelers"))
            option_num += 1

        if "manage_scooters" in permissions:
            menu_options.append((option_num, "Manage Scooters"))
            option_num += 1

        if "view_logs" in permissions:
            menu_options.append((option_num, "View System Logs"))
            option_num += 1

        if "create_backup" in permissions:
            menu_options.append((option_num, "Create Backup"))
            option_num += 1

        if "restore_backup" in permissions or "use_restore_code" in permissions:
            menu_options.append((option_num, "Restore Backup"))
            option_num += 1

        # Always available options
        menu_options.append((option_num, "Update Password"))
        option_num += 1
        menu_options.append((option_num, "Logout"))
        option_num += 1
        menu_options.append((option_num, "Exit"))

        # Display menu
        for num, option in menu_options:
            print(f"{num}. {option}")

        return menu_options

    def handle_menu_choice(self, choice, menu_options):
        """Handle user menu selection"""
        try:
            choice_num = int(choice)

            # Find the selected option
            selected_option = None
            for num, option in menu_options:
                if num == choice_num:
                    selected_option = option
                    break

            if not selected_option:
                print("Invalid choice!")
                return

            # Handle the selection
            if selected_option == "Logout":
                self.auth.logout()
                print("Logged out successfully!")
            elif selected_option == "Exit":
                self.running = False
                print("Goodbye!")
            elif selected_option == "Manage Travelers":
                self.travelers_manager.handle_travelers_menu()
            elif selected_option == "Manage Scooters":
                manage_scooters_menu(self.role_manager)
            elif selected_option == "Manage System Administrators":
                self.user_manager.handle_user_management_menu("system_admin")
            elif selected_option == "Manage Service Engineers":
                self.user_manager.handle_user_management_menu(
                    "service_engineer")
            elif selected_option == "Update Password":
                self.user_manager.update_own_password()
                input("Press Enter to continue...")
            elif selected_option == "View System Logs":
                try:
                    logs = self.auth.get_logs(self.role_manager)
                    if not logs:
                        print("\nNo log entries found.")
                    else:
                        print("\nSystem Logs:")
                        # Format logs as a table with headers
                        # Prepare headers and rows
                        headers = ["No.", "Date", "Time", "Username",
                                   "Activity", "Details", "Suspicious"]
                        rows = [
                            (log["no"], log["date"], log["time"], log["username"],
                             log["activity"], log["details"], log["suspicious"])
                            for log in logs
                        ]

                        # Define column widths (adjust as needed)
                        col_widths = [max(len(str(row[i])) for row in [
                                          headers] + rows) for i in range(len(headers))]

                        # Print header
                        header_row = " | ".join(
                            f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
                        print(header_row)
                        print("-" * len(header_row))

                        # Print rows
                        for row in rows:
                            print(" | ".join(
                                f"{str(row[i]):<{col_widths[i]}}" for i in range(len(row))))
                    input("\nPress Enter to continue...")
                except PermissionError as e:
                    print(f"\nError: {str(e)}")
                    input("Press Enter to continue...")
            else:
                print(f"\nFeature '{selected_option}' is under development")
                input("Press Enter to continue...")

        except ValueError:
            print("Please enter a valid number!")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            self.running = False

    def run(self):
        """Main application loop"""
        try:
            self.display_welcome()

            while self.running:
                if not self.auth.is_logged_in():
                    # Show login screen
                    if not self.display_login_menu():
                        if (
                            self.running
                        ):  # Only ask to retry if not exiting due to Ctrl+C
                            retry = input("Try again? (y/n): ").lower()
                            if retry != "y":
                                break
                else:
                    # Show main menu
                    menu_options = self.display_main_menu()

                    # Check if menu_options is empty (error case)
                    if not menu_options:
                        continue

                    choice = input("\nSelect an option: ")
                    self.handle_menu_choice(choice, menu_options)
        except KeyboardInterrupt:
            print("\n\nExiting...")


if __name__ == "__main__":
    app = UrbanMobilitySystem()
    app.run()
