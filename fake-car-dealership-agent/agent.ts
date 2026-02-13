// ============================================================================
// Agent Core — Handles multi-turn conversation with OpenAI function calling
// ============================================================================

import OpenAI from "openai";
import type {
  ChatCompletionMessageParam,
  ChatCompletionAssistantMessageParam,
  ChatCompletionToolMessageParam,
} from "openai/resources/chat/completions";
import type { AgentResponse } from "./types";
import { SYSTEM_PROMPT } from "./prompts/system-prompt";
import { toolDefinitions, toolHandlers } from "./tools";

const MODEL = "gpt-4o-mini";

export class AutoServeAgent {
  private client: OpenAI;
  private conversationHistory: ChatCompletionMessageParam[];

  constructor(apiKey?: string) {
    this.client = new OpenAI({
      apiKey: apiKey || process.env.OPENAI_API_KEY,
    });

    this.conversationHistory = [
      { role: "system", content: SYSTEM_PROMPT },
    ];
  }

  /**
   * Send a user message and get the agent's response.
   * Handles the full function-calling loop: if OpenAI returns tool_calls,
   * each tool is executed and its result is fed back until the model
   * produces a final text response.
   */
  async chat(userMessage: string): Promise<AgentResponse> {
    this.conversationHistory.push({
      role: "user",
      content: userMessage,
    });

    const toolCallLog: AgentResponse["tool_calls"] = [];

    // Loop until the model produces a final text response (no more tool calls)
    while (true) {
      const completion = await this.client.chat.completions.create({
        model: MODEL,
        messages: this.conversationHistory,
        tools: toolDefinitions,
        tool_choice: "auto",
      });

      const choice = completion.choices[0];
      const assistantMessage = choice.message;

      // Add the assistant's message to history
      const historyEntry: ChatCompletionAssistantMessageParam = {
        role: "assistant",
        content: assistantMessage.content ?? null,
      };
      if (assistantMessage.tool_calls && assistantMessage.tool_calls.length > 0) {
        historyEntry.tool_calls = assistantMessage.tool_calls;
      }
      this.conversationHistory.push(historyEntry);

      // If no tool calls, we have our final response
      if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
        return {
          message: assistantMessage.content ?? "",
          tool_calls: toolCallLog,
        };
      }

      // Execute each tool call and feed results back
      for (const toolCall of assistantMessage.tool_calls) {
        const toolName = toolCall.function.name;
        const toolArgs = JSON.parse(toolCall.function.arguments) as Record<string, unknown>;

        let result: string;
        const handler = toolHandlers[toolName];
        if (handler) {
          try {
            result = await handler(toolArgs);
          } catch (err) {
            result = JSON.stringify({
              error: true,
              message: `Tool execution failed: ${err instanceof Error ? err.message : String(err)}`,
            });
          }
        } else {
          result = JSON.stringify({
            error: true,
            message: `Unknown tool: ${toolName}`,
          });
        }

        // Log the tool call
        toolCallLog.push({
          tool_name: toolName,
          tool_id: toolCall.id,
          arguments: toolArgs,
          result,
        });

        // Add tool result to conversation history
        const toolMessage: ChatCompletionToolMessageParam = {
          role: "tool",
          tool_call_id: toolCall.id,
          content: result,
        };
        this.conversationHistory.push(toolMessage);
      }
      // Continue the loop — the model will process tool results and may
      // issue more tool calls or produce a final text response.
    }
  }

  /** Reset the conversation, keeping only the system prompt. */
  reset(): void {
    this.conversationHistory = [
      { role: "system", content: SYSTEM_PROMPT },
    ];
  }

  /** Get the current conversation history (for debugging). */
  getHistory(): ChatCompletionMessageParam[] {
    return [...this.conversationHistory];
  }
}
