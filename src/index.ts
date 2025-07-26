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
	ExpiresAt: string; // ISO 8601 format
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

		if (request.method === "DELETE" && pathname === "/api/delete") {
			return remove(request, env);
		}

		if (request.method === "GET" && pathname === "/where-buy") {
			return buyLink(request, env);
		}

		return new Response("Invalid endpoint", { status: 404 });
	},
} satisfies ExportedHandler<Env>;

/**
 * Should an administrator want to view the active table remotely, providing the 
 * administration key allows the relational database to be dumped in response. 
 * @param request Infoming request to get the table
 * @param env Environment, including database D1 connection
 * @returns Promise containing the contents of the D1 database
 * 
 * Example response : 
 * ```json
 * {
 * 	[
 * 		"db_0" : "value",
 * 		"db_1" : "value",
 * 		"db_n"	: "value",
 * 	],
 * 	[
 * 		"..." : "..."
 * 	]
 * }
 * ```
 */
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
		return new Response(null, { status: 204 });
	}
	return new Response(JSON.stringify(result.results), {
		headers: { "Content-Type": "application/json" },
		status: 200
	});
}

/**
 * Should your activation keys have a location to purchase them, this endpoint
 * will return the link to that location. This variable should be set in your keys.json file,
 * and any user is allowed to access this endpoint.
 * @param request The incoming request to get the buy link.
 * @param env The environment variables, including the database connection.
 * @returns A Response containing the buy link.
 * 
 * Example respnose : 
 * ```json 
 * {
 * "link" : "https://www.example.com/buy"
 * }
 * ```
 */
async function buyLink(request: Request, env: Env): Promise<Response> {
	const buyURL = KEYS.buy_url;
	if (!buyURL) {
		return new Response("Buy link can't be found", { status: 500 });
	}
	return new Response(JSON.stringify({
		link: buyURL,
	}), {
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
 * ```json
 * {
 *   "activation_key": "new-activation-key",
 *   "user_email": "user@example.com",
 * }
 * ```
 * Response is textual, 400 or 201.
 */
async function add(request: Request, env: Env): Promise<Response> {
	const { activation_key, user_email, expires, admin } = await request.json() as {activation_key?: string, user_email?: string, expires?: string, admin?: string};

	if (!activation_key || !user_email || !admin) {
		return new Response("Missing activation_key, user_email, or admin", { status: 400 });
	}

	if (admin !== ADMIN_KEY) {
		return new Response("Unauthorized", { status: 403 });
	}

	const dateCreated = new Date().toISOString();
	// see if the activation key already exists
	const existingKey: DatabaseType | null = await env.DB.prepare(
		`SELECT * FROM Keys WHERE ActivationKey = ?`
	).bind(activation_key).first();

	if (existingKey) {
		return new Response("Activation key already exists. No change to database", { status: 409 });
	}
	// set expiry date if not provided
	let formattedExpires : String; 

	if (!expires) {
		const expiryDate = new Date();
		expiryDate.setMonth(expiryDate.getMonth() + 1); // Default to 1 month from now
		// format the date to ISO 8601
		formattedExpires = expiryDate.toISOString();
	} else {
		// validate the provided expiry date
		const expiryDate = new Date(expires);
		if (isNaN(expiryDate.getTime())) {
			return new Response("Invalid expiry date format. Use ISO 8601 format.", { status: 400 });
		}
		formattedExpires = expiryDate.toISOString();
	}

	console.log("expires", formattedExpires);

	await env.DB.prepare(
		`INSERT INTO Keys (ActivationKey, UserEmail, MachineID, DateCreated, ExpiresAt)
         VALUES (?, ?, ?, ?, ?)`
	).bind(activation_key, user_email, null, dateCreated, formattedExpires).run();

	return new Response(`Activation key added: ${activation_key}, for user ${user_email} at ${dateCreated}, Expires at ${formattedExpires}`, { status: 201 });
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
 * ```json
 * {
 *   "key": "activation-key-to-check",
 *   "machine_id": "unique-machine-id"
 * }
 * ```
 * Example response: if the verification is successful
 * ```json
 * {
 *   "key": "activation-key-to-check",
 *   "machine_id": "unique-machine-id"
 * } 
 * ```
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

	return new Response(JSON.stringify({
		key: result.ActivationKey,
		machine_id: machine_id || result.MachineID,
		user_email: result.UserEmail,
		date_created: result.DateCreated,
		expires_at: result.ExpiresAt
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
 * 
 * @api {DELETE} /api/delete Remove Activation Key
 * @apiName RemoveActivationKey
 * Example request body:
 * ```json
 * {
 *   "user_email": "user@example.com",
 *   "specify_key": "activation-key-to-remove", <-- Optional! 
 *   "admin": "admin-secret-key"
 * }
 * ```
 * 
 */
async function remove(request: Request, env: Env): Promise<Response> {
	const { user_email, specify_key, admin } = await request.json() as {user_email?: string, specify_key?: string, admin?: string};

	if (!user_email || !admin) {
		return new Response("Missing user_email or admin", { status: 400 });
	}

	if(!ADMIN_KEY) {
		return new Response("ADMIN_KEY is not set in the environment variables.", { status: 500 });
	}

	if (admin !== ADMIN_KEY) {
		return new Response("Unauthorized", { status: 403 });
	}

	// if the user isn't in the database, return 404
	const userExists = await env.DB.prepare(
		`SELECT * FROM Keys WHERE UserEmail = ?`
	).bind(user_email).first();
	if (!userExists) {
		return new Response(`No activation key found for user ${user_email}`, { status: 409 });
	}

	const res = await env.DB.prepare(
		specify_key? `DELETE FROM Keys WHERE UserEmail = ? AND ActivationKey = ?`
		: `DELETE FROM Keys WHERE UserEmail = ?`
	).bind(user_email, specify_key ? specify_key : null).run();

	if (res.meta.changes && res.meta.changes > 0) {
		return new Response(`Activation key(s) removed for user ${user_email}`, { status: 200 });
	} else {
		return new Response(`No activation key found for user ${user_email}`, { status: 404 });
	}
}
