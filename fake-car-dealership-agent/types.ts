// ============================================================================
// AutoServe AI — Type Definitions
// All TypeScript interfaces for the fake car dealership agent
// ============================================================================

import type { ChatCompletionTool, ChatCompletionMessageParam } from "openai/resources/chat/completions";

// --- Vehicle Types ---

export interface ServiceHistoryEntry {
  date: string;
  service_type: string;
  mileage: number;
  notes: string;
}

export interface Vehicle {
  vin: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  color: string;
  mileage: number;
  last_service_date: string;
  service_history: ServiceHistoryEntry[];
}

export interface VehicleLookupResult {
  found: boolean;
  vehicle: Vehicle | null;
  message: string;
}

// --- Availability Types ---

export interface TimeSlot {
  time: string;
  available: boolean;
}

export interface AvailabilityResult {
  date: string;
  service_type: string | null;
  available_slots: string[];
  message: string;
}

// --- Booking Types ---

export interface BookingRequest {
  customer_name: string;
  customer_phone: string;
  vehicle_vin: string;
  service_type: string;
  date: string;
  time_slot: string;
  advisor_id?: string;
}

export interface BookingConfirmation {
  booking_id: string;
  customer_name: string;
  customer_phone: string;
  vehicle_vin: string;
  service_type: string;
  date: string;
  time_slot: string;
  advisor_name: string;
  advisor_id: string;
  estimated_duration_minutes: number;
  estimated_cost: string;
  status: "confirmed";
  message: string;
}

// --- Service Info Types ---

export interface ServiceInfo {
  service_type: string;
  display_name: string;
  description: string;
  estimated_duration_minutes: number;
  price_range: {
    min: number;
    max: number;
    currency: string;
  };
  includes: string[];
}

export interface ServiceInfoResult {
  found: boolean;
  service: ServiceInfo | null;
  message: string;
}

// --- Escalation Types ---

export interface EscalationRequest {
  reason: string;
  customer_name: string;
  customer_phone: string;
  conversation_summary: string;
}

export interface EscalationConfirmation {
  ticket_id: string;
  reason: string;
  customer_name: string;
  customer_phone: string;
  estimated_response_time: string;
  status: "escalated";
  message: string;
}

// --- Collected Data Types ---

export interface CollectedData {
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  vehicle_vin?: string;
  preferred_advisor_id?: string;
  notes?: string;
}

export interface CollectedDataConfirmation {
  saved: boolean;
  data: CollectedData;
  message: string;
}

// --- Service Advisor Types ---

export interface ServiceAdvisor {
  id: string;
  name: string;
  specialization: string;
  available: boolean;
}

// --- Tool Handler Types ---

export type ToolHandler = (args: Record<string, unknown>) => Promise<string>;

export interface ToolDefinitionWithHandler {
  definition: ChatCompletionTool;
  handler: ToolHandler;
}

// --- Agent Types ---

export type MessageRole = "system" | "user" | "assistant" | "tool";

export type ConversationMessage = ChatCompletionMessageParam;

export interface AgentResponse {
  message: string;
  tool_calls: Array<{
    tool_name: string;
    tool_id: string;
    arguments: Record<string, unknown>;
    result: string;
  }>;
}

// --- Fallback Templates ---

export interface FallbackTemplates {
  tool_error: string;
  vehicle_not_found: string;
  no_availability: string;
  booking_failed: string;
  escalation_sent: string;
  greeting: string;
}
