"""Declarative specifications for the 7 CrimeGPT legal document templates.

Each spec drives BOTH the .docx template builder (build_templates.py) and the
HTML renderer used for PDF export (document_service.render_html), so the two
output formats always stay in sync.

Spec shape (per doc type):
    {
        "header":          [str, ...]         # letterhead lines, centered bold
        "title":           str,               # main document title
        "subtitle":        str,               # statutory reference line
        "meta_rows":       [(label, jinja_placeholder_string), ...],
        "body_paragraphs": [str with jinja placeholders, ...],
        "table":           None | {
                               "caption":     str,
                               "columns":     [(header, cell_placeholder), ...],
                               "loop_var":    str,   # e.g. "item"
                               "loop_source": str,   # e.g. "seized_items"
                           },
        "sign_left":       str ("\n"-separated lines, may contain placeholders),
        "sign_right":      str,
    }

Only the context variables produced by document_service.build_context() are
referenced: fir_number, ps_name, station, incident_date, incident_time,
incident_place, crime_type, narrative_en, io_name, io_badge, accused_name,
accused_address, accused_age, victim_name, victim_address, all_accused,
all_victims, all_witnesses, sections_applied, sections_text, seized_items,
today, case_status.
"""

_LETTERHEAD = [
    "GOVERNMENT OF GUJARAT",
    "OFFICE OF THE COMMISSIONER OF POLICE, AHMEDABAD CITY",
]

DOC_SPECS: dict[str, dict] = {
    # ------------------------------------------------------------------ #
    "CHARGESHEET": {
        "header": _LETTERHEAD,
        "title": "FINAL REPORT / CHARGE SHEET",
        "subtitle": "(Under Section 193 of the Bharatiya Nagarik Suraksha Sanhita, 2023)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }} at {{ incident_time }} hrs"),
            ("Place of Incident", "{{ incident_place }}"),
            ("Nature of Offence", "{{ crime_type }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Investigating Officer", "{{ io_name }} (Badge No. {{ io_badge }})"),
            ("Date of Submission", "{{ today }}"),
        ],
        "body_paragraphs": [
            "It is respectfully submitted that on {{ incident_date }} at about "
            "{{ incident_time }} hrs, at {{ incident_place }}, within the jurisdiction of "
            "{{ ps_name }} Police Station, an offence of {{ crime_type }} was reported and "
            "registered vide FIR No. {{ fir_number }} against the accused persons named herein.",
            "Brief facts of the case: {{ narrative_en }}",
            "During the course of investigation, the statement of the complainant "
            "{{ victim_name }} and the statements of witnesses were recorded under Section 180 "
            "of the BNSS, 2023; the scene of offence was inspected and a Panchanama thereof was "
            "drawn; and the material evidence and muddamal articles were seized in the presence "
            "of independent panch witnesses in accordance with law.",
            "The investigation so conducted has established a prima facie case against the "
            "accused {{ accused_name }}, aged {{ accused_age }}, resident of "
            "{{ accused_address }}, and the co-accused (if any) named in the table below, for "
            "offences punishable under {{ sections_applied|length }} section(s), namely "
            "{{ sections_text }}. The present status of the case is {{ case_status }}.",
            "It is therefore prayed that this Final Report may kindly be accepted, cognizance "
            "of the aforesaid offences may be taken against the accused persons, and they may "
            "be tried and dealt with in accordance with law.",
        ],
        "table": {
            "caption": "Particulars of Accused Persons",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Name of Accused", "{{ person.name }}"),
                ("Age", "{{ person.age or '' }}"),
                ("Gender", "{{ person.gender or '' }}"),
                ("Address", "{{ person.address or '' }}"),
            ],
            "loop_var": "person",
            "loop_source": "all_accused",
        },
        "sign_left": "Station House Officer\n{{ ps_name }} Police Station, {{ station }}",
        "sign_right": "Investigating Officer\n{{ io_name }} (Badge No. {{ io_badge }})",
    },
    # ------------------------------------------------------------------ #
    "MEDICAL_LETTER": {
        "header": _LETTERHEAD,
        "title": "REQUEST FOR MEDICAL EXAMINATION",
        "subtitle": "(Medico-Legal Case Referral — To the Medical Officer, Civil Hospital)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }} at {{ incident_time }} hrs"),
            ("Name of Person Referred", "{{ victim_name }}"),
            ("Address of Person Referred", "{{ victim_address }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Date of Referral", "{{ today }}"),
        ],
        "body_paragraphs": [
            "To, The Medical Officer, Civil Hospital, Ahmedabad.",
            "Subject: Request for medical examination and issuance of a medico-legal "
            "certificate in connection with FIR No. {{ fir_number }} of {{ ps_name }} "
            "Police Station.",
            "Sir/Madam, it is stated that the above-referenced case has been registered at "
            "this Police Station for the offence of {{ crime_type }}, alleged to have occurred "
            "on {{ incident_date }} at {{ incident_place }}. Brief facts of the case are as "
            "under: {{ narrative_en }}",
            "The injured/victim Shri/Smt. {{ victim_name }}, resident of {{ victim_address }}, "
            "is hereby forwarded to you through police escort for medical examination. You are "
            "requested to kindly examine the said person, record the nature, dimensions and "
            "probable duration of the injuries, the type of weapon likely to have caused them, "
            "and preserve samples for forensic analysis where necessary.",
            "It is further requested that a detailed medico-legal certificate be issued at the "
            "earliest to enable this office to proceed with the investigation under "
            "{{ sections_text }}. Your cooperation in this regard is solicited.",
        ],
        "table": None,
        "sign_left": "Medical Officer\nCivil Hospital, Ahmedabad (Seal & Signature)",
        "sign_right": "Investigating Officer\n{{ io_name }} (Badge No. {{ io_badge }})\n{{ ps_name }} Police Station",
    },
    # ------------------------------------------------------------------ #
    "REMAND_REQUEST": {
        "header": _LETTERHEAD,
        "title": "APPLICATION FOR POLICE CUSTODY REMAND",
        "subtitle": "(Under Section 187 of the Bharatiya Nagarik Suraksha Sanhita, 2023)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }} at {{ incident_time }} hrs"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Name of Accused", "{{ accused_name }}"),
            ("Investigating Officer", "{{ io_name }} (Badge No. {{ io_badge }})"),
            ("Date of Application", "{{ today }}"),
        ],
        "body_paragraphs": [
            "To, The Hon'ble Magistrate/Court having jurisdiction, Ahmedabad.",
            "Most respectfully submitted that the accused {{ accused_name }}, aged "
            "{{ accused_age }}, resident of {{ accused_address }}, has been arrested in "
            "connection with FIR No. {{ fir_number }} of {{ ps_name }} Police Station, "
            "registered for offences punishable under {{ sections_text }}.",
            "Brief facts of the case: {{ narrative_en }}",
            "The custodial interrogation of the accused is necessary for the following "
            "purposes: (i) recovery of the weapon/instruments used in the commission of the "
            "offence and of the muddamal property; (ii) identification and apprehension of "
            "other accused persons involved; (iii) verification of the disclosure statements "
            "made by the accused; and (iv) collection of further material evidence essential "
            "to the investigation.",
            "It is therefore prayed that this Hon'ble Court may be pleased to remand the "
            "accused person(s) named in the table below to police custody under Section 187 "
            "of the BNSS, 2023 for a period deemed fit, in the interest of justice and for "
            "the effective completion of the investigation.",
        ],
        "table": {
            "caption": "Particulars of Accused Persons for Whom Remand Is Sought",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Name of Accused", "{{ person.name }}"),
                ("Age", "{{ person.age or '' }}"),
                ("Gender", "{{ person.gender or '' }}"),
                ("Address", "{{ person.address or '' }}"),
            ],
            "loop_var": "person",
            "loop_source": "all_accused",
        },
        "sign_left": "Before the Hon'ble Court\n(Order of the Magistrate)",
        "sign_right": "Investigating Officer\n{{ io_name }} (Badge No. {{ io_badge }})\n{{ ps_name }} Police Station",
    },
    # ------------------------------------------------------------------ #
    "SEIZURE_RECEIPT": {
        "header": _LETTERHEAD,
        "title": "SEIZURE RECEIPT",
        "subtitle": "(Receipt of Articles Seized During Investigation)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }}"),
            ("Place of Seizure", "{{ incident_place }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Date of Seizure Receipt", "{{ today }}"),
        ],
        "body_paragraphs": [
            "This is to certify that in connection with the investigation of FIR No. "
            "{{ fir_number }} of {{ ps_name }} Police Station, registered for the offence of "
            "{{ crime_type }} under {{ sections_text }}, the articles described in the table "
            "below have been seized by the undersigned Investigating Officer in the presence "
            "of two independent panch witnesses.",
            "The articles were duly sealed, labelled and taken into police custody as muddamal "
            "property on {{ today }}. The seizure was effected in accordance with the "
            "provisions of the BNSS, 2023, and a Panchanama of the proceedings has been drawn "
            "separately.",
            "A copy of this receipt has been furnished to the person from whose possession the "
            "articles were seized, in acknowledgement of the seizure.",
        ],
        "table": {
            "caption": "Description of Seized Articles (Muddamal)",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Article", "{{ item.item_name }}"),
                ("Quantity", "{{ item.quantity or '' }}"),
                ("Description", "{{ item.description or '' }}"),
                ("Seized From", "{{ item.seized_from or '' }}"),
            ],
            "loop_var": "item",
            "loop_source": "seized_items",
        },
        "sign_left": "Panch Witness No. 1\n(Name, Address & Signature)",
        "sign_right": "Panch Witness No. 2\n(Name, Address & Signature)\n\nInvestigating Officer: {{ io_name }} ({{ io_badge }})",
    },
    # ------------------------------------------------------------------ #
    "COURT_CUSTODY": {
        "header": _LETTERHEAD,
        "title": "APPLICATION FOR CUSTODY OF MUDDAMAL PROPERTY",
        "subtitle": "(Under Section 497 of the Bharatiya Nagarik Suraksha Sanhita, 2023)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Case Status", "{{ case_status }}"),
            ("Investigating Officer", "{{ io_name }} (Badge No. {{ io_badge }})"),
            ("Date of Application", "{{ today }}"),
        ],
        "body_paragraphs": [
            "To, The Hon'ble Magistrate/Court having jurisdiction, Ahmedabad.",
            "Most respectfully submitted that during the investigation of FIR No. "
            "{{ fir_number }} of {{ ps_name }} Police Station, registered for the offence of "
            "{{ crime_type }} under {{ sections_text }}, the muddamal articles described in "
            "the table below were lawfully seized and are presently held in the muddamal "
            "room of this Police Station.",
            "Brief facts of the case: {{ narrative_en }}",
            "The said articles constitute material evidence in the above case. It is prayed "
            "that this Hon'ble Court may be pleased to pass appropriate orders under Section "
            "497 of the BNSS, 2023 regarding the custody and disposal of the said muddamal "
            "property during the pendency of the inquiry/trial, including directions for its "
            "safe keeping, photography, videography or interim custody, as deemed fit in the "
            "interest of justice.",
        ],
        "table": {
            "caption": "Muddamal Articles for Which Custody Orders Are Sought",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Article", "{{ item.item_name }}"),
                ("Quantity", "{{ item.quantity or '' }}"),
                ("Description", "{{ item.description or '' }}"),
                ("Seized From", "{{ item.seized_from or '' }}"),
            ],
            "loop_var": "item",
            "loop_source": "seized_items",
        },
        "sign_left": "Before the Hon'ble Court\n(Order of the Magistrate)",
        "sign_right": "Investigating Officer\n{{ io_name }} (Badge No. {{ io_badge }})\n{{ ps_name }} Police Station",
    },
    # ------------------------------------------------------------------ #
    "PANCHANAMA": {
        "header": _LETTERHEAD,
        "title": "PANCHANAMA",
        "subtitle": "(Memorandum of Proceedings Drawn in the Presence of Panch Witnesses)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }} at {{ incident_time }} hrs"),
            ("Place of Proceedings", "{{ incident_place }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Date of Panchanama", "{{ today }}"),
        ],
        "body_paragraphs": [
            "We, the undersigned panch witnesses, having been called upon by "
            "{{ io_name }} (Badge No. {{ io_badge }}), Investigating Officer of {{ ps_name }} "
            "Police Station, do hereby state that we accompanied the said officer to "
            "{{ incident_place }} on {{ today }} in connection with FIR No. {{ fir_number }}, "
            "registered for the offence of {{ crime_type }}.",
            "Brief facts of the case as narrated to us: {{ narrative_en }}",
            "In our presence, the Investigating Officer inspected the scene of offence, and "
            "the articles described in the table below were found, taken charge of, sealed "
            "and labelled. Each article was shown to us before being sealed, and the seals "
            "were affixed in our presence.",
            "The proceedings commenced and concluded in our continuous presence, and the "
            "contents of this Panchanama have been read over and explained to us in the "
            "language we understand. We affirm the same to be a true and correct record of "
            "the proceedings, in witness whereof we set our hands below.",
        ],
        "table": {
            "caption": "Articles Found and Seized in the Presence of Panchas",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Article", "{{ item.item_name }}"),
                ("Quantity", "{{ item.quantity or '' }}"),
                ("Description", "{{ item.description or '' }}"),
                ("Seized From", "{{ item.seized_from or '' }}"),
            ],
            "loop_var": "item",
            "loop_source": "seized_items",
        },
        "sign_left": "Panch Witness No. 1\n(Name, Address & Signature)",
        "sign_right": "Panch Witness No. 2\n(Name, Address & Signature)\n\nInvestigating Officer: {{ io_name }} ({{ io_badge }})",
    },
    # ------------------------------------------------------------------ #
    "FACE_ID_FORM": {
        "header": _LETTERHEAD,
        "title": "FACE IDENTIFICATION FORM",
        "subtitle": "(Descriptive Particulars of Accused Persons for Identification)",
        "meta_rows": [
            ("FIR Number", "{{ fir_number }}"),
            ("Police Station", "{{ ps_name }}, {{ station }}"),
            ("Date of Incident", "{{ incident_date }}"),
            ("Nature of Offence", "{{ crime_type }}"),
            ("Sections Applied", "{{ sections_text }}"),
            ("Prepared By", "{{ io_name }} (Badge No. {{ io_badge }})"),
            ("Date of Preparation", "{{ today }}"),
        ],
        "body_paragraphs": [
            "This form records the descriptive and identification particulars of the accused "
            "person(s) involved in FIR No. {{ fir_number }} of {{ ps_name }} Police Station, "
            "for the purpose of identification proceedings, circulation to other units, and "
            "record in the case file.",
            "The particulars entered in the identification table below have been gathered "
            "during the investigation from the statements of the complainant "
            "{{ victim_name }}, the witnesses, and available records. A recent photograph of "
            "each accused, where available, shall be affixed to this form and attested by the "
            "Investigating Officer.",
            "This form shall accompany the case papers and may be used during test "
            "identification parades conducted in accordance with law.",
        ],
        "table": {
            "caption": "Identification Details of Accused Persons",
            "columns": [
                ("Sr. No.", "{{ loop.index }}"),
                ("Name of Accused", "{{ person.name }}"),
                ("Age", "{{ person.age or '' }}"),
                ("Gender", "{{ person.gender or '' }}"),
                ("Address", "{{ person.address or '' }}"),
            ],
            "loop_var": "person",
            "loop_source": "all_accused",
        },
        "sign_left": "Station House Officer\n{{ ps_name }} Police Station, {{ station }}",
        "sign_right": "Investigating Officer\n{{ io_name }} (Badge No. {{ io_badge }})",
    },
}
