#!/usr/bin/env python3
"""
CSV Exporter - Export MTB reports to CSV/TSV format
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional

# Handle imports
try:
    from core.data_models import MTBReport, Variant, TherapeuticRecommendation
except ModuleNotFoundError:
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent))
    from core.data_models import MTBReport, Variant, TherapeuticRecommendation


class CSVExporter:
    """
    Export MTB Report to CSV format (variants, recommendations)
    """

    def __init__(self, delimiter: str = ',', encoding: str = 'utf-8'):
        """
        Initialize CSV Exporter

        Args:
            delimiter: CSV delimiter (comma or tab)
            encoding: File encoding
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def export_variants_to_rows(self, report: MTBReport) -> List[Dict]:
        """
        Export variants to list of dictionaries (rows)

        Args:
            report: MTB Report

        Returns:
            List of variant dictionaries
        """
        rows = []

        for variant in report.variants:
            row = {
                'patient_id': report.patient.id or '',
                'gene': variant.gene,
                'cdna_change': variant.cdna_change or '',
                'protein_change': variant.protein_change or '',
                'classification': variant.classification or '',
                'vaf': variant.vaf if variant.vaf is not None else '',
                'hgnc_code': variant.gene_code.get('code', '') if variant.gene_code else '',
                'is_fusion': 'Yes' if variant.is_fusion() else 'No',
                'is_actionable': 'Yes' if variant.is_actionable() else 'No'
            }
            rows.append(row)

        return rows

    def export_recommendations_to_rows(self, report: MTBReport) -> List[Dict]:
        """
        Export therapeutic recommendations to list of dictionaries

        Args:
            report: MTB Report

        Returns:
            List of recommendation dictionaries
        """
        rows = []

        for rec in report.recommendations:
            row = {
                'patient_id': report.patient.id or '',
                'drug': rec.drug,
                'gene_target': rec.gene_target or '',
                'evidence_level': rec.evidence_level or '',
                'rxnorm_code': rec.drug_code.get('code', '') if rec.drug_code else '',
                'rationale': rec.rationale or ''
            }
            rows.append(row)

        return rows

    def export_patient_summary(self, report: MTBReport) -> List[Dict]:
        """
        Export patient summary as single row

        Args:
            report: MTB Report

        Returns:
            List with single patient summary dictionary
        """
        return [{
            'patient_id': report.patient.id or '',
            'age': report.patient.age or '',
            'sex': report.patient.sex or '',
            'birth_date': report.patient.birth_date or '',
            'diagnosis': report.diagnosis.primary_diagnosis or '',
            'stage': report.diagnosis.stage or '',
            'icd_o_code': report.diagnosis.icd_o_code.get('code', '') if report.diagnosis.icd_o_code else '',
            'tmb': report.tmb if report.tmb is not None else '',
            'ngs_method': report.ngs_method or '',
            'total_variants': len(report.variants),
            'actionable_variants': len(report.get_actionable_variants()),
            'total_recommendations': len(report.recommendations)
        }]

    def save_variants_csv(self, report: MTBReport, filepath: str):
        """Save variants to CSV file"""
        rows = self.export_variants_to_rows(report)

        if not rows:
            print("No variants to export")
            return

        fieldnames = list(rows[0].keys())

        with open(filepath, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def save_recommendations_csv(self, report: MTBReport, filepath: str):
        """Save recommendations to CSV file"""
        rows = self.export_recommendations_to_rows(report)

        if not rows:
            print("No recommendations to export")
            return

        fieldnames = list(rows[0].keys())

        with open(filepath, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def save_patient_summary_csv(self, report: MTBReport, filepath: str):
        """Save patient summary to CSV file"""
        rows = self.export_patient_summary(report)
        fieldnames = list(rows[0].keys())

        with open(filepath, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(rows)

    def save_complete_export(self, report: MTBReport, base_path: str):
        """
        Save all CSV exports

        Args:
            report: MTB Report
            base_path: Base path for files (e.g., 'output/patient_12345')
        """
        base = Path(base_path)
        base.mkdir(parents=True, exist_ok=True)

        # Export patient summary
        self.save_patient_summary_csv(report, base / 'patient_summary.csv')

        # Export variants
        if report.variants:
            self.save_variants_csv(report, base / 'variants.csv')

        # Export recommendations
        if report.recommendations:
            self.save_recommendations_csv(report, base / 'recommendations.csv')


# Example usage
if __name__ == "__main__":
    print("=== CSV Exporter Test ===\n")

    from core.mtb_parser import MTBParser

    # Sample report
    sample_text = """
    Paziente: 12345
    Età: 65 anni
    Sesso: M
    Data di nascita: 15/03/1958

    Diagnosi: Adenocarcinoma polmonare stadio IV

    Varianti:
    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    TP53 c.733G>A p.Gly245Ser Pathogenic 52%

    TMB: 8.5 mut/Mb

    Raccomandazioni: osimertinib per EGFR L858R
    """

    # Parse
    parser = MTBParser()
    report = parser.parse_report(sample_text)

    # Export
    exporter = CSVExporter(delimiter=',')

    # 1. Export variants
    print("1. Variants CSV:")
    variants_rows = exporter.export_variants_to_rows(report)
    for row in variants_rows:
        print(f"   {row}")

    # 2. Export recommendations
    print("\n2. Recommendations CSV:")
    rec_rows = exporter.export_recommendations_to_rows(report)
    for row in rec_rows:
        print(f"   {row}")

    # 3. Export patient summary
    print("\n3. Patient Summary CSV:")
    summary = exporter.export_patient_summary(report)
    for row in summary:
        print(f"   {row}")

    # 4. Save to files
    output_dir = "/tmp/mtb_export"
    exporter.save_complete_export(report, output_dir)
    print(f"\n4. Complete export saved to: {output_dir}")
    print(f"   Files created:")
    for file in Path(output_dir).glob('*.csv'):
        print(f"     - {file.name} ({file.stat().st_size} bytes)")
