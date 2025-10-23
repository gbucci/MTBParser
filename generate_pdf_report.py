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
        ["ID Paziente:", patient.get('id', 'N/A')],
        ["Età:", f"{patient.get('age', 'N/A')} anni" if patient.get('age') else 'N/A'],
        ["Sesso:", patient.get('sex', 'N/A')],
        ["Data di nascita:", patient.get('birth_date', 'N/A')]
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
    diagnosis_text = diagnosis.get('primary_diagnosis', 'Non specificata')
    if diagnosis.get('stage'):
        diagnosis_text += f" - Stadio {diagnosis['stage']}"
    
    diagnosis_data = [
        ["Diagnosi primaria:", diagnosis_text],
        ["Codice ICD-O:", diagnosis.get('icd_o_code', {}).get('code', 'N/A') if diagnosis.get('icd_o_code') else 'N/A'],
        ["Istologia:", diagnosis.get('histology', 'N/A')]
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
    ngs_data = [
        ["Metodologia:", ngs_method or panel_info['methodology']],
        ["Panel utilizzato:", panel_name],
        ["Numero di geni:", str(len(panel_info['genes']))],
        ["Biomarker analizzati:", ", ".join(panel_info['biomarkers'])]
    ]
    
    ngs_table = Table(ngs_data, colWidths=[5*cm, 10*cm])
    ngs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(ngs_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Variants Table
    if variants:
        elements.append(Paragraph("VARIANTI GENOMICHE IDENTIFICATE", heading_style))
        
        variant_table_data = [["Gene", "cDNA", "Proteina", "VAF%", "Classificazione", "HGNC"]]
        
        for variant in variants[:20]:  # Limit to 20 variants
            variant_table_data.append([
                variant.get('gene') or '',
                (variant.get('cdna_change') or '')[:20],
                (variant.get('protein_change') or '')[:20],
                str(variant.get('vaf', '')) if variant.get('vaf') else '',
                (variant.get('classification') or '')[:15],
                (variant.get('gene_code', {}).get('code') or '')[:15] if variant.get('gene_code') else ''
            ])
        
        variant_table = Table(variant_table_data, colWidths=[2.5*cm, 3*cm, 3*cm, 1.5*cm, 3*cm, 2*cm])
        variant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(variant_table)
        
        if len(variants) > 20:
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(f"<i>... e altre {len(variants)-20} varianti (vedi report completo)</i>", styles['Normal']))
        
        elements.append(Spacer(1, 0.5*cm))
    
    # TMB
    if tmb:
        elements.append(Paragraph("TUMOR MUTATIONAL BURDEN (TMB)", heading_style))
        tmb_data = [["TMB:", f"{tmb} mut/Mb"]]
        tmb_table = Table(tmb_data, colWidths=[5*cm, 10*cm])
        tmb_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(tmb_table)
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
