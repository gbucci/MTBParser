#!/usr/bin/env python3
"""
Generate PDF Report from MTB Parser JSON
Usage: python3 generate_pdf_report.py <json_file> [output_pdf]
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_generator.ngs_panels import get_panel, detect_panel_from_genes
from pdf_generator.escat_pyramid import create_escat_pyramid, create_escat_legend, map_variant_to_escat, get_escat_color


def load_mtb_data(json_path: str) -> dict:
    """Load MTB data from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_pdf_report(json_path: str, output_pdf: str = None):
    """
    Generate standardized PDF report from MTB JSON data
    
    Args:
        json_path: Path to complete_package.json
        output_pdf: Output PDF path (optional)
    """
    # Load data
    data = load_mtb_data(json_path)
    mtb_report = data.get('mtb_report', {})
    
    # Extract main sections
    patient = mtb_report.get('patient', {})
    diagnosis = mtb_report.get('diagnosis', {})
    variants = mtb_report.get('variants', [])
    recommendations = mtb_report.get('recommendations', [])
    tmb = mtb_report.get('tmb')
    ngs_method = mtb_report.get('ngs_method', 'NGS Panel Sequencing')
    
    # Determine output path
    if not output_pdf:
        json_file = Path(json_path)
        output_pdf = json_file.parent / f"MTB_Report_{patient.get('id', 'unknown')}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("DISCUSSIONE COLLEGIALE<br/>MOLECULAR TUMOR BOARD", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Patient Information
    elements.append(Paragraph("ANAGRAFICA PAZIENTE", heading_style))
    patient_data = [
        ["ID Paziente:", patient.get('id') or '-'],
        ["Età:", f"{patient.get('age')} anni" if patient.get('age') else '-'],
        ["Sesso:", patient.get('sex') or '-'],
        ["Data di nascita:", patient.get('birth_date') or '-']
    ]
    
    patient_table = Table(patient_data, colWidths=[5*cm, 10*cm])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Diagnosis
    elements.append(Paragraph("DIAGNOSI", heading_style))
    diagnosis_text = diagnosis.get('primary_diagnosis') or '-'

    icd_code = '-'
    if diagnosis.get('icd_o_code'):
        code = diagnosis['icd_o_code'].get('code', '-')
        display = diagnosis['icd_o_code'].get('display', '')
        icd_code = f"{code} ({display})" if display else code

    diagnosis_data = [
        ["Diagnosi primaria:", diagnosis_text],
        ["Stadio:", diagnosis.get('stage') or '-'],
        ["Codice ICD-O:", icd_code],
        ["Istologia:", diagnosis.get('histology') or '-']
    ]
    
    diagnosis_table = Table(diagnosis_data, colWidths=[5*cm, 10*cm])
    diagnosis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(diagnosis_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # NGS Panel Information
    detected_genes = [v['gene'] for v in variants if v.get('gene')]
    panel_name = detect_panel_from_genes(detected_genes)
    panel_info = get_panel(panel_name)

    elements.append(Paragraph("TEST GENOMICI ESEGUITI", heading_style))

    # Use Paragraph for long text to enable wrapping
    methodology_text = ngs_method or panel_info['methodology']
    methodology_para = Paragraph(methodology_text, styles['Normal'])

    ngs_data = [
        ["Metodologia:", methodology_para],
        ["Panel utilizzato:", panel_name],
        ["Numero di geni:", str(len(panel_info['genes']))],
        ["Biomarker analizzati:", ", ".join(panel_info['biomarkers'])],
    ]

    # Add TMB value if available
    if tmb is not None:
        ngs_data.append(["TMB (mut/Mb):", f"{tmb}"])

    ngs_table = Table(ngs_data, colWidths=[5*cm, 10*cm])
    ngs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(ngs_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Variants Table with ESCAT levels
    if variants:
        elements.append(Paragraph("VARIANTI GENOMICHE IDENTIFICATE", heading_style))

        # Add ESCAT column
        variant_table_data = [["Gene", "cDNA", "Proteina", "VAF%", "Classificazione", "ESCAT", "HGNC"]]

        # Track ESCAT levels for pyramid
        escat_counts = {}
        diagnosis_text = diagnosis.get('primary_diagnosis', '')

        table_styles = [
            # Header styling - lighter blue
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d0d0d0'))
        ]

        for idx, variant in enumerate(variants[:20], start=1):  # Limit to 20 variants
            # Better handling of empty values
            gene = variant.get('gene') or '-'
            cdna = variant.get('cdna_change') or '-'
            protein = variant.get('protein_change') or '-'
            vaf = f"{variant['vaf']:.1f}" if variant.get('vaf') is not None else '-'
            classification = variant.get('classification') or '-'
            hgnc = variant.get('gene_code', {}).get('code', '-') if variant.get('gene_code') else '-'

            # Map to ESCAT level
            escat_level = map_variant_to_escat(variant, diagnosis_text)
            escat_display = escat_level if escat_level else '-'

            # Track ESCAT distribution
            if escat_level:
                escat_counts[escat_level] = escat_counts.get(escat_level, 0) + 1

            # Truncate long values with ellipsis
            cdna = cdna if len(cdna) <= 20 else cdna[:17] + '...'
            protein = protein if len(protein) <= 20 else protein[:17] + '...'
            classification = classification if len(classification) <= 15 else classification[:12] + '...'

            variant_table_data.append([gene, cdna, protein, vaf, classification, escat_display, hgnc])

            # Color code ESCAT cell
            if escat_level:
                escat_color = get_escat_color(escat_level)
                text_color = colors.white if escat_level not in ['IV'] else colors.black
                table_styles.extend([
                    ('BACKGROUND', (5, idx), (5, idx), escat_color),
                    ('TEXTCOLOR', (5, idx), (5, idx), text_color),
                    ('FONTNAME', (5, idx), (5, idx), 'Helvetica-Bold'),
                ])

            # Highlight actionable variants (ESCAT I or II)
            if escat_level and escat_level.startswith(('I', 'II')):
                table_styles.append(('BACKGROUND', (0, idx), (4, idx), colors.HexColor('#e8f8f5')))

            # Highlight resistance (ESCAT X)
            if escat_level == 'X':
                table_styles.append(('BACKGROUND', (0, idx), (4, idx), colors.HexColor('#fadbd8')))

        variant_table = Table(variant_table_data, colWidths=[2*cm, 2.5*cm, 2.5*cm, 1.3*cm, 2.5*cm, 1.5*cm, 1.7*cm])
        variant_table.setStyle(TableStyle(table_styles))
        elements.append(variant_table)
        
        if len(variants) > 20:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(f"<i>... e altre {len(variants)-20} varianti (vedi report completo)</i>", styles['Normal']))

        elements.append(Spacer(1, 0.5*cm))

    # Therapeutic Recommendations
    if recommendations:
        elements.append(Paragraph("RACCOMANDAZIONI TERAPEUTICHE", heading_style))
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"<b>{i}. {rec['drug'].upper()}</b><br/>"
            if rec.get('gene_target'):
                rec_text += f"Target: {rec['gene_target']}<br/>"
            if rec.get('evidence_level'):
                rec_text += f"Livello di evidenza: {rec['evidence_level']}<br/>"
            if rec.get('rationale'):
                rec_text += f"Razionale: {rec['rationale'][:200]}"
            
            elements.append(Paragraph(rec_text, styles['Normal']))
            elements.append(Spacer(1, 0.3*cm))

    # ESCAT Pyramid - show if there are variants
    if variants:
        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph("LIVELLI DI EVIDENZA CLINICA (ESCAT)", heading_style))

        # Add pyramid visualization
        pyramid_elements = create_escat_pyramid(width=10*cm, include_legend=True)
        elements.extend(pyramid_elements)

        # Show distribution if we have ESCAT data
        if escat_counts:
            elements.append(Spacer(1, 0.5*cm))
            dist_text = "<b>Distribuzione varianti per livello ESCAT:</b><br/>"
            for level in sorted(escat_counts.keys()):
                count = escat_counts[level]
                dist_text += f"• {level}: {count} variant{'e' if count > 1 else 'e'}<br/>"

            elements.append(Paragraph(dist_text, styles['Normal']))

    # Footer
    elements.append(Spacer(1, 1*cm))
    footer_text = f"<i>Report generato automaticamente da MTBParser il {datetime.now().strftime('%d/%m/%Y alle ore %H:%M')}</i>"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    print(f"✅ PDF report generated: {output_pdf}")
    return str(output_pdf)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_pdf_report.py <json_file> [output_pdf]")
        print("\nExample:")
        print("  python3 generate_pdf_report.py output/report_001/complete_package.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(json_file).exists():
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    print("="*80)
    print("MTBParser - PDF Report Generator")
    print("="*80)
    print(f"\n📄 Input: {json_file}")
    
    try:
        pdf_path = generate_pdf_report(json_file, output_pdf)
        print(f"\n✅ Success!")
        print(f"📄 PDF saved to: {pdf_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
