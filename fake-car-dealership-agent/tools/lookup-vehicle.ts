// ============================================================================
// Tool: lookup_vehicle
// Retrieves vehicle details and service history by license plate or VIN.
// Risk Level: LOW — read-only operation
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler, VehicleLookupResult } from "../types";
import { findVehicle } from "../mock-data";

/**
 * OpenAI function-calling tool definition for lookup_vehicle.
 *
 * Looks up a vehicle in the dealership database using a license plate
 * or VIN number. Returns full vehicle details including service history.
 * At least one of license_plate or vin must be provided.
 */
export const definition: ChatCompletionTool = {
  type: "function",
  function: {
    name: "lookup_vehicle",
    description:
      "Retrieves vehicle details and service history by license plate or VIN. At least one identifier must be provided.",
    parameters: {
      type: "object",
      properties: {
        license_plate: {
          type: "string",
          description:
            "The vehicle license plate number (e.g. 'TX-BMW-3301')",
        },
        vin: {
          type: "string",
          description:
            "The Vehicle Identification Number, 17 characters (e.g. 'WBA8E9C50JK285901')",
        },
      },
      required: [],
    },
  },
};

/**
 * Mock handler for lookup_vehicle.
 * Searches hardcoded vehicles by plate or VIN and returns the match.
 */
export const handler: ToolHandler = async (
  args: Record<string, unknown>
): Promise<string> => {
  const licensePlate = args.license_plate as string | undefined;
  const vin = args.vin as string | undefined;

  if (!licensePlate && !vin) {
    const result: VehicleLookupResult = {
      found: false,
      vehicle: null,
      message:
        "Please provide at least one identifier: license_plate or vin.",
    };
    return JSON.stringify(result);
  }

  const vehicle = findVehicle(licensePlate, vin);

  if (!vehicle) {
    const result: VehicleLookupResult = {
      found: false,
      vehicle: null,
      message: `No vehicle found matching ${licensePlate ? `plate "${licensePlate}"` : ""}${licensePlate && vin ? " or " : ""}${vin ? `VIN "${vin}"` : ""}. Please double-check the information and try again.`,
    };
    return JSON.stringify(result);
  }

  const result: VehicleLookupResult = {
    found: true,
    vehicle,
    message: `Found ${vehicle.year} ${vehicle.make} ${vehicle.model} (${vehicle.color}), ${vehicle.mileage.toLocaleString()} miles.`,
  };
  return JSON.stringify(result);
};
