# Activation Key Worker (Cloudflare)

A Cloudflare Worker for managing activation keys with machine ID binding and license validation support.

## Overview

This repo is a serverless API running on Cloudflare Workers that manages activation keys for software licensing. The system supports:

- Adding new activation keys
- Activation key validation
- Machine ID binding to prevent multiple usage
- Admin dashboard for managing all keys
- Cloudflare D1 database integration


## Installation and Setup

### Prerequisites

- Node.js (Version 18+)
- Python 3.x
- A Cloudflare account
- Wrangler CLI

### 1. Clone the repository

```bash
git clone <repository-url>
cd Activation-Keys-Worker
```

### 2. Run automated setup

```bash
npm run setup
```

This automated setup script will:
- Install all NPM dependencies
- Create the Cloudflare D1 database
- Set up the Wrangler configuration file
- Create the database schema
- Configure your admin key and base URL

**Note:** Make sure you're logged into Cloudflare first with `npx wrangler login`

### 3. Start development

```bash
npm run dev
```

The worker will then run locally at `http://localhost:8787`.

## Deployment

### 1. Prepare production database

Warning: This will delete the existing table!
```bash
npx wrangler d1 execute activation-keys --remote --file=./keys.sql
```

### 2. Deploy worker

```bash
npm run deploy
```


## Features

### API-Endpoints

#### `POST /api/verify`
Verifies an activation key and optionally binds it to a machine ID.

**Request Body:**
```json
{
  "key": "activation-key-to-check",
  "machine_id": "unique-machine-id"
}
```

**Response (200 OK):**
```json
{
  "activation_key": "activation-key-to-check",
  "machine_id": "unique-machine-id"
}
```

**Possible Responses:**
- `200` - Key valid and successfully verified
- `400` - Missing activation key
- `403` - Key already in use on another machine
- `404` - Activation key not found

#### `POST /api/add`
Adds a new activation key to the database.

**Request Body:**
```json
{
  "activation_key": "new-activation-key",
  "user_email": "user@example.com",
  "expires" : "2025-07-18T10:30:00.000Z",
  "admin" : "your-admin-key"
}
```

**Response (201 Created):**
```
Activation key added: new-activation-key, for user user@example.com at 2025-07-18T10:30:00.000Z
```

**Other Responses:**
- `400` - Missing activation key, email, or admin key
- `403` - Unauthorized (admin key incorrect)
- `409` - Duplicate: activation key already exists

#### `POST /api/table`
Retrieves all activation keys (admin only).

**Request Body:**
```json
{
  "admin": "your-admin-key"
}
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "ActivationKey": "test-key-123",
    "UserEmail": "user@example.com",
    "MachineID": "machine-xyz",
    "ExpiresAt" : "2025-07-18T10:30:00.000Z",
    "DateCreated": "2025-07-18T10:30:00.000Z"
  }
]
```

**Other Responses:**
- `500` - Admin Key is not set in keys.json. You can fix this by ensuring your keys.json has a set admin key, or running `npm run setup`
- `403` - Unauthorized (admin key incorrect)

#### `POST /api/remove`
Removes the activation key related to the provided user. 

**Request Body:**
```json
{
  "user_email" : "your-users-email",
  "admin" : "your-admin-key"
}
```
**Success Response (200)**
`Activation key removed for user ${user_email}`
**Other Responses:**
- `500` - Admin Key is not set in keys.json. You can fix this by ensuring your keys.json has a set admin key, or running `npm run setup`
- `403` - Unauthorized (admin key incorrect)

## Development

### Available Scripts

- `npm run dev` - Starts the local development server
- `npm run deploy` - Deploys the worker to Cloudflare
- `npm run setup` - Runs the initial project setup
- `npm test` - Runs tests with Vitest
- `npm run cf-typegen` - Generates TypeScript types for Cloudflare

### Database Structure

```sql
CREATE TABLE Keys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ActivationKey TEXT UNIQUE NOT NULL,
  UserEmail TEXT NOT NULL,
  MachineID TEXT,
  DateCreated TEXT NOT NULL
);
```

### Project Structure

```
sonicscore-worker/
├── src/
│   └── index.ts          # Main worker code
├── test/                 # Test files (currently empty)
├── keys.json            # Configuration file (after setup)
├── keys.sql             # Database schema
├── package.json         # Node.js dependencies
├── setup.py             # Setup script
├── tsconfig.json        # TypeScript configuration
├── vitest.config.mts    # Test configuration
├── wrangler.jsonc       # Cloudflare Worker configuration
└── README.md           # This file
```

## Security

- Admin operations require a secure admin key (self provided)
- Activation keys are bound to machine IDs to prevent multiple usage (client dependent)
- All API endpoints validate input data

## License

MIT

## Support

For questions or issues, please create an issue in the repository or contact me. z
