// ============================================================================
// AutoServe AI — HTTP API for Phase C (Agent Debugger)
// Exposes POST /chat compatible with the debugger's APIAgentConnector.
// ============================================================================
// Bun loads .env automatically; no dotenv import needed.

import { AutoServeAgent } from "./agent";

const PORT = Number(process.env.PORT ?? 3099);

/** One agent instance per session (session_id from Phase C). */
const sessions = new Map<string, AutoServeAgent>();

function getOrCreateAgent(sessionId: string | null): AutoServeAgent {
  const id = sessionId ?? "default";
  let agent = sessions.get(id);
  if (!agent) {
    agent = new AutoServeAgent();
    sessions.set(id, agent);
  }
  return agent;
}

const server = Bun.serve({
  port: PORT,
  fetch(req) {
    const url = new URL(req.url);

    // Health check for pipelines
    if (url.pathname === "/health" && req.method === "GET") {
      return Response.json({ status: "ok", service: "autoserve-ai" });
    }

    // Phase C connector: POST /chat with { message, session_id }
    if (url.pathname === "/chat" && req.method === "POST") {
      return req
        .json()
        .then((body: { message?: string; session_id?: string }) => {
          const message = typeof body?.message === "string" ? body.message.trim() : "";
          if (!message) {
            return Response.json(
              { error: "Missing or empty 'message' in body" },
              { status: 400 }
            );
          }
          const sessionId = typeof body?.session_id === "string" ? body.session_id : null;
          const agent = getOrCreateAgent(sessionId);
          return agent.chat(message).then(
            (result) =>
              Response.json({
                response: result.message,
                tool_calls: result.tool_calls,
              }),
            (err: unknown) => {
              const message = err instanceof Error ? err.message : String(err);
              return Response.json(
                { error: "Agent error", detail: message },
                { status: 500 }
              );
            }
          );
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : String(err);
          return Response.json(
            { error: "Bad request", detail: message },
            { status: 400 }
          );
        });
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`AutoServe AI API listening on http://localhost:${server.port}`);
console.log(`  POST /chat   — send message (body: { message, session_id? })`);
console.log(`  GET  /health — liveness check`);
console.log("");
console.log("Phase C: set agent_map.json api_endpoint to http://localhost:" + server.port);
