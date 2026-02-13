// ============================================================================
// AutoServe AI — CLI Entry Point
// A simple interactive conversation loop for testing the agent.
// ============================================================================

import * as dotenv from "dotenv";
import * as readline from "readline";
import { AutoServeAgent } from "./agent";
import { FALLBACK_TEMPLATES } from "./prompts/fallback-templates";

dotenv.config();

const CYAN = "\x1b[36m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const DIM = "\x1b[2m";
const RESET = "\x1b[0m";

function printBanner(): void {
  console.log(`
${CYAN}╔══════════════════════════════════════════════════════════╗
║            AutoServe AI — Prestige Motors BMW             ║
║         Service Scheduling Agent (Mock / Testing)         ║
╠══════════════════════════════════════════════════════════╣
║  Type your message and press Enter to chat.              ║
║  Commands:  /reset  — start a new conversation           ║
║             /quit   — exit                               ║
╚══════════════════════════════════════════════════════════╝${RESET}
`);
}

async function main(): Promise<void> {
  if (!process.env.OPENAI_API_KEY) {
    console.error(
      "Error: OPENAI_API_KEY not set. Create a .env file with your key or export it."
    );
    process.exit(1);
  }

  const agent = new AutoServeAgent();

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  printBanner();

  // Print the greeting
  console.log(`${GREEN}AutoServe AI:${RESET} ${FALLBACK_TEMPLATES.greeting}\n`);

  const prompt = (): void => {
    rl.question(`${CYAN}You:${RESET} `, async (input) => {
      const trimmed = input.trim();

      if (!trimmed) {
        prompt();
        return;
      }

      if (trimmed === "/quit" || trimmed === "/exit") {
        console.log("\nGoodbye! Thank you for visiting Prestige Motors.\n");
        rl.close();
        process.exit(0);
      }

      if (trimmed === "/reset") {
        agent.reset();
        console.log(`\n${DIM}[Conversation reset]${RESET}\n`);
        console.log(
          `${GREEN}AutoServe AI:${RESET} ${FALLBACK_TEMPLATES.greeting}\n`
        );
        prompt();
        return;
      }

      try {
        const response = await agent.chat(trimmed);

        // Show tool calls if any occurred
        if (response.tool_calls.length > 0) {
          for (const tc of response.tool_calls) {
            console.log(
              `${DIM}  [tool] ${tc.tool_name}(${JSON.stringify(tc.arguments)})${RESET}`
            );
          }
        }

        console.log(`\n${GREEN}AutoServe AI:${RESET} ${response.message}\n`);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : String(err);
        console.error(`\n${YELLOW}Error:${RESET} ${message}\n`);
        console.log(
          `${GREEN}AutoServe AI:${RESET} ${FALLBACK_TEMPLATES.tool_error}\n`
        );
      }

      prompt();
    });
  };

  prompt();
}

main();
