import os
import sys
import json
import hashlib
import getpass
from abc import ABC, abstractmethod

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")


def setup_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    for path in [USERS_FILE, ITEMS_FILE]:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)


def read_data(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def write_data(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class User(ABC):
    def __init__(self, user_id, name, password_hash):
        self._user_id = user_id
        self._name = name
        self.__password_hash = password_hash

    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name

    def verify_password(self, password):
        return self.__password_hash == hash_text(password)

    @abstractmethod
    def get_role(self):
        pass


class Student(User):
    def __init__(self, user_id, name, password_hash, department):
        super().__init__(user_id, name, password_hash)
        self.department = department

    def get_role(self):
        return "Student"


class Admin(User):
    def __init__(self, user_id, name, password_hash, admin_code):
        super().__init__(user_id, name, password_hash)
        self.admin_code = admin_code

    def get_role(self):
        return "Admin"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_header(title):
    clear()
    print("-" * 50)
    print(f"Campus Lost & Found System - {title}")
    print("-" * 50)


def register():
    show_header("Register")
    print("1. Student")
    print("2. Admin")
    print("0. Back")
    
    choice = input("\nSelect account type: ").strip()
    if choice == "0":
        return
    if choice not in ["1", "2"]:
        input("Invalid choice. Press enter to return...")
        return

    role = "Student" if choice == "1" else "Admin"
    user_id = input("Enter Roll No / ID: ").strip()
    
    if not user_id:
        input("ID cannot be blank. Press enter to return...")
        return

    users = read_data(USERS_FILE)
    for u in users:
        if u["user_id"].lower() == user_id.lower():
            input("User ID already registered. Press enter to return...")
            return

    name = input("Enter Full Name: ").strip()
    password = getpass.getpass("Enter Password: ").strip()
    confirm = getpass.getpass("Confirm Password: ").strip()

    if password != confirm:
        input("Passwords do not match. Press enter to return...")
        return

    detail = ""
    if role == "Student":
        detail = input("Enter Department: ").strip()
    else:
        key = input("Enter Admin Passcode: ").strip()
        if key != "FUI-ADMIN-2026":
            input("Wrong admin key. Press enter to return...")
            return
        detail = "Admin"

    users.append({
        "user_id": user_id,
        "name": name,
        "password_hash": hash_text(password),
        "role": role,
        "detail": detail
    })
    write_data(USERS_FILE, users)

    input(f"\nAccount created as {role}. Press enter to continue...")


def login():
    show_header("Login")
    user_id = input("Enter ID: ").strip()
    password = getpass.getpass("Enter Password: ").strip()

    users = read_data(USERS_FILE)
    account = None
    for u in users:
        if u["user_id"].lower() == user_id.lower():
            account = u
            break

    if not account:
        input("User not found. Press enter to return...")
        return None

    if account["role"] == "Student":
        current_user = Student(
            account["user_id"],
            account["name"],
            account["password_hash"],
            account.get("detail", "")
        )
    else:
        current_user = Admin(
            account["user_id"],
            account["name"],
            account["password_hash"],
            account.get("detail", "")
        )

    if current_user.verify_password(password):
        input(f"\nWelcome, {current_user.name}! Press enter to continue...")
        return current_user
    
    input("Incorrect password. Press enter to return...")
    return None


def student_menu(student):
    while True:
        show_header(f"Student Portal ({student.name})")
        print("1. Report Lost Item")
        print("2. Report Found Item")
        print("3. Search Items")
        print("4. View Matches")
        print("5. Submit Claim")
        print("0. Logout")

        choice = input("\nSelect an option: ").strip()
        if choice == "1":
            input("\n[Report Lost Item selected] Press enter...")
        elif choice == "2":
            input("\n[Report Found Item selected] Press enter...")
        elif choice == "3":
            input("\n[Search Items selected] Press enter...")
        elif choice == "4":
            input("\n[View Matches selected] Press enter...")
        elif choice == "5":
            input("\n[Submit Claim selected] Press enter...")
        elif choice == "0":
            break
        else:
            input("Invalid selection. Press enter...")


def admin_menu(admin):
    while True:
        show_header(f"Admin Portal ({admin.name})")
        print("1. View All Items")
        print("2. Delete Post")
        print("3. Approve Claims")
        print("4. View Registered Users")
        print("0. Logout")

        choice = input("\nSelect an option: ").strip()
        if choice == "1":
            input("\n[View All Items selected] Press enter...")
        elif choice == "2":
            input("\n[Delete Post selected] Press enter...")
        elif choice == "3":
            input("\n[Approve Claims selected] Press enter...")
        elif choice == "4":
            show_header("Registered Users")
            users = read_data(USERS_FILE)
            for u in users:
                print(f"ID: {u['user_id']} | Name: {u['name']} | Role: {u['role']}")
            input("\nPress enter to return...")
        elif choice == "0":
            break
        else:
            input("Invalid selection. Press enter...")


def main():
    setup_files()
    while True:
        show_header("Main Menu")
        print("1. Login")
        print("2. Register")
        print("0. Exit")

        choice = input("\nEnter choice: ").strip()
        if choice == "1":
            user = login()
            if user:
                if user.get_role() == "Student":
                    student_menu(user)
                elif user.get_role() == "Admin":
                    admin_menu(user)
        elif choice == "2":
            register()
        elif choice == "0":
            sys.exit(0)
        else:
            input("Invalid choice. Press enter...")


if __name__ == "__main__":
    main()