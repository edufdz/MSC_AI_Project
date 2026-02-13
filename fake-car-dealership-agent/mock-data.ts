// ============================================================================
// AutoServe AI — Mock Data
// All hardcoded fake data for the car dealership agent
// ============================================================================

import type {
  Vehicle,
  ServiceAdvisor,
  ServiceInfo,
} from "./types";

// --- Mock Vehicles ---

export const MOCK_VEHICLES: Vehicle[] = [
  {
    vin: "WBA8E9C50JK285901",
    license_plate: "TX-BMW-3301",
    make: "BMW",
    model: "330i",
    year: 2023,
    color: "Alpine White",
    mileage: 18420,
    last_service_date: "2025-09-15",
    service_history: [
      {
        date: "2025-09-15",
        service_type: "oil_change",
        mileage: 15200,
        notes: "Synthetic oil change, filter replaced",
      },
      {
        date: "2025-03-10",
        service_type: "tire_rotation",
        mileage: 10800,
        notes: "Rotated all four tires, pressure adjusted to 34 PSI",
      },
      {
        date: "2024-08-22",
        service_type: "full_service",
        mileage: 5100,
        notes: "First annual service — all checks passed",
      },
    ],
  },
  {
    vin: "5UXCR6C05L9B78342",
    license_plate: "TX-LUX-0055",
    make: "BMW",
    model: "X5 xDrive40i",
    year: 2022,
    color: "Phytonic Blue Metallic",
    mileage: 34870,
    last_service_date: "2025-11-02",
    service_history: [
      {
        date: "2025-11-02",
        service_type: "brake_inspection",
        mileage: 33500,
        notes: "Front pads at 45%, rear pads at 60% — no replacement needed yet",
      },
      {
        date: "2025-06-18",
        service_type: "oil_change",
        mileage: 28900,
        notes: "Synthetic oil change, cabin air filter replaced",
      },
      {
        date: "2025-01-05",
        service_type: "annual_mot",
        mileage: 22400,
        notes: "Annual inspection passed, minor brake fluid top-up",
      },
      {
        date: "2024-07-12",
        service_type: "ac_check",
        mileage: 17200,
        notes: "AC refrigerant recharged, system operating normally",
      },
    ],
  },
  {
    vin: "WBAJB9C52KB892417",
    license_plate: "TX-540-7788",
    make: "BMW",
    model: "540i xDrive",
    year: 2024,
    color: "Black Sapphire Metallic",
    mileage: 8950,
    last_service_date: "2025-12-01",
    service_history: [
      {
        date: "2025-12-01",
        service_type: "oil_change",
        mileage: 8200,
        notes: "First oil change, all fluids topped up",
      },
    ],
  },
  {
    vin: "WBS8M9C76L5B03921",
    license_plate: "TX-M3-2024",
    make: "BMW",
    model: "M3 Competition",
    year: 2024,
    color: "Isle of Man Green",
    mileage: 12340,
    last_service_date: "2025-10-20",
    service_history: [
      {
        date: "2025-10-20",
        service_type: "oil_change",
        mileage: 11000,
        notes: "High-performance synthetic oil change",
      },
      {
        date: "2025-05-14",
        service_type: "brake_inspection",
        mileage: 7500,
        notes: "Performance brake pads inspected — excellent condition",
      },
      {
        date: "2025-05-14",
        service_type: "tire_rotation",
        mileage: 7500,
        notes: "Staggered setup — front/rear swapped left-to-right only",
      },
    ],
  },
];

// --- Mock Service Advisors ---

export const MOCK_ADVISORS: ServiceAdvisor[] = [
  {
    id: "ADV-001",
    name: "James Harrington",
    specialization: "General Service & Maintenance",
    available: true,
  },
  {
    id: "ADV-002",
    name: "Sarah Chen",
    specialization: "Performance & M Series",
    available: true,
  },
  {
    id: "ADV-003",
    name: "Mike Torres",
    specialization: "Electrical & Diagnostics",
    available: true,
  },
];

// --- Service Catalog ---

export const SERVICE_CATALOG: ServiceInfo[] = [
  {
    service_type: "oil_change",
    display_name: "Oil Change",
    description:
      "Full synthetic oil and filter change using BMW-approved Castrol EDGE Professional.",
    estimated_duration_minutes: 45,
    price_range: { min: 89, max: 149, currency: "USD" },
    includes: [
      "Synthetic oil (up to 7 quarts)",
      "OEM oil filter replacement",
      "Multi-point visual inspection",
      "Fluid level top-up",
    ],
  },
  {
    service_type: "tire_rotation",
    display_name: "Tire Rotation",
    description:
      "Rotation of all four tires to ensure even wear, includes pressure check and tread depth measurement.",
    estimated_duration_minutes: 30,
    price_range: { min: 49, max: 79, currency: "USD" },
    includes: [
      "Tire rotation (pattern based on drivetrain)",
      "Tire pressure adjustment",
      "Tread depth measurement",
      "Visual tire condition report",
    ],
  },
  {
    service_type: "brake_inspection",
    display_name: "Brake Inspection",
    description:
      "Comprehensive brake system inspection including pads, rotors, fluid, and lines.",
    estimated_duration_minutes: 60,
    price_range: { min: 59, max: 99, currency: "USD" },
    includes: [
      "Brake pad thickness measurement",
      "Rotor condition inspection",
      "Brake fluid level and condition check",
      "Brake line visual inspection",
      "Written report with recommendations",
    ],
  },
  {
    service_type: "full_service",
    display_name: "Full Annual Service",
    description:
      "Comprehensive annual service per BMW maintenance schedule. Covers all major systems.",
    estimated_duration_minutes: 180,
    price_range: { min: 349, max: 599, currency: "USD" },
    includes: [
      "Synthetic oil and filter change",
      "Air filter replacement",
      "Cabin/micro filter replacement",
      "Brake inspection",
      "Tire rotation and pressure check",
      "All fluid levels checked and topped up",
      "Battery test",
      "Multi-point digital inspection with photos",
    ],
  },
  {
    service_type: "ac_check",
    display_name: "A/C System Check",
    description:
      "Air conditioning performance test and refrigerant level check.",
    estimated_duration_minutes: 45,
    price_range: { min: 79, max: 129, currency: "USD" },
    includes: [
      "A/C performance test",
      "Refrigerant pressure check",
      "Cabin temperature verification",
      "Visual inspection of A/C components",
    ],
  },
  {
    service_type: "battery_check",
    display_name: "Battery Check & Service",
    description:
      "Battery health test, terminal cleaning, and charging system verification.",
    estimated_duration_minutes: 30,
    price_range: { min: 39, max: 59, currency: "USD" },
    includes: [
      "Battery load test",
      "Terminal cleaning and treatment",
      "Charging system voltage test",
      "Written battery health report",
    ],
  },
  {
    service_type: "transmission_service",
    display_name: "Transmission Service",
    description:
      "Transmission fluid exchange and filter replacement (automatic transmissions).",
    estimated_duration_minutes: 120,
    price_range: { min: 249, max: 449, currency: "USD" },
    includes: [
      "Transmission fluid drain and fill",
      "Transmission filter replacement",
      "Pan gasket inspection/replacement",
      "Fluid level verification and test drive",
    ],
  },
  {
    service_type: "annual_mot",
    display_name: "Annual State Inspection",
    description:
      "Texas state vehicle safety and emissions inspection required annually.",
    estimated_duration_minutes: 30,
    price_range: { min: 25, max: 40, currency: "USD" },
    includes: [
      "Safety inspection (brakes, lights, signals, horn, mirrors)",
      "Emissions test (OBD-II scan)",
      "State inspection sticker (if passed)",
      "Written report of any failures",
    ],
  },
];

// --- Mock Availability ---

/** Dates that are fully booked (no availability). */
const FULLY_BOOKED_DATES = new Set([
  "2026-02-16",
  "2026-02-23",
  "2026-03-02",
]);

/**
 * Returns available time slots for a given date.
 * Weekdays have more availability; weekends have limited slots.
 * Specific dates are fully booked.
 */
export function getAvailableSlots(date: string): string[] {
  if (FULLY_BOOKED_DATES.has(date)) {
    return [];
  }

  const dayOfWeek = new Date(date + "T12:00:00").getDay();

  // Sunday (0) — closed
  if (dayOfWeek === 0) {
    return [];
  }

  // Saturday (6) — limited hours
  if (dayOfWeek === 6) {
    return ["09:00", "10:30"];
  }

  // Weekdays — full availability
  return ["09:00", "10:30", "13:00", "15:30"];
}

// --- Helper Functions ---

/**
 * Find a vehicle by license plate or VIN.
 */
export function findVehicle(
  licensePlate?: string,
  vin?: string
): Vehicle | null {
  return (
    MOCK_VEHICLES.find(
      (v) =>
        (licensePlate &&
          v.license_plate.toLowerCase() === licensePlate.toLowerCase()) ||
        (vin && v.vin.toLowerCase() === vin.toLowerCase())
    ) ?? null
  );
}

/**
 * Find a service in the catalog by service_type key.
 */
export function findService(serviceType: string): ServiceInfo | null {
  return (
    SERVICE_CATALOG.find(
      (s) => s.service_type.toLowerCase() === serviceType.toLowerCase()
    ) ?? null
  );
}

/**
 * Find a service advisor by ID. Falls back to the first available advisor.
 */
export function findAdvisor(advisorId?: string): ServiceAdvisor {
  if (advisorId) {
    const found = MOCK_ADVISORS.find((a) => a.id === advisorId);
    if (found) return found;
  }
  return MOCK_ADVISORS[0];
}

/**
 * Generate a fake booking ID.
 */
export function generateBookingId(): string {
  const num = Math.floor(1000 + Math.random() * 9000);
  return `BK-2026-${num}`;
}

/**
 * Generate a fake escalation ticket ID.
 */
export function generateTicketId(): string {
  const num = Math.floor(1000 + Math.random() * 9000);
  return `ESC-${num}`;
}
