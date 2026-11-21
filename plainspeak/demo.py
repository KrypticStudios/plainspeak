"""Demo mode: ready-made answers for the sample letters.

These were written by the team so the app can be shown even with no API key
or no internet. The live app uses Gemini instead (see analyzer.py).
"""

from pathlib import Path

from .schema import LetterAnalysis

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

SAMPLES = {
    "Eviction notice (rent)": "eviction_notice.txt",
    "Food benefits renewal": "benefits_renewal.txt",
    "Hospital bill": "medical_bill.txt",
}


def sample_text(name: str) -> str:
    return (SAMPLES_DIR / SAMPLES[name]).read_text()


_EVICTION_EN = {
    "document_type": "Eviction warning (14-day notice to pay rent)",
    "sender": "Maplewood Property Management LLC (your landlord)",
    "summary": "Your landlord says you did not pay rent for October and November. You owe $1,450. "
               "You must pay it by December 4, 2026, or move out. If you do neither, the landlord can take you "
               "to court to make you leave. This is not an eviction yet, and there is still time to get help.",
    "urgency": "high",
    "urgency_reason": "You have less than 2 weeks before the landlord can go to court.",
    "deadlines": [
        {"date": "2026-12-04", "what": "Pay $1,450 in rent (or move out) by this day",
         "source_quote": "Payment must be made on or before December 4, 2026."},
    ],
    "actions": [
        {"step": "Call the Riverton Housing Help Line today to ask about emergency rent help.",
         "source_quote": "Contact the Riverton Housing Help Line at (555) 013-7700 for information regarding emergency rental assistance programs."},
        {"step": "Pay with a money order or cashier's check. Do not use a personal check.",
         "source_quote": "Personal checks will not be accepted. Payment must be made by money order or cashier's check."},
        {"step": "Bring or mail the payment to the office and keep your receipt.",
         "source_quote": "Payment may be delivered in person to the office address listed above, Monday through Friday, 9:00 AM to 5:00 PM, or mailed to the same address."},
        {"step": "If you think the amount is wrong, call the landlord's office.",
         "source_quote": "If you believe this notice is in error, you may contact our office."},
    ],
    "money": [
        {"amount": "$1,450.00", "what": "Total rent you owe (October + November)",
         "source_quote": "TOTAL AMOUNT DUE: $1,450.00"},
        {"amount": "$725.00", "what": "Rent for each month", "source_quote": "Rent due October 1, 2026: $725.00"},
    ],
    "contacts": [
        {"name": "Riverton Housing Help Line", "phone": "(555) 013-7700", "email": "", "address": "",
         "why": "Free help paying rent in an emergency"},
        {"name": "Maplewood Property Management (J. Hartwell)", "phone": "(555) 014-2290", "email": "",
         "address": "4410 Harbor View Drive, Suite 200, Riverton, CA 90000",
         "why": "To pay rent or ask questions about this notice"},
    ],
    "rights": ["You may be able to get emergency money to help pay rent.",
               "You can tell the landlord if you think this notice is a mistake."],
    "unclear_points": ["The letter does not say if late fees will be added.",
                       "The letter does not say how it was delivered, which can change when the 14 days start."],
    "needs_human_help": True,
    "help_reason": "Eviction can lead to court. A free tenant lawyer or housing counselor can explain your rights.",
    "confidence": "high",
}

_EVICTION_ES = {
    **_EVICTION_EN,
    "document_type": "Aviso de desalojo (aviso de 14 días para pagar la renta)",
    "sender": "Maplewood Property Management LLC (su arrendador)",
    "summary": "Su arrendador dice que usted no pagó la renta de octubre y noviembre. Usted debe $1,450. "
               "Tiene que pagar antes del 4 de diciembre de 2026 o mudarse. Si no hace ninguna de las dos cosas, "
               "el arrendador puede llevarle a la corte para sacarle. Todavía no es un desalojo y hay tiempo para pedir ayuda.",
    "urgency_reason": "Tiene menos de 2 semanas antes de que el arrendador pueda ir a la corte.",
    "deadlines": [
        {"date": "2026-12-04", "what": "Pagar $1,450 de renta (o mudarse) antes de este día",
         "source_quote": "Payment must be made on or before December 4, 2026."},
    ],
    "actions": [
        {"step": "Llame hoy a la Línea de Ayuda de Vivienda de Riverton para pedir ayuda de emergencia con la renta.",
         "source_quote": "Contact the Riverton Housing Help Line at (555) 013-7700 for information regarding emergency rental assistance programs."},
        {"step": "Pague con giro postal (money order) o cheque de caja. No use un cheque personal.",
         "source_quote": "Personal checks will not be accepted. Payment must be made by money order or cashier's check."},
        {"step": "Lleve o envíe el pago a la oficina y guarde su recibo.",
         "source_quote": "Payment may be delivered in person to the office address listed above, Monday through Friday, 9:00 AM to 5:00 PM, or mailed to the same address."},
        {"step": "Si cree que la cantidad está mal, llame a la oficina del arrendador.",
         "source_quote": "If you believe this notice is in error, you may contact our office."},
    ],
    "money": [
        {"amount": "$1,450.00", "what": "Total de renta que debe (octubre + noviembre)",
         "source_quote": "TOTAL AMOUNT DUE: $1,450.00"},
        {"amount": "$725.00", "what": "Renta de cada mes", "source_quote": "Rent due October 1, 2026: $725.00"},
    ],
    "contacts": [
        {"name": "Línea de Ayuda de Vivienda de Riverton", "phone": "(555) 013-7700", "email": "", "address": "",
         "why": "Ayuda gratis para pagar la renta en una emergencia"},
        {"name": "Maplewood Property Management (J. Hartwell)", "phone": "(555) 014-2290", "email": "",
         "address": "4410 Harbor View Drive, Suite 200, Riverton, CA 90000",
         "why": "Para pagar la renta o hacer preguntas sobre este aviso"},
    ],
    "rights": ["Es posible que pueda recibir dinero de emergencia para pagar la renta.",
               "Puede decirle al arrendador si cree que este aviso es un error."],
    "unclear_points": ["La carta no dice si se agregarán cargos por pago tardío.",
                       "La carta no dice cómo fue entregada, y eso puede cambiar cuándo empiezan los 14 días."],
    "help_reason": "Un desalojo puede llegar a la corte. Un abogado gratuito para inquilinos puede explicarle sus derechos.",
}

_BENEFITS_EN = {
    "document_type": "Food benefits renewal notice",
    "sender": "Sample County Department of Social Services",
    "summary": "Your food benefits will stop after December 31, 2026, unless you renew them. "
               "To renew, you need to do a phone interview on December 9 at 10:30 AM, and send a form with "
               "proof of your income and housing costs by December 15. If you miss these, your benefits stop on January 1.",
    "urgency": "high",
    "urgency_reason": "Missing the interview or the form will stop your food benefits.",
    "deadlines": [
        {"date": "2026-12-09", "what": "Phone interview at 10:30 AM (a caseworker will call you)",
         "source_quote": "Interview Date: 12/09/2026"},
        {"date": "2026-12-15", "what": "Send Form FA-22 and your proof documents",
         "source_quote": "Your completed form and documents must be received by 12/15/2026."},
        {"date": "2026-12-31", "what": "Your current benefits period ends",
         "source_quote": "Your eligibility period for Food Assistance benefits ends on 12/31/2026."},
    ],
    "actions": [
        {"step": "Keep your phone on and nearby on December 9 at 10:30 AM.",
         "source_quote": "Interview Type: Telephone. A caseworker will call you at the number on file."},
        {"step": "Fill out Form FA-22 (it came with this letter).",
         "source_quote": "You must also submit the enclosed Recertification Form (Form FA-22)"},
        {"step": "Collect proof of income from the last 30 days, proof of rent or housing costs, and any changes in who lives with you.",
         "source_quote": "verification of all household income received in the last 30 days, verification of current shelter costs, and any changes in household composition"},
        {"step": "If you can't do the interview at that time, call before December 9 to change it.",
         "source_quote": "you must call Customer Service at (555) 019-4400 before your interview date to reschedule."},
    ],
    "money": [],
    "contacts": [
        {"name": "County Customer Service", "phone": "(555) 019-4400", "email": "",
         "address": "200 Civic Center Plaza, Riverton, CA 90000",
         "why": "To reschedule your interview or ask questions"},
    ],
    "rights": ["You can ask for a fair hearing if you disagree with a decision.",
               "You can get a free interpreter."],
    "unclear_points": ["The letter does not give the website address for the benefits portal."],
    "needs_human_help": False,
    "help_reason": "You can probably do this yourself. Call the county if anything is confusing or you need an interpreter.",
    "confidence": "high",
}

_BILL_EN = {
    "document_type": "Hospital bill (final notice)",
    "sender": "Riverton General Hospital, Patient Financial Services",
    "summary": "The hospital says you still owe $930 for your emergency room visit on August 22. Insurance already paid part of it. "
               "If you don't pay or set up a payment plan by December 15, 2026, they may send the bill to a collection agency. "
               "You might be able to get the bill lowered or removed through their Financial Assistance Program.",
    "urgency": "medium",
    "urgency_reason": "You have about 3 weeks before the bill could go to collections.",
    "deadlines": [
        {"date": "2026-12-15", "what": "Pay, set up a payment plan, or apply for financial help before this day",
         "source_quote": "If payment in full or acceptable payment arrangements are not received by December 15, 2026, your account may be referred to an outside collection agency."},
    ],
    "actions": [
        {"step": "Call the hospital and ask for a Financial Assistance Application. Apply before December 15.",
         "source_quote": "To apply, complete a Financial Assistance Application, available at our Patient Financial Services office or by calling (555) 017-3300."},
        {"step": "If you can't pay all at once, ask for a payment plan.",
         "source_quote": "Payment plans are available."},
    ],
    "money": [
        {"amount": "$930.00", "what": "What the hospital says you owe", "source_quote": "PATIENT RESPONSIBILITY: $930.00"},
        {"amount": "$2,910.00", "what": "Already paid or removed by insurance",
         "source_quote": "Insurance Payments and Adjustments: -$2,910.00"},
    ],
    "contacts": [
        {"name": "Riverton General Hospital Billing", "phone": "(555) 017-3300", "email": "",
         "address": "PO Box 7781, Riverton, CA 90000", "why": "Financial help, payment plans, or billing questions"},
    ],
    "rights": ["If your household income is at or below 400% of the poverty level, the bill may be reduced or removed.",
               "Applying for help before collections pauses collection activity."],
    "unclear_points": ["The letter does not say what 400% of the poverty level is in dollars for your family size."],
    "needs_human_help": False,
    "help_reason": "The hospital's billing office can help you apply. A free health-insurance counselor can help if you're unsure.",
    "confidence": "high",
}

_DEMO = {
    ("Eviction notice (rent)", "English"): _EVICTION_EN,
    ("Eviction notice (rent)", "Español (Spanish)"): _EVICTION_ES,
    ("Food benefits renewal", "English"): _BENEFITS_EN,
    ("Hospital bill", "English"): _BILL_EN,
}


def demo_languages(sample: str) -> list[str]:
    return [lang for (s, lang) in _DEMO if s == sample]


def demo_analysis(sample: str, language: str) -> LetterAnalysis | None:
    data = _DEMO.get((sample, language))
    if data is None:
        return None
    return LetterAnalysis(original_text=sample_text(sample), **data)


def with_simulated_mistake(a: LetterAnalysis) -> LetterAnalysis:
    """For the demo: add two mistakes like an AI might make, to show PlainSpeak's checks catching them.

    1. An invented deadline whose "quote" isn't in the letter at all (easy to catch).
    2. A sneaky one: a REAL sentence from the letter, paired with the WRONG date (another date that
       does appear in the letter, e.g. the day it was sent). Only the "date must be next to its
       sentence" check catches this one.
    """
    from .checks import dates_in, deadline_is_trustworthy
    from .schema import Deadline

    invented = Deadline(date="2026-11-28", what="⚠ SIMULATED AI MISTAKE 1: pay a $200 late fee",
                        source_quote="A late fee of $200.00 will be charged after November 28, 2026.")
    mistakes = [invented]
    real = next((d for d in a.deadlines if deadline_is_trustworthy(d, a.original_text)), None)
    if real:
        other_dates = sorted(x for x in dates_in(a.original_text) if x.isoformat() != real.date)
        if other_dates:
            mistakes.append(Deadline(date=other_dates[0].isoformat(),
                                     what=f"⚠ SIMULATED AI MISTAKE 2: {real.what}",
                                     source_quote=real.source_quote))
    return a.model_copy(update={"deadlines": [*mistakes, *a.deadlines]})


# Ready-made answers to suggested questions, so "Ask a question" works in the demo with no AI key.
# Keyed by the answer's document_type. Some questions are deliberately NOT answered by the letter,
# to show that PlainSpeak says "the letter doesn't say" instead of guessing.
_QA = {
    _EVICTION_EN["document_type"]: [
        ("What happens if I can't pay by December 4?",
         {"answer": "The landlord can start a court case to take back your apartment. They can also ask you to pay "
                    "court costs and their lawyer's fees. Call the Housing Help Line now. They may help you pay.",
          "answered_from_letter": True,
          "source_quotes": ["Failure to do so will result in the landlord instituting legal proceedings against you to "
                            "recover possession of the premises",
                            "together with court costs and attorney's fees as permitted by law"],
          "who_to_ask": "Riverton Housing Help Line, (555) 013-7700"}),
        ("Can I pay with a personal check?",
         {"answer": "No. You must pay with a money order or a cashier's check.", "answered_from_letter": True,
          "source_quotes": ["Personal checks will not be accepted. Payment must be made by money order or cashier's check."],
          "who_to_ask": ""}),
        ("Will I have to go to court right away?",
         {"answer": "The letter doesn't say when a court case would start. Ask a free tenant lawyer or the Housing "
                    "Help Line. They can explain what happens next where you live.",
          "answered_from_letter": False, "source_quotes": [],
          "who_to_ask": "Riverton Housing Help Line, (555) 013-7700, or a free tenant lawyer (LawHelp.org)"}),
    ],
    _EVICTION_ES["document_type"]: [
        ("¿Qué pasa si no puedo pagar antes del 4 de diciembre?",
         {"answer": "El arrendador puede empezar un caso en la corte para recuperar su apartamento. También puede "
                    "pedirle que pague los costos de la corte y de su abogado. Llame ahora a la Línea de Ayuda de Vivienda.",
          "answered_from_letter": True,
          "source_quotes": ["Failure to do so will result in the landlord instituting legal proceedings against you to "
                            "recover possession of the premises",
                            "together with court costs and attorney's fees as permitted by law"],
          "who_to_ask": "Línea de Ayuda de Vivienda de Riverton, (555) 013-7700"}),
        ("¿Puedo pagar con un cheque personal?",
         {"answer": "No. Tiene que pagar con giro postal (money order) o cheque de caja.", "answered_from_letter": True,
          "source_quotes": ["Personal checks will not be accepted. Payment must be made by money order or cashier's check."],
          "who_to_ask": ""}),
    ],
    _BENEFITS_EN["document_type"]: [
        ("What if I can't do the interview on December 9?",
         {"answer": "Call the county before December 9 to pick a new time.", "answered_from_letter": True,
          "source_quotes": ["If you cannot attend your interview at the scheduled time, you must call Customer Service "
                            "at (555) 019-4400 before your interview date to reschedule."],
          "who_to_ask": ""}),
        ("What papers do I need to send?",
         {"answer": "Send Form FA-22, proof of all money your household got in the last 30 days, proof of your rent or "
                    "housing costs, and any changes in who lives with you.", "answered_from_letter": True,
          "source_quotes": ["verification of all household income received in the last 30 days, verification of current "
                            "shelter costs, and any changes in household composition"],
          "who_to_ask": ""}),
        ("How much money will I get each month?",
         {"answer": "The letter doesn't say how much you will get. Ask the county when they call you.",
          "answered_from_letter": False, "source_quotes": [], "who_to_ask": "County Customer Service, (555) 019-4400"}),
    ],
    _BILL_EN["document_type"]: [
        ("Can I get this bill lowered?",
         {"answer": "Maybe. If your household income is low enough, the hospital may lower or remove the bill. "
                    "Ask for a Financial Assistance Application before December 15.", "answered_from_letter": True,
          "source_quotes": ["Patients with household income at or below 400% of the Federal Poverty Level may qualify "
                            "for a full or partial reduction of their balance."],
          "who_to_ask": "Riverton General Hospital Billing, (555) 017-3300"}),
        ("Will this hurt my credit score?",
         {"answer": "The letter doesn't talk about your credit score. It only says the bill may be sent to a "
                    "collection agency after December 15. Ask the billing office.",
          "answered_from_letter": False,
          "source_quotes": ["your account may be referred to an outside collection agency"],
          "who_to_ask": "Riverton General Hospital Billing, (555) 017-3300"}),
    ],
}


def suggested_questions(a: LetterAnalysis) -> list[str]:
    return [q for q, _ in _QA.get(a.document_type, [])]


def demo_answer(a: LetterAnalysis, question: str):
    """The saved answer for a suggested question, or None."""
    from .schema import QuestionAnswer
    for q, ans in _QA.get(a.document_type, []):
        if q == question:
            return QuestionAnswer(**ans)
    return None
