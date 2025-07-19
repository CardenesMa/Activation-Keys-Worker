export interface Env {
	DB: D1Database;
}

// Developed using : https://developers.cloudflare.com/d1/get-started/#populate-your-d1-database


// Mirrors what the keys table looks like
type DatabaseType = 
{
	ActivationKey: string;
	UserEmail: string;
	DateCreated: string;
	MachineID?: string; // Optional, can be null
}

import KEYS from "../keys.json"
const ADMIN_KEY = KEYS.admin_key; // Use the admin key from keys.json

export default {
	async fetch(request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const pathname = url.pathname;

		if (request.method === "POST" && pathname === "/api/verify") {
			return verify(request, env);
		}

		// Create a new activation key
		if (request.method === "POST" && pathname === "/api/add") {
			return add(request, env);
		}

		if(request.method === "POST" && pathname === "/api/table") {
			return table(request, env);
		}

		if (request.method === "POST" && pathname === "/api/remove") {
			return remove(request, env);
		}

		return new Response("Invalid endpoint", { status: 404 });
	},
} satisfies ExportedHandler<Env>;

async function table(request: Request, env: Env): Promise<Response> {
	// make sure the ADMIN is querying the table
	const {admin} = await request.json() as {admin?: string};

	const adminKey = ADMIN_KEY;
	if (!adminKey) {
		return new Response("ADMIN_KEY is not set in the environment variables.", { status: 500 });
	}
	if (!admin || admin !== adminKey) {
		return new Response("Unauthorized", { status: 403 });
	}

	const result = await env.DB.prepare(
		`SELECT * FROM Keys`
	).all();
	if (result.results.length === 0) {
		return new Response("No activation keys found", { status: 404 });
	}
	return new Response(JSON.stringify(result.results), {
		headers: { "Content-Type": "application/json" },
		status: 200
	});
}

/**
 * Adds a new activation key to the database.
 * @param request The incoming request containing activation key details.
 * @param env The environment variables, including the database connection.
 * @returns A Response indicating the result of the operation.
 * 
 * @api {POST} /api/add Add Activation Key
 * @apiName AddActivationKey
 * 
 * Example request body:
 * {
 *   "activation_key": "new-activation-key",
 *   "user_email": "user@example.com",
 * }
 * 
 * Response is textual, 400 or 201.
 */
async function add(request: Request, env: Env): Promise<Response> {
	const { activation_key, user_email, admin } = await request.json() as {activation_key?: string, user_email?: string, admin?: string};

	if (!activation_key || !user_email || !admin) {
		return new Response("Missing activation_key, user_email, or admin", { status: 400 });
	}

	if (admin !== ADMIN_KEY) {
		return new Response("Unauthorized", { status: 403 });
	}

	const dateCreated = new Date().toISOString();

	await env.DB.prepare(
		`INSERT INTO Keys (ActivationKey, UserEmail, MachineID, DateCreated)
         VALUES (?, ?, ?, ?)`
	).bind(activation_key, user_email, null, dateCreated).run();

	return new Response(`Activation key added: ${activation_key}, for user ${user_email} at ${dateCreated}`, { status: 201 });
};

/**
 * Checks if an activation key by exists in the database. The machine ID is to 
 * verify that the key is not being used on multiple machines. It is up to the
 * client to ensure that the returning machine ID is valid with the current machine.
 *
 * @param request The incoming request containing activation details.
 * @param env The environment variables, including the database connection.
 * @returns A Response indicating the result of the operation.
 * 
 * Example request body:
 * {
 *   "key": "activation-key-to-check",
 *   "machine_id": "unique-machine-id"
 * }
 * Example response: if the verification is successful
 * {
 *   "key": "activation-key-to-check",
 *   "machine_id": "unique-machine-id"
 * } 
 */
async function verify(request: Request, env: Env): Promise<Response> {
	const { key , machine_id } = await request.json() as {key?: string, machine_id?: string};

	if (!key) {
		return new Response("Missing activation key", { status: 400 });
	}

	const result : DatabaseType | null = await env.DB.prepare(
		`SELECT * FROM Keys WHERE ActivationKey = ?`
	).bind(key).first();

	if (!result) {
		return new Response("Activation key not found", { status: 404 });
	}

	// if there is an existing machine ID, make sure it's consistent with the one provided
	if (result.MachineID && result.MachineID !== machine_id) {
		return new Response("Activation key is already in use on another machine", { status: 403 });
	}
	// If the machine ID is not set, update it
	if (!result.MachineID) {
		await env.DB.prepare(
			`UPDATE Keys SET MachineID = ? WHERE ActivationKey = ?`
		).bind(machine_id, key).run();
	}

	// all good! 
	return new Response(JSON.stringify({
		activation_key: key,
		machine_id: machine_id
	}), {
		headers: { "Content-Type": "application/json" },
		status: 200
	});

}

/**
 * Removes an activation key from the database.
 * @param request The incoming request containing user details.
 * @param env The environment variables, including the database connection.
 * @returns A Response indicating the result of the operation.
 */
async function remove(request: Request, env: Env): Promise<Response> {
	const { user_email, admin } = await request.json() as {user_email?: string, admin?: string};

	

	if (!user_email || !admin) {
		return new Response("Missing user_email or admin", { status: 400 });
	}

	if(!ADMIN_KEY) {
		return new Response("ADMIN_KEY is not set in the environment variables.", { status: 500 });
	}

	if (admin !== ADMIN_KEY) {
		return new Response("Unauthorized", { status: 403 });
	}

	await env.DB.prepare(
		`DELETE FROM Keys WHERE UserEmail = ?`
	).bind(user_email).run();

	return new Response(`Activation key removed for user ${user_email}`, { status: 200 });
}
