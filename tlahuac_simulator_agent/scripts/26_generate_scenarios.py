#!/usr/bin/env python3
"""
Generate scenarios.json with 100 scenarios
"""

import json
from pathlib import Path

# Template starter openers by category pattern
STARTER_PATTERNS = {
    "booking": [
        "Hola, quiero agendar una cita",
        "Buen día, necesito programar servicio",
        "Quiero agendar cita para mantenimiento",
        "Necesito agendar una cita",
        "Buenas, quiero programar servicio",
        "Hola, puedo agendar una cita?",
        "Quiero agendar para servicio",
        "Necesito cita para mi auto",
        "Buen día, quiero agendar",
        "Hola, necesito agendar cita de servicio",
        "Quiero agendar mantenimiento",
        "Necesito programar una cita",
        "Puedo agendar una cita?",
        "Quiero agendar servicio",
        "Necesito agendar",
        "Buen día, quiero agendar cita",
        "Hola, necesito cita",
        "Quiero programar una cita",
        "Necesito agendar para mantenimiento",
        "Puedo programar una cita?"
    ],
    "status": [
        "Hola, ya está listo?",
        "Buen día, cuándo estará listo?",
        "Ya quedó mi auto?",
        "Para cuándo estará?",
        "Cuándo puedo pasar?",
        "Ya está listo mi vehículo?",
        "Sigue en taller?",
        "Cuándo estará listo?",
        "Ya terminaron?",
        "Para cuándo estará listo?",
        "Hola, cuándo estará?",
        "Ya está listo?",
        "Cuándo puedo recoger?",
        "Sigue en servicio?",
        "Ya está?",
        "Para cuándo?",
        "Cuándo estará?",
        "Ya quedó?",
        "Está listo?",
        "Cuándo puedo pasar por mi auto?"
    ],
    "warranty": [
        "Hola, tengo una pregunta sobre la garantía",
        "Mi auto está en garantía?",
        "Esto cubre la garantía?",
        "Tengo garantía?",
        "Está cubierto por garantía?",
        "La garantía cubre esto?",
        "Tengo garantía todavía?",
        "Está en garantía?",
        "Cubre la garantía?",
        "Tengo una duda sobre garantía",
        "Mi garantía cubre esto?",
        "Está en garantía mi auto?",
        "Tengo garantía?",
        "La garantía aplica?",
        "Está cubierto?",
        "Tengo garantía activa?",
        "Cubre garantía?",
        "Está en garantía?",
        "Tengo garantía?",
        "La garantía cubre?"
    ],
    "pricing": [
        "Cuánto cuesta?",
        "Cuánto sale?",
        "Cuál es el precio?",
        "Cuánto cuesta el servicio?",
        "Cuánto sale el mantenimiento?",
        "Cuál es el costo?",
        "Cuánto cuesta aproximadamente?",
        "Cuánto sale más o menos?",
        "Cuál es el precio del servicio?",
        "Cuánto cuesta?",
        "Cuánto sale?",
        "Cuál es el precio?",
        "Cuánto cuesta el servicio?",
        "Cuánto sale?",
        "Cuál es el costo?",
        "Cuánto cuesta aproximadamente?",
        "Cuánto sale más o menos?",
        "Cuál es el precio?",
        "Cuánto cuesta?",
        "Cuánto sale?"
    ],
    "diagnostic": [
        "Hola, mi auto está haciendo un ruido",
        "Mi carro tiene un problema",
        "Mi auto no está funcionando bien",
        "Tengo un problema con mi auto",
        "Mi carro está fallando",
        "Mi auto tiene un ruido raro",
        "Mi carro no arranca bien",
        "Mi auto tiene un problema",
        "Tengo un ruido en mi auto",
        "Mi carro está haciendo algo raro",
        "Mi auto no funciona bien",
        "Tengo un problema",
        "Mi carro tiene un ruido",
        "Mi auto está fallando",
        "Tengo un problema con el auto",
        "Mi carro no está bien",
        "Mi auto tiene un ruido extraño",
        "Mi carro está haciendo ruido",
        "Tengo un problema",
        "Mi auto no está funcionando"
    ],
    "parts": [
        "Tienen la refacción?",
        "Tienen disponible la pieza?",
        "Cuándo llega la refacción?",
        "Tienen la pieza?",
        "Está disponible la refacción?",
        "Cuándo llega?",
        "Tienen la refacción disponible?",
        "Cuándo llega la pieza?",
        "Tienen la refacción?",
        "Está disponible?",
        "Cuándo llega la refacción?",
        "Tienen la pieza disponible?",
        "Cuándo llega?",
        "Tienen la refacción?",
        "Está disponible la pieza?",
        "Cuándo llega la refacción?",
        "Tienen disponible?",
        "Cuándo llega?",
        "Tienen la refacción?",
        "Está disponible?"
    ]
}

# Common slots by category
SLOTS_BY_CATEGORY = {
    "booking/rescheduling/cancel": {
        "required": ["service_type"],
        "optional": ["car_model", "year", "km", "preferred_date", "time_preference", "reason"]
    },
    "status updates & chasing": {
        "required": [],
        "optional": ["service_date", "promised_time", "current_status"]
    },
    "warranty & policy confusion": {
        "required": ["warranty_question_type"],
        "optional": ["purchase_date", "mileage", "issue_description"]
    },
    "pricing/payment/invoice disputes": {
        "required": ["service_type"],
        "optional": ["car_model", "year", "previous_quote", "payment_method"]
    },
    "diagnostics & my car is doing X": {
        "required": ["symptom_description"],
        "optional": ["car_model", "year", "km", "when_started", "frequency"]
    },
    "parts & logistics & docs": {
        "required": ["part_name"],
        "optional": ["car_model", "year", "urgency", "delivery_address"]
    }
}

# Common strategies by category
STRATEGIES_BY_CATEGORY = {
    "booking/rescheduling/cancel": ["clarify_question", "add_details", "reduce_request", "provide_constraint"],
    "status updates & chasing": ["ask_status", "complain_escalate", "change_channel"],
    "warranty & policy confusion": ["ask_clarification", "add_details", "complain_escalate"],
    "pricing/payment/invoice disputes": ["clarify_question", "reduce_request", "compare_elsewhere"],
    "diagnostics & my car is doing X": ["add_details", "clarify_question", "provide_constraint"],
    "parts & logistics & docs": ["ask_clarification", "add_details", "change_channel"]
}

# Success and failure endings
SUCCESS_ENDINGS = [
    "Perfecto, gracias",
    "Listo, nos vemos entonces",
    "Excelente, gracias",
    "Perfecto, hasta entonces",
    "Ok, gracias",
    "Perfecto",
    "Listo, gracias",
    "Ok",
    "Gracias",
    "Perfecto, hasta luego"
]

FAILURE_ENDINGS = [
    "Ok gracias",
    "Bueno, luego les marco",
    "Ok, luego veo",
    "Gracias",
    "Ok",
    "Bueno",
    "Luego les marco",
    "Ok, gracias",
    "Bueno, gracias",
    "Ok, luego"
]

def get_category_for_scenario(scenario_id):
    """Determine category from scenario ID."""
    if "booking" in scenario_id or "rescheduling" in scenario_id or "cancel" in scenario_id:
        return "booking/rescheduling/cancel"
    elif "status" in scenario_id or "chase" in scenario_id:
        return "status updates & chasing"
    elif "warranty" in scenario_id or "policy" in scenario_id:
        return "warranty & policy confusion"
    elif "price" in scenario_id or "payment" in scenario_id or "invoice" in scenario_id:
        return "pricing/payment/invoice disputes"
    elif "diagnostic" in scenario_id:
        return "diagnostics & my car is doing X"
    elif "parts" in scenario_id or "logistics" in scenario_id or "docs" in scenario_id:
        return "parts & logistics & docs"
    return "booking/rescheduling/cancel"

def get_starter_pattern(category):
    """Get starter pattern for category."""
    if "booking" in category:
        return "booking"
    elif "status" in category:
        return "status"
    elif "warranty" in category:
        return "warranty"
    elif "pricing" in category or "payment" in category:
        return "pricing"
    elif "diagnostic" in category:
        return "diagnostic"
    elif "parts" in category:
        return "parts"
    return "booking"

def create_scenario(scenario_id, description, category):
    """Create a scenario entry."""
    starter_pattern = get_starter_pattern(category)
    starters = STARTER_PATTERNS.get(starter_pattern, STARTER_PATTERNS["booking"])
    
    slots = SLOTS_BY_CATEGORY.get(category, {"required": [], "optional": []})
    strategies = STRATEGIES_BY_CATEGORY.get(category, ["clarify_question", "add_details"])
    
    return {
        "scenario_id": scenario_id,
        "category": category,
        "description": description,
        "starter_openers": starters[:20],  # Use first 20
        "required_slots": slots["required"],
        "optional_slots": slots["optional"],
        "common_customer_strategies": strategies,
        "success_endings": SUCCESS_ENDINGS[:5],
        "failure_endings": FAILURE_ENDINGS[:5]
    }

def main():
    """Generate scenarios.json."""
    scenarios = {}
    
    # Define all scenarios
    all_scenarios = [
        # Booking (15)
        ("booking_service_appointment", "Customer requesting service appointment"),
        ("rescheduling_appointment", "Customer needs to reschedule existing appointment"),
        ("cancel_appointment", "Customer wants to cancel appointment"),
        ("urgent_same_day_booking", "Customer needs same-day urgent service"),
        ("booking_with_constraints", "Customer booking with time/location constraints"),
        ("booking_multiple_services", "Customer booking multiple services at once"),
        ("booking_with_discount_request", "Customer booking while asking for discount"),
        ("booking_after_hours", "Customer trying to book outside business hours"),
        ("booking_weekend_only", "Customer only available on weekends"),
        ("booking_early_morning", "Customer requesting early morning appointment"),
        ("rescheduling_due_conflict", "Customer rescheduling due to schedule conflict"),
        ("rescheduling_due_emergency", "Customer rescheduling due to emergency"),
        ("cancel_due_emergency", "Customer canceling due to emergency"),
        ("cancel_due_price", "Customer canceling due to price concerns"),
        ("cancel_due_delay", "Customer canceling due to previous delays"),
        
        # Status (15)
        ("status_update_general", "General status check"),
        ("status_update_urgent", "Urgent status check"),
        ("status_chase_delayed", "Following up on delayed service"),
        ("status_chase_no_update", "Asking for update when none provided"),
        ("status_chase_promised_time", "Following up on promised completion time"),
        ("status_update_multiple_checks", "Multiple status checks in conversation"),
        ("status_update_after_promise", "Status check after promise was made"),
        ("status_chase_escalation", "Status check with escalation threat"),
        ("status_update_pickup_ready", "Checking if ready for pickup"),
        ("status_update_in_progress", "Asking about current progress"),
        ("status_update_waiting_parts", "Status check while waiting for parts"),
        ("status_update_diagnosis_complete", "Checking if diagnosis is complete"),
        ("status_update_quality_check", "Checking quality inspection status"),
        ("status_update_final_inspection", "Checking final inspection status"),
        ("status_chase_frustrated", "Frustrated status follow-up"),
        
        # Warranty (15)
        ("warranty_claim_general", "General warranty claim"),
        ("warranty_coverage_question", "Question about warranty coverage"),
        ("warranty_denied_appeal", "Appealing denied warranty claim"),
        ("warranty_expired_question", "Question about expired warranty"),
        ("warranty_transfer_question", "Question about warranty transfer"),
        ("warranty_documentation_needed", "Warranty claim needing documentation"),
        ("warranty_part_not_covered", "Part not covered by warranty"),
        ("warranty_labor_not_covered", "Labor not covered by warranty"),
        ("warranty_misunderstanding", "Customer misunderstanding warranty terms"),
        ("warranty_third_party_question", "Question about third-party warranty"),
        ("policy_refund_question", "Question about refund policy"),
        ("policy_cancellation_fee", "Question about cancellation fees"),
        ("policy_rescheduling_fee", "Question about rescheduling fees"),
        ("policy_warranty_extension", "Question about warranty extension"),
        ("policy_service_guarantee", "Question about service guarantee"),
        
        # Pricing (15)
        ("price_quote_general", "General price quote request"),
        ("price_quote_breakdown", "Requesting detailed price breakdown"),
        ("price_quote_discount_request", "Asking for discount"),
        ("price_quote_comparison", "Comparing prices with other shops"),
        ("price_quote_package_options", "Asking about package pricing"),
        ("price_dispute_higher_than_quoted", "Price higher than quoted"),
        ("price_dispute_unexpected_charges", "Unexpected charges on invoice"),
        ("price_dispute_labor_cost", "Disputing labor cost"),
        ("price_dispute_part_cost", "Disputing part cost"),
        ("payment_methods_question", "Question about payment methods"),
        ("payment_installment_request", "Requesting payment installments"),
        ("invoice_error_correction", "Invoice error needs correction"),
        ("invoice_missing_item", "Missing item on invoice"),
        ("invoice_tax_question", "Question about tax on invoice"),
        ("invoice_payment_confirmation", "Confirming payment received"),
        
        # Diagnostics (25)
        ("diagnostic_noise_issue", "Car making strange noise"),
        ("diagnostic_engine_light", "Engine light is on"),
        ("diagnostic_starting_problem", "Car not starting"),
        ("diagnostic_brake_issue", "Brake problem"),
        ("diagnostic_transmission_issue", "Transmission problem"),
        ("diagnostic_electrical_issue", "Electrical problem"),
        ("diagnostic_ac_heating_issue", "AC/heating not working"),
        ("diagnostic_suspension_issue", "Suspension problem"),
        ("diagnostic_fuel_economy", "Poor fuel economy"),
        ("diagnostic_smell_issue", "Strange smell"),
        ("diagnostic_vibration_issue", "Car vibrating"),
        ("diagnostic_overheating", "Car overheating"),
        ("diagnostic_battery_issue", "Battery problem"),
        ("diagnostic_tire_issue", "Tire problem"),
        ("diagnostic_fluid_leak", "Fluid leak"),
        ("diagnostic_warning_lights", "Warning lights on dashboard"),
        ("diagnostic_strange_sound", "Strange sound"),
        ("diagnostic_performance_issue", "Performance issue"),
        ("diagnostic_safety_concern", "Safety concern"),
        ("diagnostic_urgent_breakdown", "Urgent breakdown"),
        ("diagnostic_second_opinion", "Seeking second opinion"),
        ("diagnostic_previous_repair_issue", "Previous repair issue"),
        ("diagnostic_warranty_related", "Diagnostic related to warranty"),
        ("diagnostic_maintenance_reminder", "Maintenance reminder question"),
        ("diagnostic_general_checkup", "General checkup request"),
        
        # Parts (15)
        ("parts_availability_question", "Question about parts availability"),
        ("parts_ordering_request", "Requesting to order parts"),
        ("parts_price_quote", "Asking for parts price"),
        ("parts_aftermarket_vs_oem", "Question about aftermarket vs OEM"),
        ("parts_delivery_time", "Question about parts delivery time"),
        ("parts_installation_question", "Question about parts installation"),
        ("logistics_pickup_arrangement", "Arranging vehicle pickup"),
        ("logistics_delivery_request", "Requesting delivery service"),
        ("logistics_dropoff_time", "Question about dropoff time"),
        ("logistics_loaner_vehicle", "Requesting loaner vehicle"),
        ("logistics_shuttle_service", "Question about shuttle service"),
        ("docs_invoice_request", "Requesting invoice"),
        ("docs_warranty_certificate", "Requesting warranty certificate"),
        ("docs_service_history", "Requesting service history"),
        ("docs_insurance_claim_docs", "Requesting insurance claim documents")
    ]
    
    for scenario_id, description in all_scenarios:
        category = get_category_for_scenario(scenario_id)
        scenarios[scenario_id] = create_scenario(scenario_id, description, category)
    
    # Write to file
    output_file = Path(__file__).parent.parent / "scenarios.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"scenarios": scenarios}, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(scenarios)} scenarios in {output_file}")

if __name__ == "__main__":
    main()
