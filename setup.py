import subprocess
import json
import sys
import os
import shutil

# ANSI color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def run_command(command, description):
    """Runs a command and shows progress"""
    print(f"\n{Colors.BLUE}[INFO]{Colors.RESET} {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {description} completed successfully")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Error during {description}:")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return None

def setup_wrangler_config(database_id):
    """Creates the wrangler.jsonc configuration file"""
    print(f"\n{Colors.BLUE}[INFO]{Colors.RESET} Creating wrangler.jsonc configuration...")
    
    if not os.path.exists("wrangler.example.jsonc"):
        print(f"{Colors.RED}[ERROR]{Colors.RESET} wrangler.example.jsonc not found!")
        return False
    
    # Copy example to wrangler.jsonc
    shutil.copy("wrangler.example.jsonc", "wrangler.jsonc")
    
    # Read the file and replace placeholders
    with open("wrangler.jsonc", "r") as f:
        content = f.read()
    
    # Replace placeholders with actual values
    content = content.replace("your-database-name", "activation-keys")
    content = content.replace("your-database-id-here", database_id)
    
    with open("wrangler.jsonc", "w") as f:
        f.write(content)
    
    print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} wrangler.jsonc configuration created")
    return True

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.CYAN}Activation Keys Worker Setup{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    
    # 1. Install NPM Dependencies
    npm_output = run_command("npm install", "Installing NPM dependencies")
    if npm_output is None:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} NPM installation failed. Please make sure Node.js is installed.")
        sys.exit(1)
    
    # 2. Create Cloudflare D1 Database
    

    print(f"\n{Colors.BLUE}[INFO]{Colors.RESET} Creating Cloudflare D1 database...")
    db_output = run_command("npx wrangler d1 create activation-keys", "Creating D1 database")
    if db_output is None:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Database creation failed. You may already have a database with this name.")
        input(f"{Colors.YELLOW} Continue Anyway? (Press Enter to continue or Ctrl+C to exit){Colors.RESET}")
    else:
        # Extract the Database ID from output
        database_id = None
        for line in db_output.split('\n'):
            if 'database_id' in line and '"' in line:
                # Extract the ID between quotes
                database_id = line.split('"')[1]
                break
    
        if not database_id:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Could not extract Database ID from output.")
            print("Please check the output and manually enter the Database ID in wrangler.jsonc.")
            print(f"Output: {db_output}")
        else:
            print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} Database created with ID: {Colors.YELLOW}{database_id}{Colors.RESET}")
            
        # 3. Create wrangler.jsonc configuration
        if not setup_wrangler_config(database_id):
            sys.exit(1)
    
    # 4. Create database schema
    schema_output = run_command("npx wrangler d1 execute activation-keys --file=./keys.sql", "Creating database schema")
    if schema_output is None:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Schema creation failed.")
        sys.exit(1)
    
    # 5. Configuration for Admin Key and Base URL
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}Configuration{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    
    admin_key = input(f"{Colors.YELLOW}Custom Admin Key: {Colors.RESET}")
    base_url = input(f"{Colors.YELLOW}Cloudflare Worker URL (leave empty for local development): {Colors.RESET}")
    buy_url = input(f"{Colors.YELLOW}URL to Buy Activation Keys (can be configured later): {Colors.RESET}")
    
    if not admin_key:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} Admin Key is required.")
        sys.exit(1)
    
    # Default URL for local development if none provided
    if not base_url:
        base_url = "http://localhost:8787"
    
    # Save configuration to keys.json
    config = {
        "admin_keys":[admin_key],
        "base_url": base_url,
        "buy_url": buy_url
    }
    
    with open('keys.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}Setup completed successfully!{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"\n{Colors.BOLD}Next steps:{Colors.RESET}")
    print(f"{Colors.WHITE}• For local development: {Colors.CYAN}npm run dev{Colors.RESET}")
    print(f"{Colors.WHITE}• For production deployment:{Colors.RESET}")
    print(f"  {Colors.WHITE}1. {Colors.CYAN}npx wrangler d1 execute activation-keys --remote --file=./keys.sql{Colors.RESET}")
    print(f"  {Colors.WHITE}2. {Colors.CYAN}npm run deploy{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Note:{Colors.RESET} For production, you should update the base_url in keys.json to your")
    print("deployed Worker URL.")