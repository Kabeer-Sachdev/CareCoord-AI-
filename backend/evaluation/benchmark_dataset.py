BENCHMARK_QUESTIONS = [
    # Category 1: Direct Factual Questions
    {
        "id": "Q01",
        "category": "Direct Factual",
        "question": "What are the visiting hours for the Intensive Care Unit (ICU)?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["11:00 AM", "02:00 PM", "05:00 PM", "08:00 PM"],
        "is_answerable": True
    },
    {
        "id": "Q02",
        "category": "Direct Factual",
        "question": "By what time should scheduled patients vacate their beds on discharge day?",
        "expected_doc": "Patient_Discharge_Procedure.txt",
        "expected_answer_keywords": ["11:00 AM", "discharge"],
        "is_answerable": True
    },
    {
        "id": "Q03",
        "category": "Direct Factual",
        "question": "How much advance notice is required to cancel a general outpatient consultation?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["24 hours"],
        "is_answerable": True
    },
    {
        "id": "Q04",
        "category": "Direct Factual",
        "question": "How much advance notice is required to cancel specialized diagnostic procedures like MRI or CT scan?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["48 hours", "advance notice"],
        "is_answerable": True
    },
    {
        "id": "Q05",
        "category": "Direct Factual",
        "question": "What is the fee for a second missed appointment without prior notice?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["$25", "fee"],
        "is_answerable": True
    },
    {
        "id": "Q06",
        "category": "Direct Factual",
        "question": "What is the target turnaround time for cleaning a standard ward bed after patient discharge?",
        "expected_doc": "Bed_Allocation_Guidelines.txt",
        "expected_answer_keywords": ["45 minutes"],
        "is_answerable": True
    },
    {
        "id": "Q07",
        "category": "Direct Factual",
        "question": "What is the bed turnaround time for isolation and decontamination rooms including UV-C disinfection?",
        "expected_doc": "Bed_Allocation_Guidelines.txt",
        "expected_answer_keywords": ["75 minutes", "UV-C"],
        "is_answerable": True
    },
    {
        "id": "Q08",
        "category": "Direct Factual",
        "question": "What are the standard daily visiting hours for general medical and surgical wards?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["10:00 AM", "08:00 PM"],
        "is_answerable": True
    },
    {
        "id": "Q09",
        "category": "Direct Factual",
        "question": "What is the target evaluation time for an ESI Level 2 Emergent patient in the emergency department?",
        "expected_doc": "Emergency_Admission_Workflow.txt",
        "expected_answer_keywords": ["10 minutes"],
        "is_answerable": True
    },
    {
        "id": "Q10",
        "category": "Direct Factual",
        "question": "How many hours in advance must an elective admission be scheduled by the physician?",
        "expected_doc": "Patient_Admission_Policy.txt",
        "expected_answer_keywords": ["48 hours"],
        "is_answerable": True
    },

    # Category 2: Department-Specific Operational Procedures
    {
        "id": "Q11",
        "category": "Department Operational",
        "question": "What lab tests must be completed prior to elective admission and within what timeframe?",
        "expected_doc": "Patient_Admission_Policy.txt",
        "expected_answer_keywords": ["CBC", "BMP", "7 days"],
        "is_answerable": True
    },
    {
        "id": "Q12",
        "category": "Department Operational",
        "question": "What is the initial deposit percentage required for uninsured self-pay elective admissions?",
        "expected_doc": "Patient_Admission_Policy.txt",
        "expected_answer_keywords": ["30%"],
        "is_answerable": True
    },
    {
        "id": "Q13",
        "category": "Department Operational",
        "question": "What is the highest priority for bed assignment when inpatient capacity exceeds 85% occupancy?",
        "expected_doc": "Bed_Allocation_Guidelines.txt",
        "expected_answer_keywords": ["Priority 1", "Level 1/2", "Emergency Department"],
        "is_answerable": True
    },
    {
        "id": "Q14",
        "category": "Department Operational",
        "question": "Which infectious diseases mandate negative pressure airborne isolation rooms?",
        "expected_doc": "Bed_Allocation_Guidelines.txt",
        "expected_answer_keywords": ["Tuberculosis", "Measles", "Varicella"],
        "is_answerable": True
    },
    {
        "id": "Q15",
        "category": "Department Operational",
        "question": "How long can an emergency department hold a patient before documenting an admission decision?",
        "expected_doc": "Emergency_Admission_Workflow.txt",
        "expected_answer_keywords": ["4 hours"],
        "is_answerable": True
    },
    {
        "id": "Q16",
        "category": "Department Operational",
        "question": "What is the protocol for identifying unconscious unidentified trauma patients?",
        "expected_doc": "Emergency_Admission_Workflow.txt",
        "expected_answer_keywords": ["John/Jane Doe", "TRAUMA-M-01"],
        "is_answerable": True
    },
    {
        "id": "Q17",
        "category": "Department Operational",
        "question": "By what time must the attending physician sign the formal electronic discharge order?",
        "expected_doc": "Patient_Discharge_Procedure.txt",
        "expected_answer_keywords": ["09:00 AM"],
        "is_answerable": True
    },
    {
        "id": "Q18",
        "category": "Department Operational",
        "question": "Where do clinically cleared patients wait if their ride or medication is delayed past 11:00 AM?",
        "expected_doc": "Patient_Discharge_Procedure.txt",
        "expected_answer_keywords": ["Discharge Hospitality Lounge"],
        "is_answerable": True
    },
    {
        "id": "Q19",
        "category": "Department Operational",
        "question": "What are the overnight bedside rules for parents in the pediatric inpatient ward?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["24/7", "sleeper recliner"],
        "is_answerable": True
    },
    {
        "id": "Q20",
        "category": "Department Operational",
        "question": "How many simultaneous bedside visitors are permitted in general inpatient wards?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["two", "2 visitors"],
        "is_answerable": True
    },

    # Category 3: Rescheduling & Administrative Rules
    {
        "id": "Q21",
        "category": "Administrative Rules",
        "question": "How many times consecutively can a patient reschedule an appointment without administrative review?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["two", "2"],
        "is_answerable": True
    },
    {
        "id": "Q22",
        "category": "Administrative Rules",
        "question": "What happens if a patient accumulates 3 no-shows within a 12-month period?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["standby", "six months"],
        "is_answerable": True
    },
    {
        "id": "Q23",
        "category": "Administrative Rules",
        "question": "Within what timeframe must the hospital notify patients if a doctor cancels their clinic hours?",
        "expected_doc": "Appointment_Cancellation_Policy.txt",
        "expected_answer_keywords": ["2 hours"],
        "is_answerable": True
    },
    {
        "id": "Q24",
        "category": "Administrative Rules",
        "question": "What identification must visitors present to receive a security badge?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["photo identification", "Security Lobby Desk"],
        "is_answerable": True
    },
    {
        "id": "Q25",
        "category": "Administrative Rules",
        "question": "What happens if a visitor has experienced fever or cough within the past 48 hours?",
        "expected_doc": "Hospital_Visiting_Hours.txt",
        "expected_answer_keywords": ["prohibited", "entering"],
        "is_answerable": True
    },

    # Category 4: Unanswerable / Out-of-Domain Questions (Negative Tests)
    {
        "id": "Q26",
        "category": "Unanswerable / Out of Domain",
        "question": "What is the hospital's policy on personal pet dogs staying overnight in patient rooms?",
        "expected_doc": None,
        "expected_answer_keywords": ["sufficient information"],
        "is_answerable": False
    },
    {
        "id": "Q27",
        "category": "Unanswerable / Out of Domain",
        "question": "How much does employee parking cost per month on the hospital campus?",
        "expected_doc": None,
        "expected_answer_keywords": ["sufficient information"],
        "is_answerable": False
    },
    {
        "id": "Q28",
        "category": "Unanswerable / Out of Domain",
        "question": "What is the dose of intravenous vancomycin for acute bacterial endocarditis?",
        "expected_doc": None,
        "expected_answer_keywords": ["sufficient information"],
        "is_answerable": False
    },
    {
        "id": "Q29",
        "category": "Unanswerable / Out of Domain",
        "question": "What brand of coffee is served in the hospital doctors' lounge?",
        "expected_doc": None,
        "expected_answer_keywords": ["sufficient information"],
        "is_answerable": False
    },
    {
        "id": "Q30",
        "category": "Unanswerable / Out of Domain",
        "question": "Can patients smoke electronic cigarettes on hospital balconies?",
        "expected_doc": None,
        "expected_answer_keywords": ["sufficient information"],
        "is_answerable": False
    }
]
