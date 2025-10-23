#!/usr/bin/env python3
"""
Batch Report Generator for MTBParser
Generates CSV summary and PDF report with statistics for multiple patients
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import Counter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_generator.escat_pyramid import create_escat_pyramid, map_variant_to_escat, get_escat_color, ESCAT_LEVELS


def load_batch_reports(report_dir: Path) -> List[Dict]:
    """
    Load all MTB reports from directory structure

    Expected structure:
      report_dir/
        patient_001/complete_package.json
        patient_002/complete_package.json
        ...
    """
    reports = []

    for patient_dir in report_dir.iterdir():
        if not patient_dir.is_dir():
            continue

        json_file = patient_dir / "complete_package.json"
        if not json_file.exists():
            # Try mtb_report.json as fallback
            json_file = patient_dir / "mtb_report.json"
            if not json_file.exists():
                continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both complete_package and direct mtb_report
            if 'mtb_report' in data:
                mtb_report = data['mtb_report']
            else:
                mtb_report = data

            reports.append({
                'patient_dir': patient_dir.name,
                'json_path': str(json_file),
                'data': mtb_report
            })
        except Exception as e:
            print(f"⚠️  Error loading {json_file}: {e}")
            continue

    return reports


def generate_batch_csv(reports: List[Dict], output_path: Path):
    """Generate CSV summary with one row per variant"""

    csv_rows = []

    for report in reports:
        data = report['data']
        patient = data.get('patient', {})
        diagnosis = data.get('diagnosis', {})
        variants = data.get('variants', [])

        patient_id = patient.get('id', 'unknown')
        age = patient.get('age', '')
        sex = patient.get('sex', '')
        primary_diagnosis = diagnosis.get('primary_diagnosis', '')
        stage = diagnosis.get('stage', '')
        tmb = data.get('tmb', '')

        # If no variants, add one row with patient info
        if not variants:
            csv_rows.append({
                'Patient_ID': patient_id,
                'Age': age,
                'Sex': sex,
                'Diagnosis': primary_diagnosis,
                'Stage': stage,
                'TMB': tmb,
                'Gene': '',
                'cDNA_Change': '',
                'Protein_Change': '',
                'VAF': '',
                'Classification': '',
                'ESCAT_Level': '',
                'HGNC_Code': '',
                'Actionable': '',
                'Resistance': ''
            })
        else:
            # One row per variant
            for variant in variants:
                gene = variant.get('gene', '')
                cdna = variant.get('cdna_change', '')
                protein = variant.get('protein_change', '')
                vaf = variant.get('vaf', '')
                classification = variant.get('classification', '')
                hgnc = variant.get('gene_code', {}).get('code', '') if variant.get('gene_code') else ''

                # Map to ESCAT
                escat_level = map_variant_to_escat(variant, primary_diagnosis)

                # Determine if actionable or resistance
                actionable = 'Yes' if escat_level and escat_level.startswith(('I', 'II')) else 'No'
                resistance = 'Yes' if escat_level == 'X' else 'No'

                csv_rows.append({
                    'Patient_ID': patient_id,
                    'Age': age,
                    'Sex': sex,
                    'Diagnosis': primary_diagnosis,
                    'Stage': stage,
                    'TMB': tmb,
                    'Gene': gene,
                    'cDNA_Change': cdna,
                    'Protein_Change': protein,
                    'VAF': vaf,
                    'Classification': classification,
                    'ESCAT_Level': escat_level or '',
                    'HGNC_Code': hgnc,
                    'Actionable': actionable,
                    'Resistance': resistance
                })

    # Write CSV
    if csv_rows:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = csv_rows[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(f"✅ CSV summary: {output_path}")
        print(f"   • {len(reports)} patients")
        print(f"   • {len(csv_rows)} total variants")
    else:
        print("⚠️  No data to export to CSV")


def generate_batch_pdf(reports: List[Dict], output_path: Path, csv_path: Path = None):
    """Generate comprehensive PDF summary with statistics"""

    # Create PDF
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        fontSize=11,
        textColor=colors.HexColor('#2c5f8d'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    # Title
    elements.append(Paragraph("MOLECULAR TUMOR BOARD<br/>REPORT RIASSUNTIVO BATCH", title_style))
    elements.append(Paragraph(
        f"Generato il {datetime.now().strftime('%d/%m/%Y alle ore %H:%M')}",
        ParagraphStyle('Subtitle', fontSize=10, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=30)
    ))

    # ==== GLOBAL STATISTICS ====
    elements.append(Paragraph("📊 STATISTICHE GLOBALI", heading_style))

    total_patients = len(reports)
    total_variants = sum(len(r['data'].get('variants', [])) for r in reports)
    total_actionable = 0
    total_resistance = 0
    escat_distribution = Counter()
    gene_distribution = Counter()
    diagnosis_distribution = Counter()

    for report in reports:
        data = report['data']
        diagnosis = data.get('diagnosis', {}).get('primary_diagnosis', 'Unknown')
        diagnosis_distribution[diagnosis] += 1

        for variant in data.get('variants', []):
            gene = variant.get('gene', 'Unknown')
            gene_distribution[gene] += 1

            escat = map_variant_to_escat(variant, diagnosis)
            if escat:
                escat_distribution[escat] += 1
                if escat.startswith(('I', 'II')):
                    total_actionable += 1
                elif escat == 'X':
                    total_resistance += 1

    stats_data = [
        ["Pazienti analizzati:", str(total_patients)],
        ["Varianti totali identificate:", str(total_variants)],
        ["Varianti actionable (ESCAT I-II):", f"{total_actionable} ({total_actionable/total_variants*100:.1f}%)" if total_variants > 0 else "0"],
        ["Marcatori di resistenza (ESCAT X):", f"{total_resistance} ({total_resistance/total_variants*100:.1f}%)" if total_variants > 0 else "0"],
        ["Media varianti per paziente:", f"{total_variants/total_patients:.1f}" if total_patients > 0 else "0"],
    ]

    stats_table = Table(stats_data, colWidths=[10*cm, 5*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.8*cm))

    # ==== ESCAT DISTRIBUTION ====
    elements.append(Paragraph("🎯 DISTRIBUZIONE LIVELLI ESCAT", heading_style))

    if escat_distribution:
        escat_data = [["Livello ESCAT", "N. Varianti", "Percentuale", "Evidenza"]]

        for level in ['I-A', 'I-B', 'II-A', 'II-B', 'III-A', 'III-B', 'IV', 'X']:
            count = escat_distribution.get(level, 0)
            if count > 0:
                pct = count / total_variants * 100 if total_variants > 0 else 0
                evidence = ESCAT_LEVELS[level]['description']

                level_para = Paragraph(
                    f"<b>{level}</b>",
                    ParagraphStyle('Level', fontSize=10, alignment=TA_CENTER)
                )

                escat_data.append([level_para, str(count), f"{pct:.1f}%", evidence])

        escat_table = Table(escat_data, colWidths=[2.5*cm, 2.5*cm, 2.5*cm, 7.5*cm])

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]

        # Color code ESCAT levels
        row = 1
        for level in ['I-A', 'I-B', 'II-A', 'II-B', 'III-A', 'III-B', 'IV', 'X']:
            if escat_distribution.get(level, 0) > 0:
                level_color = get_escat_color(level)
                text_color = colors.white if level != 'IV' else colors.black
                table_style.extend([
                    ('BACKGROUND', (0, row), (0, row), level_color),
                    ('TEXTCOLOR', (0, row), (0, row), text_color),
                ])
                row += 1

        escat_table.setStyle(TableStyle(table_style))
        elements.append(escat_table)

    elements.append(Spacer(1, 0.8*cm))

    # ==== ESCAT PYRAMID ====
    elements.append(Paragraph("📈 PIRAMIDE ESCAT", heading_style))
    pyramid_elements = create_escat_pyramid(width=10*cm, include_legend=True)
    elements.extend(pyramid_elements)

    # ==== PAGE BREAK ====
    elements.append(PageBreak())

    # ==== TOP GENES ====
    elements.append(Paragraph("🧬 GENI PIÙ FREQUENTI", heading_style))

    top_genes = gene_distribution.most_common(15)
    if top_genes:
        gene_data = [["Gene", "N. Varianti", "Pazienti (%)"]]

        for gene, count in top_genes:
            pct = count / total_patients * 100 if total_patients > 0 else 0
            gene_data.append([gene, str(count), f"{pct:.1f}%"])

        gene_table = Table(gene_data, colWidths=[5*cm, 4*cm, 4*cm])
        gene_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(gene_table)

    elements.append(Spacer(1, 0.8*cm))

    # ==== DIAGNOSIS DISTRIBUTION ====
    elements.append(Paragraph("🏥 DISTRIBUZIONE DIAGNOSI", heading_style))

    if diagnosis_distribution:
        diag_data = [["Diagnosi", "N. Pazienti", "Percentuale"]]

        for diagnosis, count in diagnosis_distribution.most_common():
            pct = count / total_patients * 100 if total_patients > 0 else 0
            diag_text = diagnosis if diagnosis else "Non specificata"
            diag_data.append([diag_text[:40], str(count), f"{pct:.1f}%"])

        diag_table = Table(diag_data, colWidths=[9*cm, 3*cm, 3*cm])
        diag_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(diag_table)

    # ==== PATIENT SUMMARY TABLE ====
    elements.append(PageBreak())
    elements.append(Paragraph("👥 DETTAGLIO PER PAZIENTE", heading_style))

    patient_data = [["ID", "Età", "Sesso", "Diagnosi", "Varianti", "Actionable", "Resistenza"]]

    for report in reports:
        data = report['data']
        patient = data.get('patient', {})
        diagnosis = data.get('diagnosis', {})
        variants = data.get('variants', [])

        patient_id = patient.get('id', 'unknown')
        age = patient.get('age', '-')
        sex = patient.get('sex', '-')
        diag = diagnosis.get('primary_diagnosis') or '-'
        n_variants = len(variants)

        # Count actionable and resistance
        n_actionable = 0
        n_resistance = 0
        for variant in variants:
            escat = map_variant_to_escat(variant, diag)
            if escat and escat.startswith(('I', 'II')):
                n_actionable += 1
            elif escat == 'X':
                n_resistance += 1

        # Color code based on actionability
        patient_data.append([
            str(patient_id),
            str(age) if age != '-' else '-',
            str(sex) if sex and sex != '-' else '-',
            diag[:30] if diag != '-' else '-',
            str(n_variants),
            str(n_actionable) if n_actionable > 0 else '-',
            str(n_resistance) if n_resistance > 0 else '-'
        ])

    patient_table = Table(patient_data, colWidths=[2*cm, 1.5*cm, 1.5*cm, 5*cm, 1.8*cm, 2*cm, 2*cm])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(patient_table)

    # ==== FOOTER ====
    elements.append(Spacer(1, 1*cm))
    if csv_path:
        elements.append(Paragraph(
            f"<i>Dati dettagliati disponibili in: {csv_path.name}</i>",
            ParagraphStyle('Footer', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
        ))
    elements.append(Paragraph(
        f"<i>Report generato da MTBParser il {datetime.now().strftime('%d/%m/%Y alle ore %H:%M')}</i>",
        ParagraphStyle('Footer', fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=10)
    ))

    # Build PDF
    doc.build(elements)
    print(f"✅ PDF summary: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_report_generator.py <reports_directory> [output_directory]")
        print("\nExample:")
        print("  python3 batch_report_generator.py output/20240718 batch_reports")
        sys.exit(1)

    reports_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("batch_reports")

    if not reports_dir.exists():
        print(f"❌ Directory not found: {reports_dir}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)

    print("="*80)
    print("MTBParser - Batch Report Generator")
    print("="*80)
    print(f"\n📂 Input directory: {reports_dir}")
    print(f"📂 Output directory: {output_dir}")

    # Load reports
    print(f"\n🔍 Loading reports...")
    reports = load_batch_reports(reports_dir)

    if not reports:
        print("❌ No reports found")
        sys.exit(1)

    print(f"✅ Loaded {len(reports)} patient reports")

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Generate CSV
    print(f"\n📊 Generating CSV summary...")
    csv_path = output_dir / f"batch_summary_{timestamp}.csv"
    generate_batch_csv(reports, csv_path)

    # Generate PDF
    print(f"\n📄 Generating PDF summary...")
    pdf_path = output_dir / f"batch_summary_{timestamp}.pdf"
    generate_batch_pdf(reports, pdf_path, csv_path)

    print(f"\n✅ Batch reporting complete!")
    print(f"\n📁 Output files:")
    print(f"   • CSV: {csv_path}")
    print(f"   • PDF: {pdf_path}")


if __name__ == "__main__":
    main()
