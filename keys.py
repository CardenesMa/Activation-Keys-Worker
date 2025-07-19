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
        print(json.loads(response.text))

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")

def addKey(key, email):
    """Add a new activation key to the database."""

    url = f"{base_url}/api/add"
    headers = {"Content-Type": "application/json"}
    body = {
        "activation_key": key,
        "user_email": email,
        "admin": admin_key
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        print(f"Response ({response.status_code}):")
        print(response.text)
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
        print(f"Response ({response.status_code}):")
        print(response.text)
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
  %(prog)s -t                                          Get all keys (admin)
  %(prog)s -a "KEY123" "user@email.com" "admin-key"    Add new key
  %(prog)s -v "KEY123" "MACHINE456"                    Verify key

Configuration: Make sure to set the base_url and admin_key are set to your values in keys.py.
        """
    )
    
    parser.add_argument("-t", "--table", action="store_true", 
                       help="Get the activation keys table (requires admin)")
    parser.add_argument("-a", "--add", nargs=2, metavar=("KEY", "EMAIL"), 
                       help="Add a new activation key")
    parser.add_argument("-v", "--verify", nargs=2, metavar=("KEY", "MACHINE_ID"), 
                       help="Verify an activation key")

    args = parser.parse_args()

    # Show configuration status
    print("SonicScore Worker CLI")
    print(f"Worker URL: {base_url or 'Not configured'}")
    print(f"Admin Key: {'Set' if admin_key else 'Not set'}")
    print()

    if args.table:
        getTable()
    elif args.add:
        addKey(args.add[0], args.add[1])
    elif args.verify:
        verifyKey(args.verify[0], args.verify[1])
    else:
        parser.print_help()
