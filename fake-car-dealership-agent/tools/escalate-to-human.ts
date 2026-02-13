// ============================================================================
// Tool: escalate_to_human
// Escalates the conversation to a human service advisor.
// Risk Level: MEDIUM — triggers an external notification workflow
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, EscalationConfirmation } from "../types";
import { generateTicketId } from "../mock-data";

/**
 * OpenAI function-calling tool definition for escalate_to_human.
 *
 * Escalates the current conversation to a human service advisor. Should
 * be used for complaints, warranty disputes, pricing negotiations, or
 * anything the AI agent cannot resolve on its own.
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "escalate_to_human",
    description:
      "Escalates the conversation to a human service advisor at Prestige Motors. Use for complaints, warranty disputes, pricing negotiations, or issues the AI cannot resolve.",
    parameters: {
      type: "object",
      properties: {
        reason: {
          type: "string",
          description:
            "The reason for escalation (e.g. 'Customer has a warranty dispute', 'Pricing negotiation requested')",
        },
        customer_name: {
          type: "string",
          description: "Full name of the customer",
        },
        customer_phone: {
          type: "string",
          description: "Customer phone number for callback",
        },
        conversation_summary: {
          type: "string",
          description:
            "Brief summary of the conversation so far so the human advisor has context",
        },
      },
      required: [
        "reason",
        "customer_name",
        "customer_phone",
        "conversation_summary",
      ],
    },
  },
};

/**
 * Mock handler for escalate_to_human.
 * Always succeeds — generates a fake escalation ticket ID and confirms
 * that a human advisor will follow up within 2 hours.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const reason = args.reason as string;
  const customerName = args.customer_name as string;
  const customerPhone = args.customer_phone as string;

  const confirmation: EscalationConfirmation = {
    ticket_id: generateTicketId(),
    reason,
    customer_name: customerName,
    customer_phone: customerPhone,
    estimated_response_time: "within 2 hours",
    status: "escalated",
    message: `Your request has been escalated to a service advisor. Ticket ID: ${generateTicketId()}. A team member will contact you at ${customerPhone} within 2 hours during business hours (Mon–Fri 8 AM–6 PM, Sat 9 AM–1 PM).`,
  };

  return JSON.stringify(confirmation);
};
