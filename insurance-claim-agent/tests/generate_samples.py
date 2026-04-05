"""
Generate realistic sample policy and hospital bill PDFs for testing.

Generates:
  - 1 detailed multi-page health insurance policy (12 pages)
  - 7 hospital bill PDFs covering every rule scenario

Usage:
    cd insurance-claim-agent
    python -m tests.generate_samples
"""

import os
import fitz  # PyMuPDF

SAMPLE_DIR = os.path.join("app", "storage", "samples")

# ---------------------------------------------------------------------------
# POLICY DOCUMENT — 12 pages, realistic Indian health insurance
# ---------------------------------------------------------------------------

POLICY_TEXT_PAGES = [
    # Page 1 — Cover
    """
                STAR HEALTH INSURANCE COMPANY LIMITED
              ─────────────────────────────────────────
                 COMPREHENSIVE HEALTH INSURANCE POLICY
                         (Individual Plan)

    ╔═══════════════════════════════════════════════════════════════╗
    ║  Policy Number      :  SHI/IND/2025/0056781                 ║
    ║  Policyholder Name  :  Mr. Rahul Sharma                     ║
    ║  Date of Birth      :  15-March-1990   (Age: 35 years)      ║
    ║  Gender             :  Male                                  ║
    ║  Address            :  42, MG Road, Indiranagar,            ║
    ║                        Bengaluru, Karnataka - 560038         ║
    ║  Sum Insured        :  Rs. 5,00,000 (Five Lakhs Only)       ║
    ║  Policy Period      :  01-Jan-2025 to 31-Dec-2025           ║
    ║  Date of Issue      :  28-Dec-2024                          ║
    ║  First Policy Date  :  01-Jan-2024 (Continuous)             ║
    ║  Premium Paid       :  Rs. 12,500 (inclusive of GST)        ║
    ║  Nominee            :  Mrs. Anita Sharma (Wife)             ║
    ╚═══════════════════════════════════════════════════════════════╝

    This document constitutes the complete terms and conditions of the
    health insurance contract between the Policyholder and Star Health
    Insurance Company Limited ("the Company").
    """,

    # Page 2 — Table of Contents
    """
    TABLE OF CONTENTS
    =================

    Section 1  : Definitions ................................. Page 3
    Section 2  : Scope of Coverage ........................... Page 4
    Section 3  : In-Patient Hospitalization ................... Page 5
    Section 4  : Sub-Limits and Caps .......................... Page 6
    Section 5  : Waiting Periods .............................. Page 7
    Section 6  : General Exclusions ........................... Page 8
    Section 7  : Pre-Existing Disease Clause .................. Page 9
    Section 8  : Co-Payment and Deductible .................... Page 10
    Section 9  : Daycare Procedures ........................... Page 10
    Section 10 : Claim Procedure .............................. Page 11
    Section 11 : Non-Medical Items ............................ Page 11
    Section 12 : General Conditions ........................... Page 12
    """,

    # Page 3 — Definitions
    """
    SECTION 1: DEFINITIONS

    1.1 "Accident" means a sudden, unforeseen and involuntary event caused
        by external, visible and violent means.

    1.2 "Cashless Facility" means a facility extended by the Company where
        the payments of the costs of treatment undergone by the Insured
        Person are directly made to the Network Hospital by the Company.

    1.3 "Condition Precedent" means a policy term or condition upon which
        the Company's liability under the policy is conditional.

    1.4 "Daycare Treatment" means treatment or procedure that is undertaken
        under general or local anesthesia in a hospital/daycare centre in
        less than 24 hours because of technological advancement and which
        would have otherwise required hospitalization of more than 24 hours.

    1.5 "Hospital" means any institution established for in-patient care
        and day care treatment of illness and/or injuries that has been
        registered as a hospital with the local authorities and has at
        least 15 in-patient beds, qualified nursing staff under 24-hour
        supervision of a Medical Practitioner (relaxed for daycare centres).

    1.6 "Hospitalization" means admission in a Hospital for a minimum
        period of 24 consecutive hours except for specified Daycare
        Treatments.

    1.7 "Medical Practitioner" means a person who holds a valid registration
        from the Medical Council of India (MCI) or State Medical Council.

    1.8 "Network Hospital" means a hospital which has been empanelled by
        the Company / TPA to provide cashless treatment to policyholders.

    1.9 "Pre-Existing Disease" means any condition, ailment, injury or
        disease that is diagnosed or for which medical advice or treatment
        was recommended by, or received from, a Medical Practitioner prior
        to the inception of the first insurance policy with the Company.

    1.10 "Reasonable and Customary Charges" means charges for treatment
         which are consistent with the prevailing charges in the geographical
         area for identical or similar treatment.
    """,

    # Page 4 — Scope of Coverage
    """
    SECTION 2: SCOPE OF COVERAGE

    2.1 The Company shall indemnify the Policyholder against the
        following medical expenses incurred during the Policy Period:

        a) In-Patient Hospitalization expenses
        b) Pre-Hospitalization expenses (up to 30 days prior)
        c) Post-Hospitalization expenses (up to 60 days after discharge)
        d) Daycare Treatment expenses
        e) Ambulance charges up to Rs. 2,000 per hospitalization
        f) Organ Donor expenses

    2.2 The total liability shall not exceed the Sum Insured during
        the Policy Period. Coverage is on indemnity basis; the Company
        shall pay the actual expenses incurred, subject to policy terms.

    2.3 Emergency hospitalization at a Non-Network Hospital is covered;
        however, the claim shall be processed on reimbursement basis.

    2.4 The coverage extends anywhere within India. Overseas treatment
        is excluded unless specifically endorsed.
    """,

    # Page 5 — In-Patient Hospitalization
    """
    SECTION 3: IN-PATIENT HOSPITALIZATION COVERAGE

    3.1 Eligibility for In-Patient Claim
        The Insured Person must be hospitalized for a minimum period of
        24 consecutive hours. Hospitalization of less than 24 hours of
        duration is not covered except for specified Daycare Procedures
        listed in Annexure-A or if the patient dies within 24 hours of
        admission.

    3.2 Covered Expenses
        The following expenses during hospitalization are covered:
        - Room, Boarding and Nursing charges
        - Surgeon, Anesthetist, Medical Practitioner, Specialist fees
        - Anesthesia, blood, oxygen, Operation Theatre (OT) charges
        - Cost of medicines, drugs, consumables, and implants
        - Cost of diagnostic tests and imaging (X-Ray, MRI, CT Scan,
          Ultrasound, blood and urine tests, etc.)
        - ICU / ICCU charges
        - Physiotherapy during hospitalization
        - Cost of prosthetic devices if implanted internally

    3.3 The Company reserves the right to verify the medical necessity
        of hospitalization through its Medical Board. If hospitalization
        is deemed medically unnecessary, the claim may be denied.
    """,

    # Page 6 — Sub-Limits
    """
    SECTION 4: SUB-LIMITS AND CAPS

    4.1 Room Rent Limit
        Room Rent (including boarding and nursing expenses) is limited
        to a maximum of 1% of the Sum Insured per day.

        For Sum Insured of Rs. 5,00,000:
          Maximum Room Rent = Rs. 5,000 per day

        If the actual room rent exceeds the allowable limit, all other
        payable claim items shall be proportionately reduced in the
        same proportion.

    4.2 ICU / ICCU Charges
        ICU / ICCU charges are limited to 2% of the Sum Insured per day.
        For Sum Insured of Rs. 5,00,000:
          Maximum ICU charges = Rs. 10,000 per day

    4.3 Ambulance Charges
        Maximum Rs. 2,000 per hospitalization event.

    4.4 Cataract Surgery
        Limited to Rs. 40,000 per eye, subject to overall waiting period.

    4.5 The proportionate reduction (Clause 4.1) shall be calculated as:
        Admissible Room Rent ÷ Actual Room Rent × Claimed Amount
    """,

    # Page 7 — Waiting Periods
    """
    SECTION 5: WAITING PERIODS

    5.1 Initial Waiting Period (Cooling Period)
        No claims shall be admissible during the first 30 days of
        the first policy period, except claims arising out of an
        Accident. This is a one-time waiting period and shall not
        apply on renewals.

    5.2 Specific Disease Waiting Period
        The following diseases / treatments shall be covered only
        after a continuous waiting period of 24 months (2 years)
        from the date of the first policy:

        - Cataract
        - Benign Ear, Nose and Throat (ENT) disorders
        - Hernia of all types
        - Hydrocele
        - Fistula in anus / Piles / Sinuses
        - Kidney Stones / Gallbladder Stones (Urolithiasis/Cholelithiasis)
        - Joint Replacement Surgery
        - Surgery on internal congenital anomalies
        - Hysterectomy for menorrhagia or fibromyoma
        - Benign prostatic hypertrophy
        - Tonsillectomy / Adenoidectomy
        - Surgery for prolapsed intervertebral disc

    5.3 Maternity Waiting Period
        Maternity benefits, if applicable, are available only after
        a continuous coverage of 36 months (3 years).
    """,

    # Page 8 — General Exclusions
    """
    SECTION 6: GENERAL EXCLUSIONS

    The Company shall not be liable to make any payment under this
    policy in respect of any expense incurred in connection with:

    6.1  Cosmetic or plastic surgery, unless necessitated by an Accident
         or medically necessary reconstruction after cancer surgery.

    6.2  Dental treatment or surgery unless requiring hospitalization
         and involving maxillo-facial surgery due to Accident.

    6.3  Treatment for correction of eyesight (spectacles, contact
         lenses, LASIK, or any refractive error correction).

    6.4  Fertility treatment, assisted reproduction technologies like
         IVF, ICSI, IUI, surrogacy or any related procedure.

    6.5  Obesity / Weight management treatment including but not limited
         to bariatric surgery, liposuction, abdominoplasty.

    6.6  Treatment arising from or traceable to pregnancy, childbirth,
         caesarean section, miscarriage (except ectopic pregnancy).

    6.7  Experimental, investigational or unproven treatment or devices.

    6.8  Treatments received in health hydros, nature cure clinics, spas,
         or similar establishments, including Ayurvedic, Unani, Siddha,
         or Homeopathic treatments unless in Government hospital.

    6.9  Intentional self-injury, suicide attempt, or substance abuse.

    6.10 STDs and related illnesses including HIV/AIDS management.

    6.11 War, terrorism, nuclear contamination, or radioactive exposure.

    6.12 Vaccination, inoculation, or change of life management.
    """,

    # Page 9 — Pre-Existing Disease
    """
    SECTION 7: PRE-EXISTING DISEASE CLAUSE

    7.1 Any Pre-Existing Disease shall stand excluded for a period
        of 48 months (4 years) from the date of inception of the
        first policy with the Company, provided the policy has been
        continuously renewed without a break.

    7.2 Pre-Existing Diseases commonly include but are not limited to:
        - Diabetes Mellitus (Type 1 and Type 2)
        - Hypertension (High Blood Pressure)
        - Heart Disease (Coronary Artery Disease, Valve disorders)
        - Chronic Kidney Disease / Renal Failure
        - Asthma / Chronic Obstructive Pulmonary Disease (COPD)
        - Thyroid Disorders (Hypothyroidism, Hyperthyroidism)
        - Epilepsy
        - Arthritis (Rheumatoid or Osteoarthritis)
        - Cancer (if diagnosed prior to first policy)
        - Liver Cirrhosis or Hepatitis B/C
        - Stroke or Cerebrovascular Disease
        - Any condition for which treatment was taken before first policy

    7.3 After completion of 48 continuous months, pre-existing diseases
        shall be covered like any other illness under this policy.

    7.4 If the insured has obtained a policy through misrepresentation
        or non-disclosure of pre-existing conditions, the Company
        reserves the right to cancel the policy and forfeit the premium.
    """,

    # Page 10 — Co-Pay and Daycare
    """
    SECTION 8: CO-PAYMENT AND DEDUCTIBLE

    8.1 Co-Payment Clause
        - For policyholders aged below 60 years: No co-payment applicable.
        - For policyholders aged 60 to 75 years: 10% co-payment.
        - For policyholders aged above 75 years: 20% co-payment.

        The co-payment is calculated on the admissible claim amount
        (after applying sub-limits and exclusions).

    8.2 Voluntary Deductible
        If the policyholder has opted for a voluntary deductible at the
        time of policy purchase, the corresponding deductible amount
        shall be subtracted from the admissible claim amount.

    ─────────────────────────────────────────────────────────────────

    SECTION 9: DAYCARE PROCEDURES

    9.1 The following daycare procedures are covered even if
        hospitalization is less than 24 hours:
        - Dialysis
        - Chemotherapy / Radiotherapy
        - Eye surgeries (Cataract, Glaucoma)
        - Lithotripsy (ESWL)
        - Tonsillectomy / Adenoidectomy
        - D&C (Dilation and Curettage)
        - Coronary Angiography / Angioplasty
        - Endoscopic procedures (Sclerotherapy, ERCP, Colonoscopy)
        - Oral surgery requiring general anesthesia
        - Fracture reduction and cast application
        - Arthroscopy and joint aspiration

    9.2 The list of daycare procedures is indicative and not exhaustive.
        Any procedure that satisfies the definition of Daycare Treatment
        under Section 1.4 shall be considered for coverage.
    """,

    # Page 11 — Claim Procedure and Non-Medical Items
    """
    SECTION 10: CLAIM PROCEDURE

    10.1 Cashless Claims
         For treatment at a Network Hospital, the insured must present
         the Health Card or Policy Details. Pre-authorization shall be
         obtained before planned hospitalization (at least 48 hours
         before admission) or within 24 hours for emergency admission.

    10.2 Reimbursement Claims
         Claims must be submitted within 30 days of discharge along
         with the following documents:
         a) Duly filled Claim Form
         b) Original hospital discharge summary
         c) Original hospital bills and receipts
         d) Prescription and diagnostic test reports
         e) FIR copy (in case of accident/medico-legal cases)
         f) Photo ID proof of the insured

    10.3 Incomplete documentation may lead to delay or rejection of
         the claim. The Company shall communicate any deficiency
         within 15 days of receiving the documents.

    ─────────────────────────────────────────────────────────────────

    SECTION 11: NON-MEDICAL ITEMS (NOT PAYABLE)

    11.1 The following non-medical items/expenses are NOT payable:
         - Toiletries (soap, toothpaste, comb, tissue paper)
         - Personal comfort items (TV rental, telephone charges,
           extra bed for attendant, mineral water, guest meals)
         - Administrative charges (admission kit, documentation charges,
           registration charges, service charges)
         - Cosmetic items (gown, slippers, cap)
         - Food charges (except patient diet as prescribed)
         - Charges for items not related to the diagnosed condition
    """,

    # Page 12 — General Conditions
    """
    SECTION 12: GENERAL CONDITIONS

    12.1 Disclosure
         The Policyholder is required to disclose all material facts
         at the time of proposal. Non-disclosure or misrepresentation
         of material facts may result in the policy being void.

    12.2 Renewal
         This policy can be renewed within 30 days of expiry (grace
         period). Continuity benefits (including waiting period credits)
         shall lapse if the policy is not renewed within the grace period.

    12.3 Cancellation
         Either party may cancel the policy by giving 15 days written
         notice. Refund on cancellation shall be on short-period scale.

    12.4 Arbitration
         Any dispute arising from this policy shall be referred to a
         sole arbitrator under the Arbitration and Conciliation Act,
         1996. The seat of arbitration shall be Bengaluru.

    12.5 Grievance Redressal
         Policyholder may contact:
         - Customer Service: 1800-XXX-XXXX (Toll Free)
         - Email: claims@starhealthinsurance.in
         - IRDAI Grievance Cell: igms.irda.gov.in

    12.6 This policy is governed by and construed in accordance with
         the laws of India.


    ─────────────────────────────────────────────────────────────────
    Authorized Signatory
    Star Health Insurance Company Limited
    Regd. Office: No. 1, New Tank Street, Chennai - 600001
    """,
]

# ---------------------------------------------------------------------------
# HOSPITAL BILLS — 7 scenarios covering all 10 rules
# ---------------------------------------------------------------------------

BILL_CASES = {
    # 1. APPROVED — Clean case, everything within limits
    "bill_01_approved_clean.txt": {
        "description": "APPROVED — Appendectomy, all within policy limits",
        "text": """
            ══════════════════════════════════════════════════════════
                          CITY CARE MULTI-SPECIALITY HOSPITAL
                  #128, 100 Feet Road, Indiranagar, Bengaluru - 560038
                  NABH Accredited | Reg No: KA/BLR/2019/HC-3421
            ══════════════════════════════════════════════════════════

            FINAL HOSPITAL BILL / DISCHARGE SUMMARY

            Patient Name       : Mr. Rahul Sharma
            UHID               : CCH-2025-089341
            Age / Gender       : 35 years / Male
            Contact            : +91 98765 43210

            Date of Admission  : 15-Jun-2025, 09:30 AM
            Date of Discharge  : 18-Jun-2025, 11:00 AM
            Duration of Stay   : 3 days

            Treating Doctor    : Dr. Vinay Kulkarni, MS (General Surgery)
            Department         : General Surgery

            Diagnosis (ICD-10) : K35.80 — Acute Appendicitis, unspecified
            Procedure (ICD-10) : 0DTJ4ZZ — Laparoscopic Appendectomy

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            Room Charges - Deluxe (3 days × Rs.4,000)    12,000
            Surgeon Fee                                   25,000
            Anaesthesia Charges                            8,000
            Operation Theatre Charges                     10,000
            Medicines & Consumables                        5,500
            Diagnostic Tests (CBC, LFT, USG Abdomen)       3,200
            Nursing Charges                                2,000
            Consultation Fee (Pre & Post Operative)        2,000
            ──────────────────────────────────────────────────────
            Sub-Total                                     67,700
            Less: Discount                                -2,700
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                        Rs. 65,000
            ══════════════════════════════════════════════════════

            Payment Mode: To be settled via Insurance (Cashless)
            TPA Ref: TPA/CL/2025/456789

            The patient was hemodynamically stable at discharge.
            Follow-up after 7 days with Dr. Vinay Kulkarni.

            Authorized Signatory                Billing Department
            City Care Hospital                  Ph: 080-2345-6789
        """,
    },

    # 2. REJECTED — Cosmetic surgery exclusion
    "bill_02_rejected_cosmetic.txt": {
        "description": "REJECTED — Cosmetic rhinoplasty, excluded under Section 6.1",
        "text": """
            ══════════════════════════════════════════════════════════
                     GLAMOUR AESTHETICS & COSMETIC SURGERY CENTRE
                    #45, Brigade Road, Bengaluru, Karnataka - 560001
                    Reg No: KA/BLR/2021/CS-0891
            ══════════════════════════════════════════════════════════

            FINAL HOSPITAL BILL

            Patient Name       : Ms. Priya Mehta
            Age / Gender       : 28 years / Female
            UHID               : GAC-2025-10234

            Date of Admission  : 10-Mar-2025, 08:00 AM
            Date of Discharge  : 11-Mar-2025, 06:00 PM
            Duration of Stay   : 1 day

            Treating Doctor    : Dr. Kavitha Rao, MCh (Plastic Surgery)
            Department         : Cosmetic & Plastic Surgery

            Diagnosis          : Deviated Nasal Septum (cosmetic concern)
            Procedure          : Cosmetic Rhinoplasty (Nose reshaping)

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            Room Charges - Suite (1 day × Rs.8,000)       8,000
            Plastic Surgeon Fee                          55,000
            Anaesthesia Charges                          15,000
            Operation Theatre Charges                    20,000
            Medicines & Consumables                       4,500
            Nasal Splint & Dressing Material               1,500
            Post-Operative Care                           2,000
            ──────────────────────────────────────────────────────
            Sub-Total                                   1,06,000
            Less: Discount                               -12,000
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                        Rs. 94,000
            ══════════════════════════════════════════════════════

            NOTE: This is a cosmetic/elective procedure.
        """,
    },

    # 3. PARTIAL — Room rent exceeds policy cap
    "bill_03_partial_room_rent.txt": {
        "description": "PARTIAL — Room rent Rs.8,000/day exceeds cap of Rs.5,000/day",
        "text": """
            ══════════════════════════════════════════════════════════
                     SUPREME HOSPITAL & RESEARCH CENTRE
               #67, Outer Ring Road, Marathahalli, Bengaluru - 560037
               NABH Accredited | ISO 9001:2015 | Reg: KA/BLR/2018/SH-112
            ══════════════════════════════════════════════════════════

            FINAL HOSPITAL BILL / TAX INVOICE

            Patient Name       : Mr. Anil Kumar
            UHID               : SUP-2025-55678
            Age / Gender       : 42 years / Male

            Date of Admission  : 20-Aug-2025, 02:15 PM (Emergency)
            Date of Discharge  : 25-Aug-2025, 10:30 AM
            Duration of Stay   : 5 days

            Treating Doctor    : Dr. Ravi Deshmukh, MD (Pulmonology)
            Department         : Pulmonary Medicine

            Diagnosis (ICD-10) : J18.9 — Pneumonia, unspecified organism
                                 (Severe Community Acquired Pneumonia)
            Procedure          : Hospitalization with IV Antibiotics,
                                 Oxygen therapy, Chest Physiotherapy

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            Room Charges - Premium Suite
              (5 days × Rs. 8,000/day)                   40,000
            Consulting Physician Visits (5 visits)       10,000
            Medicines & IV Antibiotics                   15,500
            Diagnostic Tests:
              - Chest X-Ray (PA view)                     1,200
              - CBC, ESR, CRP                               900
              - Blood Culture & Sensitivity                1,500
              - Sputum Culture                               800
              - ABG (Arterial Blood Gas)                   1,200
              - HRCT Chest                                 3,500
            Oxygen / Nebulization Charges                  5,200
            Nursing Charges                                2,000
            Physiotherapy (Chest)                           1,200
            ──────────────────────────────────────────────────────
            GROSS TOTAL                                  83,000
            Less: Adjustment                              -6,000
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                        Rs. 77,000
            ══════════════════════════════════════════════════════

            Room Rent per day: Rs. 8,000
            Policy Room Rent Limit: Rs. 5,000/day
            Excess room rent requires policyholder settlement.
        """,
    },

    # 4. REJECTED — Waiting period violation (policy started Jan 2025, hernia in Feb 2025)
    "bill_04_rejected_waiting_period.txt": {
        "description": "REJECTED — Hernia within 30-day initial waiting period",
        "text": """
            ══════════════════════════════════════════════════════════
                      APOLLO HOSPITALS ENTERPRISE LIMITED
                    Bannerghatta Road, Bengaluru - 560076
                    NABH Accredited | JCI Accredited
            ══════════════════════════════════════════════════════════

            PATIENT DISCHARGE SUMMARY & FINAL BILL

            Patient Name       : Mr. Suresh Reddy
            UHID               : APL-2025-112890
            Age / Gender       : 50 years / Male
            Insurance Policy   : SHI/IND/2025/0056781

            Date of Admission  : 18-Jan-2025, 07:30 AM
            Date of Discharge  : 20-Jan-2025, 04:00 PM
            Duration of Stay   : 2 days

            Treating Doctor    : Dr. Mohan Rao, MS, FACS (General Surgery)
            Department         : General Surgery

            Diagnosis (ICD-10) : K40.90 — Unilateral Inguinal Hernia
            Procedure          : Laparoscopic Inguinal Hernia Repair
                                 (TEP - Totally Extra-Peritoneal Repair)
                                 with Prolene Mesh Placement

            Clinical Summary:
            Patient presented with right inguinal swelling for 3 months.
            Diagnosed with right indirect inguinal hernia. Elective
            laparoscopic TEP repair done under general anesthesia.
            Uneventful post-operative recovery.

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            Room Charges - Twin Sharing
              (2 days × Rs. 3,500/day)                    7,000
            Surgeon Fee                                  30,000
            Anaesthesia Charges                          10,000
            Operation Theatre Charges                    12,000
            Prolene Mesh Implant                          8,000
            Medicines & Consumables                       4,500
            Diagnostic Tests (Pre-Op: CBC, ECG, CXR)      2,800
            Nursing Charges                                1,500
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                        Rs. 75,800
            ══════════════════════════════════════════════════════

            Note: Admission date 18-Jan-2025 falls within 30 days
            of policy start date (01-Jan-2025). Also hernia has
            a specific waiting period of 2 years.
        """,
    },

    # 5. REJECTED — Pre-existing disease (diabetes complications, policy < 4 yrs)
    "bill_05_rejected_preexisting.txt": {
        "description": "REJECTED — Diabetic foot surgery, pre-existing diabetes < 4 yrs",
        "text": """
            ══════════════════════════════════════════════════════════
                        MANIPAL HOSPITAL (OLD AIRPORT ROAD)
                    98, HAL Old Airport Road, Bengaluru - 560017
                    NABH Accredited | Reg: KA/BLR/2015/MH-201
            ══════════════════════════════════════════════════════════

            FINAL HOSPITAL BILL / DISCHARGE SUMMARY

            Patient Name       : Mr. Venkatesh Iyer
            UHID               : MH-2025-34567
            Age / Gender       : 58 years / Male

            Date of Admission  : 05-Sep-2025, 11:00 AM
            Date of Discharge  : 12-Sep-2025, 02:00 PM
            Duration of Stay   : 7 days

            Treating Doctor    : Dr. Shilpa Nair, MS (General Surgery)
                                 Dr. Arvind Mehta, MD (Endocrinology)
            Department         : General Surgery / Endocrinology

            Diagnosis:
              1. E11.621 — Type 2 Diabetes Mellitus with foot ulcer
              2. L97.529 — Non-pressure chronic ulcer, left foot
              3. I70.233 — Atherosclerosis, left leg with ulceration

            Procedure:
              Surgical debridement of diabetic foot ulcer (left foot)
              with negative pressure wound therapy (VAC therapy)

            Clinical History:
            Known case of Type 2 Diabetes Mellitus for 12 years (since
            2013), currently on Insulin Glargine 20U + Metformin 1000mg.
            HbA1c on admission: 9.2%. This is a complication directly
            arising from the patient's pre-existing diabetes.

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            Room Charges - Single AC
              (7 days × Rs. 4,500/day)                   31,500
            Surgeon Fee (Debridement × 2 sittings)       20,000
            Dressing Material & VAC Therapy Kit           18,000
            Medicines (Antibiotics IV, Insulin, etc.)    12,500
            Endocrinology Consultation (3 visits)         4,500
            Diagnostic Tests
              - HbA1c, FBS, PPBS, Lipid Profile           2,200
              - Color Doppler Lower Limb                   3,500
              - Wound Culture & Sensitivity                1,800
              - CBC, KFT, LFT                              1,500
            Nursing Charges (7 days)                       3,500
            Physiotherapy                                  2,000
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                       Rs. 1,01,000
            ══════════════════════════════════════════════════════

            Pre-existing condition: Diabetes since 2013 (12 years).
            Policy inception: Jan 2024 (< 4 years cover for PED).
        """,
    },

    # 6. PARTIAL — Senior citizen co-pay (age > 60)
    "bill_06_partial_copay_senior.txt": {
        "description": "PARTIAL — Senior citizen (65 yrs), 10% co-pay applicable",
        "text": """
            ══════════════════════════════════════════════════════════
                    NARAYANA HEALTH — HEALTH CITY CAMPUS
                   #258/A, Bommasandra, Bengaluru - 560099
                   NABH & JCI Accredited
            ══════════════════════════════════════════════════════════

            PATIENT DISCHARGE SUMMARY & FINAL BILL

            Patient Name       : Mr. Ramachandran Pillai
            UHID               : NH-2025-78901
            Age / Gender       : 65 years / Male

            Date of Admission  : 02-Jul-2025, 06:45 PM (Emergency)
            Date of Discharge  : 08-Jul-2025, 11:30 AM
            Duration of Stay   : 6 days (including 2 days in ICU)

            Treating Doctor    : Dr. Suresh Hegde, DM (Cardiology)
            Department         : Cardiology / Cardiac ICU

            Diagnosis (ICD-10) : I21.0 — Acute ST-Elevation Myocardial
                                 Infarction (STEMI), Anterior Wall
            Procedure          : Primary Percutaneous Coronary
                                 Intervention (PCI) with Drug Eluting
                                 Stent (DES) to LAD artery

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            ICU / ICCU Charges (2 days × Rs.8,000)       16,000
            Room Charges - Single AC
              (4 days × Rs. 4,000/day)                   16,000
            Cardiologist / Interventionist Fee           40,000
            Drug Eluting Stent (DES) × 1                 35,000
            Cath Lab / Procedure Charges                 30,000
            Anaesthesia Charges                           8,000
            Medicines (Antiplatelets, Statins,
              Heparin, Nitrates, Beta-blockers)          12,000
            Diagnostic Tests:
              - 2D Echo                                   3,000
              - Coronary Angiography                      8,000
              - Troponin-I, CK-MB, BNP                    2,500
              - CBC, KFT, LFT, Lipid Profile              2,000
              - ECG (serial × 4)                            800
            Nursing Charges (6 days)                       3,000
            Cardiac Rehabilitation (1 session)             1,500
            ──────────────────────────────────────────────────────
            GROSS TOTAL                                1,77,800
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                       Rs. 1,77,800
            ══════════════════════════════════════════════════════

            Note: Patient is 65 years old. As per policy Section 8.1,
            10% co-payment is applicable for ages 60-75.
        """,
    },

    # 7. PARTIAL — Sum insured breached (claim > Rs. 5,00,000)
    "bill_07_partial_sum_insured.txt": {
        "description": "PARTIAL — Total bill Rs. 6,25,000 exceeds sum insured Rs. 5,00,000",
        "text": """
            ══════════════════════════════════════════════════════════
                        FORTIS HOSPITAL, BANNERGHATTA ROAD
                    154/9, Bannerghatta Road, Bengaluru - 560076
                    NABH Accredited
            ══════════════════════════════════════════════════════════

            FINAL HOSPITAL BILL / TAX INVOICE

            Patient Name       : Mr. Deepak Joshi
            UHID               : FH-2025-23456
            Age / Gender       : 48 years / Male

            Date of Admission  : 10-Oct-2025, 09:00 AM (Emergency)
            Date of Discharge  : 30-Oct-2025, 03:00 PM
            Duration of Stay   : 20 days (including 8 days in ICU)

            Treating Doctor    : Dr. Pradeep Kumar, MCh (Neuro Surgery)
                                 Dr. Anjali Sharma, DM (Neurology)
            Department         : Neurosurgery / Neurology ICU

            Diagnosis (ICD-10) : I61.0 — Intracerebral Hemorrhage,
                                 left basal ganglia
                                 G93.6 — Cerebral Edema
            Procedure          : Emergency Craniotomy and Evacuation
                                 of Intracerebral Hematoma,
                                 Decompressive Craniectomy

            ─────────────  ITEMIZED BILL  ──────────────────────────

            Description                              Amount (Rs.)
            ──────────────────────────────────────────────────────
            ICU / Neuro ICU Charges
              (8 days × Rs. 10,000/day)                  80,000
            Room Charges - Single Deluxe
              (12 days × Rs. 5,000/day)                  60,000
            Neurosurgeon Fee                             80,000
            Anaesthesia Charges (Craniotomy)              25,000
            Operation Theatre Charges                    40,000
            Cranial Implant (Titanium Mesh)              45,000
            Ventilator Charges (5 days)                  50,000
            Medicines & Drugs:
              - IV Antibiotics                           15,000
              - Mannitol, Anticonvulsants                 8,000
              - Blood Products (FFP, Platelets)          12,000
            Diagnostic Tests:
              - CT Brain (× 4 scans)                     16,000
              - MRI Brain with contrast                  10,000
              - EEG Monitoring                            5,000
              - CBC, KFT, LFT, ABG (serial)               6,000
              - Coagulation Profile (serial)               3,000
            Neurology Consultations (8 visits)           12,000
            Physiotherapy (10 sessions)                   10,000
            Tracheostomy Kit & Care                       8,000
            Nursing Charges (20 days)                    10,000
            Attendant / Dietician                         2,000
            Ambulance (inter-facility transfer)           2,000
            Administrative & Documentation                3,000
            Toiletries & Guest Meals                      2,000
            Telephone & TV Rental                         1,000
            ──────────────────────────────────────────────────────
            GROSS TOTAL                                6,30,000
            Less: Non-medical items (Section 11)         -5,000
            ──────────────────────────────────────────────────────
            NET TOTAL PAYABLE                       Rs. 6,25,000
            ══════════════════════════════════════════════════════

            Note: Sum Insured = Rs. 5,00,000. Claim exceeds the
            aggregate limit. Maximum payable under policy is
            Rs. 5,00,000.
        """,
    },
}


def generate_policy_pdf():
    """Create a realistic multi-page insurance policy PDF."""
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    doc = fitz.open()

    for i, page_text in enumerate(POLICY_TEXT_PAGES):
        page = doc.new_page(width=595, height=842)  # A4
        text_rect = fitz.Rect(50, 50, 545, 780)

        # Title page gets larger font
        fontsize = 10 if i == 0 else 9.5
        page.insert_textbox(
            text_rect,
            page_text.strip(),
            fontsize=fontsize,
            fontname="helv",
        )

        # Page number footer (skip cover page)
        if i > 0:
            footer_rect = fitz.Rect(260, 810, 335, 830)
            page.insert_textbox(footer_rect, f"— Page {i + 1} —", fontsize=8, fontname="helv")

    path = os.path.join(SAMPLE_DIR, "sample_policy.pdf")
    doc.save(path)
    doc.close()
    print(f"Created: {path}  ({len(POLICY_TEXT_PAGES)} pages)")


def generate_bill_files():
    """Create hospital bill text files and corresponding PDFs."""
    os.makedirs(SAMPLE_DIR, exist_ok=True)

    for filename, case in BILL_CASES.items():
        # Write .txt
        txt_path = os.path.join(SAMPLE_DIR, filename)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(case["text"].strip())
        print(f"Created: {txt_path}  [{case['description']}]")

        # Write .pdf — auto-paginate long bills
        pdf_name = filename.replace(".txt", ".pdf")
        doc = fitz.open()
        bill_text = case["text"].strip()
        fontsize = 8.5
        fontname = "cour"

        while bill_text:
            page = doc.new_page(width=595, height=842)
            text_rect = fitz.Rect(40, 40, 555, 800)
            rc = page.insert_textbox(
                text_rect, bill_text, fontsize=fontsize, fontname=fontname
            )
            if rc >= 0:
                # All text fit on this page
                break
            # Text overflowed — estimate how much fit and continue
            # rc < 0 means overflow; we split text roughly by page capacity
            chars_per_page = int(len(bill_text) * 0.65)  # conservative estimate
            bill_text = bill_text[chars_per_page:].strip()
        pdf_path = os.path.join(SAMPLE_DIR, pdf_name)
        doc.save(pdf_path)
        doc.close()
        print(f"Created: {pdf_path}")


if __name__ == "__main__":
    generate_policy_pdf()
    print()
    generate_bill_files()
    print(f"\n✓ All files generated in: {os.path.abspath(SAMPLE_DIR)}")
