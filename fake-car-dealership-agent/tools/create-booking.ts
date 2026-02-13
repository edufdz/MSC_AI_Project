// ============================================================================
// Tool: create_booking
// Creates a new service appointment booking.
// Risk Level: MEDIUM — creates a booking record (state-changing operation)
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, BookingConfirmation } from "../types";
import { findAdvisor, findService, generateBookingId } from "../mock-data";

/**
 * OpenAI function-calling tool definition for create_booking.
 *
 * Books a service appointment for a customer. Requires customer details,
 * vehicle VIN, service type, date, and time slot. Optionally accepts a
 * preferred service advisor ID.
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "create_booking",
    description:
      "Creates a new service appointment booking at Prestige Motors. Returns a booking confirmation with ID, advisor, estimated duration, and cost.",
    parameters: {
      type: "object",
      properties: {
        customer_name: {
          type: "string",
          description: "Full name of the customer",
        },
        customer_phone: {
          type: "string",
          description:
            "Customer phone number including area code (e.g. '(512) 555-0123')",
        },
        vehicle_vin: {
          type: "string",
          description: "VIN of the vehicle to be serviced",
        },
        service_type: {
          type: "string",
          description:
            "Type of service requested (e.g. 'oil_change', 'brake_inspection', 'full_service')",
        },
        date: {
          type: "string",
          description: "Appointment date in YYYY-MM-DD format",
        },
        time_slot: {
          type: "string",
          description: "Appointment time slot (e.g. '09:00', '10:30')",
        },
        advisor_id: {
          type: "string",
          description:
            "Optional preferred service advisor ID (e.g. 'ADV-001')",
        },
      },
      required: [
        "customer_name",
        "customer_phone",
        "vehicle_vin",
        "service_type",
        "date",
        "time_slot",
      ],
    },
  },
};

/**
 * Mock handler for create_booking.
 * Always succeeds — generates a fake booking ID and returns a confirmation
 * object with all booking details, including advisor assignment, estimated
 * duration, and cost range from the service catalog.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const customerName = args.customer_name as string;
  const customerPhone = args.customer_phone as string;
  const vehicleVin = args.vehicle_vin as string;
  const serviceType = args.service_type as string;
  const date = args.date as string;
  const timeSlot = args.time_slot as string;
  const advisorId = args.advisor_id as string | undefined;

  const advisor = findAdvisor(advisorId);
  const service = findService(serviceType);

  const estimatedDuration = service?.estimated_duration_minutes ?? 60;
  const estimatedCost = service
    ? `$${service.price_range.min}–$${service.price_range.max}`
    : "$100–$200 (estimate)";

  const confirmation: BookingConfirmation = {
    booking_id: generateBookingId(),
    customer_name: customerName,
    customer_phone: customerPhone,
    vehicle_vin: vehicleVin,
    service_type: serviceType,
    date,
    time_slot: timeSlot,
    advisor_name: advisor.name,
    advisor_id: advisor.id,
    estimated_duration_minutes: estimatedDuration,
    estimated_cost: estimatedCost,
    status: "confirmed",
    message: `Booking confirmed! Your ${service?.display_name ?? serviceType} appointment is set for ${date} at ${timeSlot} with ${advisor.name}. Estimated duration: ${estimatedDuration} minutes. Please arrive 10 minutes early.`,
  };

  return JSON.stringify(confirmation);
};
