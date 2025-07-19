#!/usr/bin/env python3
"""
SonicScore Worker CLI
A simple CLI interface for making API requests to the SonicScore Worker.

Setup:
1. Copy .env.example to .env: cp .env.example .env
2. Update .env with your Worker URL and Admin Key
3. Run with: python keys.py -h for help

Usage:
    python keys.py -t                    # Get activation key table (requires admin key)
    python keys.py -a KEY EMAIL         # Add activation key
    python keys.py -v KEY MACHINE_ID    # Verify activation key
"""

import requests 
import json
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

with open('keys.json', 'r') as f:
    config = json.load(f)

admin_key = config['admin_key']
base_url = config['base_url']

def getTable():
    """Get all activation keys from the database (admin only)."""
    url = f"{base_url}/api/table"
    headers = {"Content-Type": "application/json"}
    body = {"admin": admin_key}
    
    try:
        # see what the response is
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET}")
        elif response.status_code == 204:
            print(f"{Colors.YELLOW}[INFO]{Colors.RESET} No activation keys found")
        else:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Status code: {response.status_code}")

        print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")

def addKey(email, key, expiry_date = None):
    """Add a new activation key to the database."""

    url = f"{base_url}/api/add"
    headers = {"Content-Type": "application/json"}
    body = {
        "activation_key": key,
        "user_email": email,
        "expires": expiry_date,
        "admin": admin_key
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 201:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} 201 Created")
        elif response.status_code == 409:
            print(f"{Colors.YELLOW}[CONFLICT]{Colors.RESET} 409 Conflict - Key already exists")
        else:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Status code: {response.status_code}")

        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")

def verifyKey(key, machineID):
    """Verify an activation key with machine ID."""

    url = f"{base_url}/api/verify"
    headers = {"Content-Type": "application/json"}
    body = {
        "key": key,
        "machine_id": machineID
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET}")
        else:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")

def deleteKey(email, specify_key=None):
    """Delete an activation key from the database (admin only)."""
    
    url = f"{base_url}/api/delete"
    headers = {"Content-Type": "application/json"}
    body = {
        "user_email": email,
        "specify_key": specify_key,  # Optional key to specify which key to delete
        "admin": admin_key
    }
    
    try:
        response = requests.delete(url, headers=headers, json=body)
        if response.status_code == 200:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET}")
        else:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")

# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Activation Key Worker CLI- Manage activation keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -v "KEY123" "MACHINE456"                    Verify key
  %(prog)s -a "user@email.com" "KEY123"                Add new key (admin only)
  %(prog)s -d "user@email.com" [optional "KEY123", "Expiry Date (ISO 8601)"]     Delete key (admin only)
  %(prog)s -t                                          Get all keys (admin only)

Configuration: Make sure to set the base_url and admin_key are set to your values in keys.py.
        """
    )
    
    parser.add_argument("-t", "--table", action="store_true", 
                       help="Get the activation keys table (requires admin)")
    parser.add_argument("-a", "--add", nargs='+', 
                       help="Add a new activation key. Usage: -a EMAIL KEY [EXPIRY_DATE]")
    parser.add_argument("-v", "--verify", nargs=2, metavar=("KEY", "MACHINE_ID"), 
                       help="Verify an activation key")
    parser.add_argument("-d", "--delete", nargs='+', metavar=("EMAIL", "SPECIFY_KEY"), 
                       help="Delete an activation key (admin only). Usage: -d EMAIL [SPECIFY_KEY]")

    args = parser.parse_args()

    # Show configuration status
    print("SonicScore Worker CLI")
    print(f"Worker URL: {base_url or 'Not configured'}")
    print(f"Admin Key: {'Set' if admin_key else 'Not set'}")
    print()

    if args.table:
        getTable()
    elif args.add:
        email = args.add[0]
        key = args.add[1] if len(args.add) > 1 else None
        expiry_date = args.add[2] if len(args.add) > 2 else None
        if key is None:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} EMAIL and KEY are required for adding a key.")
        else:
            addKey(email, key, expiry_date)
    elif args.verify:
        verifyKey(args.verify[0], args.verify[1])
    elif args.delete:
        email = args.delete[0]
        specify_key = args.delete[1] if len(args.delete) > 1 else None
        deleteKey(email, specify_key)
    else:
        parser.print_help()
