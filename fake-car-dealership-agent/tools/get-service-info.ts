// ============================================================================
// Tool: get_service_info
// Retrieves details about a specific service from the catalog.
// Risk Level: LOW — read-only operation
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, ServiceInfoResult } from "../types";
import { findService, SERVICE_CATALOG } from "../mock-data";

/**
 * OpenAI function-calling tool definition for get_service_info.
 *
 * Returns detailed information about a service type including description,
 * estimated duration, price range, and what is included.
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "get_service_info",
    description:
      "Retrieves detailed information about a service type offered at Prestige Motors, including description, estimated duration, price range, and what is included.",
    parameters: {
      type: "object",
      properties: {
        service_type: {
          type: "string",
          description: `The service type key. Available services: ${SERVICE_CATALOG.map((s) => s.service_type).join(", ")}`,
        },
      },
      required: ["service_type"],
    },
  },
};

/**
 * Mock handler for get_service_info.
 * Looks up a service in the hardcoded catalog and returns its details.
 * Returns a helpful error if the service type is not found.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const serviceType = args.service_type as string;

  if (!serviceType) {
    const result: ServiceInfoResult = {
      found: false,
      service: null,
      message: "Please provide a service_type to look up.",
    };
    return JSON.stringify(result);
  }

  const service = findService(serviceType);

  if (!service) {
    const available = SERVICE_CATALOG.map((s) => s.service_type).join(", ");
    const result: ServiceInfoResult = {
      found: false,
      service: null,
      message: `Service type "${serviceType}" not found. Available services: ${available}`,
    };
    return JSON.stringify(result);
  }

  const result: ServiceInfoResult = {
    found: true,
    service,
    message: `${service.display_name}: ${service.description} Duration: ~${service.estimated_duration_minutes} min. Price: $${service.price_range.min}–$${service.price_range.max}.`,
  };
  return JSON.stringify(result);
};
