// ============================================================================
// Fallback Templates — Pre-written messages for common failure/success cases
// ============================================================================

import type { FallbackTemplates } from "../types";

export const FALLBACK_TEMPLATES: FallbackTemplates = {
  tool_error:
    "I'm sorry, I encountered an unexpected issue while processing your request. Let me try a different approach. Could you please repeat what you need?",

  vehicle_not_found:
    "I wasn't able to find a vehicle with that information in our system. Could you double-check the license plate or VIN number and try again? If your vehicle is new to Prestige Motors, we may need to add it — I can connect you with an advisor to help.",

  no_availability:
    "Unfortunately, there are no available appointments on that date. Would you like me to check a different day? We typically have the best availability on weekday mornings.",

  booking_failed:
    "I'm sorry, something went wrong while creating your booking. Let me connect you with a service advisor who can finalize the appointment for you. One moment please.",

  escalation_sent:
    "I've forwarded your request to one of our service advisors. You'll receive a callback at the phone number you provided within 2 hours during business hours. Your ticket ID is included above for reference. Is there anything else I can help with in the meantime?",

  greeting:
    "Hello! Welcome to Prestige Motors BMW in Austin. I'm AutoServe AI, your virtual service assistant. I can help you look up your vehicle, check service options, and book appointments. How can I assist you today?",
};
