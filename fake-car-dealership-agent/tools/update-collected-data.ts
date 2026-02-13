// ============================================================================
// Tool: update_collected_data
// Saves/updates customer information gathered during the conversation.
// Risk Level: HIGH — data modification operation (PII storage)
//
// HIGH RISK: This tool writes customer personally identifiable information
// (PII) to the customer profile. In a production system this would trigger
// data-protection compliance checks (GDPR, CCPA). Handle with care.
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, CollectedDataConfirmation, CollectedData } from "../types";

/**
 * OpenAI function-calling tool definition for update_collected_data.
 *
 * Saves or updates customer information that has been collected during
 * the conversation. This is called once the agent has gathered the
 * customer's name, phone, email, vehicle VIN, or advisor preference.
 *
 * HIGH RISK — This is a data modification operation that stores PII.
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "update_collected_data",
    description:
      "Saves or updates customer information collected during the conversation. Call this once customer details (name, phone, email, vehicle VIN) have been gathered. HIGH RISK: stores personally identifiable information.",
    parameters: {
      type: "object",
      properties: {
        customer_name: {
          type: "string",
          description: "Customer's full name",
        },
        customer_phone: {
          type: "string",
          description: "Customer's phone number",
        },
        customer_email: {
          type: "string",
          description: "Customer's email address",
        },
        vehicle_vin: {
          type: "string",
          description: "VIN of the customer's vehicle",
        },
        preferred_advisor_id: {
          type: "string",
          description: "ID of the customer's preferred service advisor",
        },
        notes: {
          type: "string",
          description:
            "Any additional notes about the customer or their request",
        },
      },
      required: [],
    },
  },
};

/**
 * Mock handler for update_collected_data.
 * Always succeeds — echoes back the data that was saved. In a real system
 * this would write to a CRM or customer database.
 *
 * HIGH RISK: Data modification operation — stores customer PII.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const data: CollectedData = {};

  if (args.customer_name) data.customer_name = args.customer_name as string;
  if (args.customer_phone) data.customer_phone = args.customer_phone as string;
  if (args.customer_email) data.customer_email = args.customer_email as string;
  if (args.vehicle_vin) data.vehicle_vin = args.vehicle_vin as string;
  if (args.preferred_advisor_id)
    data.preferred_advisor_id = args.preferred_advisor_id as string;
  if (args.notes) data.notes = args.notes as string;

  const savedFields = Object.keys(data);

  const confirmation: CollectedDataConfirmation = {
    saved: true,
    data,
    message:
      savedFields.length > 0
        ? `Customer data saved: ${savedFields.join(", ")}.`
        : "No data fields provided to save.",
  };

  return JSON.stringify(confirmation);
};
