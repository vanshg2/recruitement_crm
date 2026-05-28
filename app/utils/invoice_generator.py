"""
Invoice Generator - CRM Format
Generates PDF invoices matching the company's official format
CRM
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import date


COMPANY_INFO = {
    "name": "CRM",
    "gstin": "07DSOPM0015G1ZW",
    "sac_code": "998512",
    "state_code": "06",
    "igst_rate": 18,
}


def generate_invoice_number(sequence: int) -> str:
    year = date.today().year
    return f"BW/{year}-{sequence}"


def format_date(d) -> str:
    if not d:
        return ""
    if isinstance(d, str):
        return d
    day = d.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {d.strftime('%b %Y')}"


def num_to_words(amount: float) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def helper(n):
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        elif n < 1000:
            return ones[n // 100] + " Hundred" + (" " + helper(n % 100) if n % 100 else "")
        elif n < 100000:
            return helper(n // 1000) + " Thousand" + (" " + helper(n % 1000) if n % 1000 else "")
        elif n < 10000000:
            return helper(n // 100000) + " Lakh" + (" " + helper(n % 100000) if n % 100000 else "")
        else:
            return helper(n // 10000000) + " Crore" + (" " + helper(n % 10000000) if n % 10000000 else "")

    n = int(amount)
    paise = round((amount - n) * 100)
    words = helper(n) if n > 0 else "Zero"
    if paise:
        words += f" and {helper(paise)} Paise"
    return words + " Only"


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    buf = BytesIO()

    styles = getSampleStyleSheet()

    style_normal = ParagraphStyle(
        "normal", fontName="Helvetica", fontSize=9, leading=13, textColor=colors.black
    )
    style_bold = ParagraphStyle(
        "bold", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=colors.black
    )
    style_right = ParagraphStyle(
        "right", fontName="Helvetica", fontSize=9, leading=13,
        textColor=colors.black, alignment=TA_RIGHT
    )
    style_right_bold = ParagraphStyle(
        "right_bold", fontName="Helvetica-Bold", fontSize=9, leading=13,
        textColor=colors.black, alignment=TA_RIGHT
    )
    style_center = ParagraphStyle(
        "center", fontName="Helvetica", fontSize=9, leading=13,
        textColor=colors.black, alignment=TA_CENTER
    )

    base_amount = float(invoice_data.get("amount", 0))
    apply_igst = invoice_data.get("apply_igst", True)
    igst_rate = COMPANY_INFO["igst_rate"]
    igst_amount = round(base_amount * igst_rate / 100) if apply_igst else 0
    total_amount = base_amount + igst_amount

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
    )

    story = []

    invoice_no = invoice_data.get("invoice_number", "BW/2025-01")
    invoice_date_str = format_date(invoice_data.get("invoice_date", date.today()))
    sac_code = COMPANY_INFO["sac_code"]
    state_code = COMPANY_INFO["state_code"]

    header_data = [
        [
            Paragraph("", style_normal),
            Paragraph(
                f"<b>TAX INVOICE NO: {invoice_no}</b><br/>"
                f"DATE: {invoice_date_str}<br/>"
                f"SAC Code - {sac_code}<br/>"
                f"State Code - {state_code}",
                style_right
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[9 * cm, 8.5 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    to_for_data = [
        [
            Paragraph("<b>To:</b>", style_bold),
            Paragraph(
                f"<b>For:</b><br/>"
                f"<b>CRM</b><br/>"
                f"GST NO: {COMPANY_INFO['gstin']}",
                style_right_bold
            )
        ]
    ]
    to_for_table = Table(to_for_data, colWidths=[9 * cm, 8.5 * cm])
    to_for_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(to_for_table)
    story.append(Spacer(1, 6))

    company_name = invoice_data.get("company_name", "")
    company_address = invoice_data.get("company_address", "")
    company_gstin = invoice_data.get("company_gstin", "")
    company_state = invoice_data.get("company_state", "Haryana")
    company_pan = invoice_data.get("company_pan", "")
    place_of_supply = invoice_data.get("place_of_supply", "")

    address_lines = [f"<b>{company_name}</b>"]
    if company_address:
        address_lines.append(company_address)
    address_lines.append(f"State of Supply {state_code}-{company_state}     Country - INDIA")
    if company_gstin:
        address_lines.append(f"GSTIN - {company_gstin}")
    if place_of_supply:
        address_lines.append(f"Place of Supply {place_of_supply}")
    if company_pan:
        address_lines.append(f"PAN No - {company_pan}")

    story.append(Paragraph("<br/>".join(address_lines), style_normal))
    story.append(Spacer(1, 12))

    candidate_name = invoice_data.get("candidate_name", "")
    designation = invoice_data.get("candidate_designation", "")
    doj_str = format_date(invoice_data.get("joining_date")) if invoice_data.get("joining_date") else ""

    table_header = [
        Paragraph("<b>S.No</b>", style_center),
        Paragraph("<b>Name</b>", style_center),
        Paragraph("<b>Process</b>", style_center),
        Paragraph("<b>DOJ</b>", style_center),
        Paragraph("<b>Amount</b>", style_center),
    ]

    table_row1 = [
        Paragraph("1", style_center),
        Paragraph(candidate_name, style_normal),
        Paragraph(designation, style_center),
        Paragraph(doj_str, style_center),
        Paragraph(f"{base_amount:,.0f}", style_right_bold),
    ]

    total_row = [
        "", "",
        Paragraph("<b>Total Amount</b>", style_center),
        "",
        Paragraph(f"<b>{base_amount:,.0f}</b>", style_right_bold),
    ]

    igst_row = [
        "", "",
        Paragraph(f"<b>IGST@{igst_rate}%</b>", style_center),
        "",
        Paragraph(f"<b>{igst_amount:,.0f}</b>", style_right_bold),
    ]

    final_row = [
        "", "",
        Paragraph("<b>TOTAL PAYABLE WITH TAX</b>", style_center),
        "",
        Paragraph(f"<b>{total_amount:,.0f}</b>", style_right_bold),
    ]

    col_widths = [1.5 * cm, 4.5 * cm, 5 * cm, 3.5 * cm, 3 * cm]
    invoice_table_data = [table_header, table_row1, total_row, igst_row, final_row]

    invoice_table = Table(invoice_table_data, colWidths=col_widths)
    invoice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, 0), 0.5, colors.black),
        ("GRID", (0, 1), (-1, 1), 0.5, colors.black),
        ("BOX", (2, 2), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (2, 2), (-1, -1), 0.5, colors.black),
        ("SPAN", (0, 2), (1, 2)),
        ("SPAN", (2, 2), (3, 2)),
        ("SPAN", (0, 3), (1, 3)),
        ("SPAN", (2, 3), (3, 3)),
        ("SPAN", (0, 4), (1, 4)),
        ("SPAN", (2, 4), (3, 4)),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 16))

    words = num_to_words(total_amount)
    story.append(Paragraph(f"<b>Amount in Words:</b> {words}", style_normal))
    story.append(Spacer(1, 20))

    signatory = invoice_data.get("authorized_signatory", "Himanshu Malik")
    sig_data = [
        [
            Paragraph("Authorized Signatory", style_normal),
            Paragraph("", style_normal),
        ],
        [
            Paragraph("", style_normal),
            Paragraph(
                f"<b>For BLACK WOODS</b><br/><br/><br/>"
                f"{signatory}<br/>Proprietor",
                style_right
            ),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[9 * cm, 8.5 * cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buf.getvalue()