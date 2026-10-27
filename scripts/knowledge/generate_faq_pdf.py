import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_faq_pdf(output_filename="GLG_Assets_FAQ_2026.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E1B4B'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#6D28D9'),
        spaceAfter=15
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=6
    )

    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=4
    )

    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("GLG ASSETS LTD. — REAL ESTATE DEVELOPERS", subtitle_style))
    story.append(Paragraph("Official Frequently Asked Questions (FAQ) & Knowledge Guide", title_style))
    story.append(Paragraph("<b>Category:</b> FAQ & General Information | <b>Status:</b> Active (RAG Indexed) | <b>Year:</b> 2026", answer_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#8B5CF6'), spaceAfter=12))

    # Section 1: Overview & Projects
    story.append(Paragraph("1. Available Projects & Property Specifications", section_heading))

    story.append(Paragraph("Q1: What residential projects are currently available for booking?", question_style))
    story.append(Paragraph("<b>Answer:</b> GLG Assets offers three premier luxury residential developments in Dhaka:", answer_style))

    # Projects Table
    table_data = [
        ["Project Name", "Location", "Unit Types & Size", "Starting Price"],
        ["GLG Gulshan Heights", "Road 44, Gulshan-2", "3 BHK Condos (1,850 - 2,450 sqft)", "BDT 2.45 Crore"],
        ["GLG Banani Crest", "Block E, Banani", "3 BHK Suites (1,600 - 1,950 sqft)", "BDT 1.85 Crore"],
        ["GLG Grand Residency", "Sector 11, Uttara", "2 & 3 BHK Flats (1,250 - 1,650 sqft)", "BDT 95 Lakhs"]
    ]
    t = Table(table_data, colWidths=[130, 120, 160, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E1B4B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 2: Pricing & Payment Schedule
    story.append(Paragraph("2. Pricing, Payment Plans & Home Loans", section_heading))

    story.append(Paragraph("Q2: What is the required down payment and installment schedule?", question_style))
    story.append(Paragraph("<b>Answer:</b> Our standard payment schedule is structured as follows:<br/>"
                           "• <b>Booking Amount:</b> 20% down payment upon signing the booking agreement.<br/>"
                           "• <b>Installments:</b> 80% balance payable in equal interest-free monthly installments over 36 months.<br/>"
                           "• <b>Bank Financing:</b> Up to 70% home loan facility available through our partner financial institutions including Dutch-Bangla Bank (DBBL), City Bank, Eastern Bank Limited (EBL), and IDLC Finance.", answer_style))

    story.append(Paragraph("Q3: Are there any hidden fees or extra handover charges?", question_style))
    story.append(Paragraph("<b>Answer:</b> No hidden charges. All mandatory costs (utility connection fees, solar panel contribution, and legal deed registration duties) are clearly detailed in the booking contract before signing.", answer_style))

    # Section 3: VIP Site Visits & Amenities
    story.append(Paragraph("3. VIP Site Visits & Property Amenities", section_heading))

    story.append(Paragraph("Q4: How can I schedule a VIP site visit to GLG properties?", question_style))
    story.append(Paragraph("<b>Answer:</b> Site visits are available daily from 10:00 AM to 5:00 PM (including Fridays and holidays). You can request a visit directly through our AI Live Chat, WhatsApp, or Telegram assistant, or book online at <i>https://glgassets.bd/book-visit</i>.", answer_style))

    story.append(Paragraph("Q5: What amenities are included in GLG Gulshan Heights & Banani Crest?", question_style))
    story.append(Paragraph("<b>Answer:</b> Highlights include:<br/>"
                           "• Rooftop Infinity Swimming Pool & Landscaping Garden<br/>"
                           "• Fully Equipped Fitness Gym & Community Lounge<br/>"
                           "• 100% Full Power Backup Generator (covers all apartments & common areas)<br/>"
                           "• 3-Tier Smart Security System with 24/7 CCTV Monitoring and Biometric Access Control.", answer_style))

    # Section 4: Legal & RAJUK Approval
    story.append(Paragraph("4. Legal Title & RAJUK Approvals", section_heading))

    story.append(Paragraph("Q6: Are GLG Assets developments approved by RAJUK with legal land title?", question_style))
    story.append(Paragraph("<b>Answer:</b> Yes. All GLG Assets projects are 100% RAJUK approved with verified 100% freehold land titles, mutation land certificates, and NOC clearances from civil aviation and environmental authorities.", answer_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("<i>GLG Assets Ltd. | Contact: +880 1700-000000 | Email: info@glgassets.bd | Website: https://glgassets.bd</i>", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1)))

    doc.build(story)
    print(f"SUCCESS: PDF generated successfully: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    create_faq_pdf()
