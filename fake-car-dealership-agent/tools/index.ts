// ============================================================================
// Tools Index — Exports all tool definitions and handlers
// ============================================================================

import type { ChatCompletionTool } from "openai/resources/chat/completions";
import type { ToolHandler } from "../types";

import * as lookupVehicle from "./lookup-vehicle";
import * as checkAvailability from "./check-availability";
import * as createBooking from "./create-booking";
import * as getServiceInfo from "./get-service-info";
import * as escalateToHuman from "./escalate-to-human";
import * as updateCollectedData from "./update-collected-data";

/** All tool definitions as an array, ready to pass to OpenAI chat completions. */
export const toolDefinitions: ChatCompletionTool[] = [
  lookupVehicle.definition,
  checkAvailability.definition,
  createBooking.definition,
  getServiceInfo.definition,
  escalateToHuman.definition,
  updateCollectedData.definition,
];

/** Map of tool name → handler function for dispatching tool calls. */
export const toolHandlers: Record<string, ToolHandler> = {
  lookup_vehicle: lookupVehicle.handler,
  check_availability: checkAvailability.handler,
  create_booking: createBooking.handler,
  get_service_info: getServiceInfo.handler,
  escalate_to_human: escalateToHuman.handler,
  update_collected_data: updateCollectedData.handler,
};
