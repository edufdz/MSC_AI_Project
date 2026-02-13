// ============================================================================
// Tool: check_availability
// Checks available appointment time slots for a given date.
// Risk Level: LOW — read-only operation
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, AvailabilityResult } from "../types";
import { getAvailableSlots } from "../mock-data";

/**
 * OpenAI function-calling tool definition for check_availability.
 *
 * Queries available service appointment slots for a specific date.
 * Optionally filters by service type (though in this mock, the service
 * type does not affect slot availability).
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "check_availability",
    description:
      "Checks available appointment time slots for a given date at Prestige Motors. Returns a list of open slots.",
    parameters: {
      type: "object",
      properties: {
        date: {
          type: "string",
          description:
            "The date to check availability for, in YYYY-MM-DD format (e.g. '2026-03-15')",
        },
        service_type: {
          type: "string",
          description:
            "Optional service type to check availability for (e.g. 'oil_change', 'full_service')",
        },
      },
      required: ["date"],
    },
  },
};

/**
 * Mock handler for check_availability.
 * Returns time slots based on the day of week — weekdays get 4 slots,
 * Saturdays get 2, Sundays return none (closed), and specific dates
 * are marked as fully booked.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const date = args.date as string;
  const serviceType = (args.service_type as string) || null;

  if (!date) {
    const result: AvailabilityResult = {
      date: "",
      service_type: serviceType,
      available_slots: [],
      message: "Please provide a date in YYYY-MM-DD format.",
    };
    return JSON.stringify(result);
  }

  const slots = getAvailableSlots(date);

  const dayOfWeek = new Date(date + "T12:00:00").getDay();
  const isSunday = dayOfWeek === 0;

  let message: string;
  if (isSunday) {
    message =
      "Prestige Motors is closed on Sundays. Please choose another day.";
  } else if (slots.length === 0) {
    message = `Sorry, there are no available slots on ${date}. Please try a different date.`;
  } else {
    message = `We have ${slots.length} available slot${slots.length > 1 ? "s" : ""} on ${date}: ${slots.join(", ")}.`;
  }

  const result: AvailabilityResult = {
    date,
    service_type: serviceType,
    available_slots: slots,
    message,
  };
  return JSON.stringify(result);
};
