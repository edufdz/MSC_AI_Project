# AutoServe AI — Fake Car Dealership Agent

A mock car dealership service scheduling agent built for testing and development. Uses OpenAI function calling with entirely hardcoded/fake data — no real API connections.

**Dealership:** Prestige Motors (fictitious BMW dealership)
**Location:** 123 Motorway Drive, Austin, TX 78701
**Phone:** (512) 555-0199

## Quick Start

```bash
# Install dependencies
bun install

# Set your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Run the agent
bun index.ts
```

## Architecture

```
fake-car-dealership-agent/
├── index.ts                  # CLI conversation loop
├── agent.ts                  # Core agent: OpenAI chat + tool-call loop
├── tools/
│   ├── index.ts              # Barrel export of all tool definitions & handlers
│   ├── lookup-vehicle.ts     # Vehicle lookup by plate/VIN
│   ├── check-availability.ts # Appointment slot availability
│   ├── create-booking.ts     # Booking creation
│   ├── get-service-info.ts   # Service catalog lookup
│   ├── escalate-to-human.ts  # Human escalation
│   └── update-collected-data.ts # Customer data persistence (HIGH RISK)
├── prompts/
│   ├── system-prompt.ts      # Main agent instruction prompt
│   └── fallback-templates.ts # Pre-written messages for common cases
├── mock-data.ts              # All hardcoded fake data
├── types.ts                  # TypeScript interfaces
├── package.json
└── tsconfig.json
```

## Tools

| Tool | Description | Risk Level |
|------|-------------|------------|
| `lookup_vehicle` | Find vehicle by plate or VIN | Low |
| `check_availability` | Check open appointment slots | Low |
| `create_booking` | Book a service appointment | Medium |
| `get_service_info` | Get service details and pricing | Low |
| `escalate_to_human` | Transfer to human advisor | Medium |
| `update_collected_data` | Save customer PII | **High** |

## Mock Data

### Vehicles

| Plate | VIN | Model | Year | Color |
|-------|-----|-------|------|-------|
| TX-BMW-3301 | WBA8E9C50JK285901 | 330i | 2023 | Alpine White |
| TX-LUX-0055 | 5UXCR6C05L9B78342 | X5 xDrive40i | 2022 | Phytonic Blue |
| TX-540-7788 | WBAJB9C52KB892417 | 540i xDrive | 2024 | Black Sapphire |
| TX-M3-2024 | WBS8M9C76L5B03921 | M3 Competition | 2024 | Isle of Man Green |

### Service Advisors

- **James Harrington** (ADV-001) — General Service & Maintenance
- **Sarah Chen** (ADV-002) — Performance & M Series
- **Mike Torres** (ADV-003) — Electrical & Diagnostics

### Availability Rules

- **Weekdays:** 4 slots (09:00, 10:30, 13:00, 15:30)
- **Saturday:** 2 slots (09:00, 10:30)
- **Sunday:** Closed
- **Fully booked dates:** 2026-02-16, 2026-02-23, 2026-03-02

## Example Conversations

### Happy Path — Customer Books an Oil Change

```
You: Hi, I'd like to book an oil change for my BMW.

AutoServe AI: Hello! Welcome to Prestige Motors BMW in Austin. I'd be happy to
help you book an oil change. Could you provide me with your vehicle's license
plate number or VIN so I can look it up?

You: Sure, plate is TX-BMW-3301

  [tool] lookup_vehicle({"license_plate":"TX-BMW-3301"})

AutoServe AI: I found your vehicle — a 2023 BMW 330i in Alpine White with
18,420 miles. Your last service was on September 15, 2025. An oil change sounds
like good timing! Before I check available dates, could I get your full name
and phone number?

You: John Miller, (512) 555-0234

  [tool] update_collected_data({"customer_name":"John Miller","customer_phone":"(512) 555-0234","vehicle_vin":"WBA8E9C50JK285901"})

AutoServe AI: Thanks, John! I've saved your details. What date works best for
your oil change?

You: How about next Wednesday, March 4th?

  [tool] check_availability({"date":"2026-03-04","service_type":"oil_change"})

AutoServe AI: We have 4 available slots on March 4th: 09:00, 10:30, 13:00, and
15:30. Which time works best for you?

You: 10:30 works great.

  [tool] get_service_info({"service_type":"oil_change"})

AutoServe AI: Let me confirm the details:
- **Service:** Oil Change ($89–$149)
- **Vehicle:** 2023 BMW 330i (VIN: WBA8E9C50JK285901)
- **Date:** March 4, 2026 at 10:30 AM
- **Estimated duration:** 45 minutes

Shall I go ahead and book this?

You: Yes, please!

  [tool] create_booking({"customer_name":"John Miller","customer_phone":"(512) 555-0234","vehicle_vin":"WBA8E9C50JK285901","service_type":"oil_change","date":"2026-03-04","time_slot":"10:30"})

AutoServe AI: Your appointment is confirmed! Here are the details:

- **Booking ID:** BK-2026-4827
- **Service Advisor:** James Harrington
- **Date:** March 4, 2026 at 10:30 AM
- **Estimated cost:** $89–$149
- **Duration:** ~45 minutes

Please arrive about 10 minutes early. Is there anything else I can help with?

You: No, that's all. Thanks!

AutoServe AI: You're welcome, John! See you on March 4th. Have a great day!
```

### Failure Path — Vehicle Not Found

```
You: I need to schedule a brake check. My plate is ABC-1234.

  [tool] lookup_vehicle({"license_plate":"ABC-1234"})

AutoServe AI: I wasn't able to find a vehicle with plate "ABC-1234" in our
system. Could you double-check the license plate number or try providing the
VIN instead?

You: Hmm, maybe try VIN WBAXXXXXXXX12345

  [tool] lookup_vehicle({"vin":"WBAXXXXXXXX12345"})

AutoServe AI: I still couldn't find that vehicle. This might mean the vehicle
hasn't been registered at Prestige Motors before. I'd recommend calling us at
(512) 555-0199 so a team member can help add your vehicle to our system and
get you scheduled. Would you like me to connect you with an advisor?

You: Yes please, this is frustrating.

  [tool] escalate_to_human({"reason":"Vehicle not found in system, customer frustrated","customer_name":"Unknown","customer_phone":"Unknown","conversation_summary":"Customer wants brake check but vehicle not found by plate ABC-1234 or VIN WBAXXXXXXXX12345."})

AutoServe AI: I completely understand the frustration. I've escalated this to
our service team — a human advisor will reach out to help get your vehicle
added and your brake check scheduled. Is there a phone number where they can
reach you?
```
