if __name__ == "__main__":
    # prompt the admin key, and the base URL
    admin_key = input("Custom Admin Key: ")
    base_url = input("Cloudflare Worker URL: ")

    if not admin_key or not base_url:
        print("Admin key and base URL are required.")
        exit(1)

    # save the configuration to keys.json
    import json
    config = {
        "admin_key": admin_key,
        "base_url": base_url
    }
    with open('keys.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("All set up! Use npx wrangler dev to run the worker locally, or npx wrangler deploy to deploy it to Cloudflare Workers.")
    print("Note that local development has a different base URL (usually http://localhost:8787). You can change this in keys.json.")