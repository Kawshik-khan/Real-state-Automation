import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_pdf(filename, title, subtitle, category, sections):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E1B4B'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#6D28D9'),
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    story = []

    story.append(Paragraph("GLG ASSETS LTD. — REAL ESTATE DEVELOPERS", subtitle_style))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"<b>Category:</b> {category} | <b>Status:</b> Active (RAG Knowledge Base Ready) | <b>Year:</b> 2026", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#8B5CF6'), spaceAfter=10))

    for sec in sections:
        if 'heading' in sec:
            story.append(Paragraph(sec['heading'], section_heading))
        if 'content' in sec:
            story.append(Paragraph(sec['content'], body_style))
        if 'table' in sec:
            t = Table(sec['table'], colWidths=sec.get('colWidths', [130, 120, 160, 110]))
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E1B4B')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 5),
                ('TOPPADDING', (0,0), (-1,0), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
                ('FONTSIZE', (0,1), (-1,-1), 8.5),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=10, spaceAfter=6))
    story.append(Paragraph("<i>GLG Assets Ltd. | Phone: +880 1700-000000 | Email: info@glgassets.bd | Website: https://glgassets.bd</i>", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1)))

    doc.build(story)
    print(f"SUCCESS: Created {filename}")

def generate_all_pdfs():
    # 1. Legal & Compliance PDF
    create_pdf(
        "GLG_Legal_and_Compliance_Guide.pdf",
        "Official Legal & Compliance Documentation",
        "GLG ASSETS REAL ESTATE LEGAL AFFAIRS",
        "Legal & Compliance",
        [
            {
                "heading": "1. RAJUK Approval & Freehold Land Title Verification",
                "content": "All GLG Assets projects (including GLG Gulshan Heights, Banani Crest, and Grand Residency) possess 100% verified freehold land titles, clean mutation certificates, and official RAJUK plan approvals. Every purchaser receives a guaranteed clear title deed upon completion of payment."
            },
            {
                "heading": "2. Land Registration & Transfer Duties",
                "content": "Property registration duties, stamp duties, local government taxes, and gain taxes are calculated according to official government tariff schedules. GLG Assets provides complete legal assistance for deed registration at the Sub-Registry Office."
            },
            {
                "heading": "3. Mandatory Compliance & Environmental Approvals",
                "content": "GLG Assets projects strictly comply with the Bangladesh National Building Code (BNBC), Fire Service NOC guidelines, Civil Aviation height clearances, and Department of Environment NOC approvals."
            }
        ]
    )

    # 2. Governance & Policies PDF
    create_pdf(
        "GLG_Company_Governance_and_Policies.pdf",
        "Company Governance & Customer Refund Policies",
        "GLG ASSETS CORPORATE GOVERNANCE",
        "Governance & Policies",
        [
            {
                "heading": "1. Booking Cancellation & Refund Policy",
                "content": "In the event a customer requests booking cancellation prior to installment agreement execution, GLG Assets processes refunds within 45 working days with a minimal 5% administrative processing deduction."
            },
            {
                "heading": "2. Property Handover Guarantee & Timeline",
                "content": "GLG Assets guarantees on-time property handover as specified in the agreement. In case of unexpected delay beyond the grace period, GLG Assets pays compensation interest to the buyer per month as detailed in the purchase contract."
            },
            {
                "heading": "3. Building Maintenance & Apartment Owners Association",
                "content": "Upon handover, GLG Assets assists in forming the Apartment Owners Association and manages facility operations (generator, elevator, security) for 12 months free of management service fee."
            }
        ]
    )

    # 3. Property Details PDF
    create_pdf(
        "GLG_Gulshan_Heights_Property_Details.pdf",
        "GLG Gulshan Heights — Architectural Specifications & Floor Plans",
        "GLG ASSETS LUXURY RESIDENTIAL SERIES",
        "Property Details",
        [
            {
                "heading": "1. Architectural & Structural Overview",
                "content": "GLG Gulshan Heights is a 14-storey architectural masterpiece located at Road 44, Gulshan-2, Dhaka. Built on a 15-katha freehold plot, it features earthquake-resistant RCC frame structure (Zone 3 compliance) and double-glazed soundproof glass facade."
            },
            {
                "heading": "2. Unit Configurations & Square Footage",
                "table": [
                    ["Unit Type", "Size (Sq Ft)", "Bedrooms", "Balconies", "Parking Slots"],
                    ["Type A (Corner)", "2,450 sqft", "4 BHK + Servant", "4 Balconies", "2 Car Slots"],
                    ["Type B (Front View)", "2,150 sqft", "3 BHK + Servant", "3 Balconies", "2 Car Slots"],
                    ["Type C (Executive)", "1,850 sqft", "3 BHK", "3 Balconies", "1 Car Slot"]
                ]
            },
            {
                "heading": "3. VIP Amenities & Facilities",
                "content": "Features include rooftop infinity swimming pool, European-fitted gym, community lounge hall, 100% full generator power backup, 3 high-speed Mitsubishi elevators, and 24/7 smart biometric security control."
            }
        ]
    )

    # 4. Pricing & Payment Plans PDF
    create_pdf(
        "GLG_Pricing_and_Payment_Plans_2026.pdf",
        "Official Pricing Schedule & Flexible Payment Plans (2026)",
        "GLG ASSETS SALES & FINANCIAL SERVICES",
        "Pricing & Payment",
        [
            {
                "heading": "1. Price List & Square Feet Rate Schedule",
                "table": [
                    ["Project Name", "Price per Sq Ft", "Starting Total Price", "Down Payment (20%)"],
                    ["GLG Gulshan Heights", "BDT 10,000 / sqft", "BDT 1.85 Crore", "BDT 37 Lakhs"],
                    ["GLG Banani Crest", "BDT 9,500 / sqft", "BDT 1.52 Crore", "BDT 30.4 Lakhs"],
                    ["GLG Grand Residency", "BDT 7,200 / sqft", "BDT 90 Lakhs", "BDT 18 Lakhs"]
                ]
            },
            {
                "heading": "2. 36-Month Interest-Free Installment Plan",
                "content": "Buyers pay 20% down payment at booking agreement signing. The remaining 80% balance is distributed into 36 equal monthly installments with 0% interest."
            },
            {
                "heading": "3. Home Loan Banking Partners",
                "content": "Up to 70% home loan facility is available through DBBL, City Bank, EBL, IDLC Finance, and BRAC Bank with expedited 7-day fast-track processing for GLG Assets clients."
            }
        ]
    )

if __name__ == "__main__":
    generate_all_pdfs()
