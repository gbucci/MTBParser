#!/usr/bin/env python3
"""
MTB Parser - Main parser engine for Molecular Tumor Board reports
Combines pattern extraction, vocabulary mapping, and quality metrics
"""

import re
from datetime import datetime
from typing import Optional

# Handle imports for both module and script execution
try:
    from core.data_models import MTBReport, Patient, Diagnosis, Variant, TherapeuticRecommendation, QualityMetrics
    from core.pattern_extractors import PatternExtractors
    from vocabularies.vocabulary_loader import VocabularyLoader
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Patient, Diagnosis, Variant, TherapeuticRecommendation, QualityMetrics
    from core.pattern_extractors import PatternExtractors
    from vocabularies.vocabulary_loader import VocabularyLoader


class MTBParser:
    """
    Main MTB Report Parser

    Extracts structured clinical and molecular data from unstructured MTB report text.
    Uses controlled vocabularies (ICD-O, RxNorm, HGNC) for standardized coding.
    """

    def __init__(self, vocab_loader: Optional[VocabularyLoader] = None):
        """
        Initialize MTB Parser

        Args:
            vocab_loader: VocabularyLoader instance. If None, creates a new one.
        """
        self.vocab = vocab_loader if vocab_loader else VocabularyLoader()
        self.extractors = PatternExtractors(self.vocab)

        # NGS method patterns
        self.ngs_method_patterns = [
            r'Pannello[:\s]+([^\n]+)',
            r'Panel[:\s]+([^\n]+)',
            r'NGS[:\s]+([^\n]+)',
            r'(?:utilizzato|used)[:\s]+([^\n]+panel)',
        ]

        # Report date patterns
        self.report_date_patterns = [
            r'Data\s+report[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Report\s+date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Data[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]

    def parse_report(self, text: str) -> MTBReport:
        """
        Parse complete MTB report

        Args:
            text: Raw MTB report text

        Returns:
            MTBReport object with all extracted entities and quality metrics
        """
        # Extract all entities
        patient = self.extractors.extract_patient_info(text)
        diagnosis = self.extractors.extract_diagnosis(text)
        variants = self.extractors.extract_variants(text)
        recommendations = self.extractors.extract_therapeutic_recommendations(text)
        tmb = self.extractors.extract_tmb(text)
        ngs_method = self._extract_ngs_method(text)
        report_date = self._extract_report_date(text)

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(
            patient, diagnosis, variants, recommendations, tmb
        )

        # Create report
        report = MTBReport(
            patient=patient,
            diagnosis=diagnosis,
            variants=variants,
            recommendations=recommendations,
            tmb=tmb,
            ngs_method=ngs_method,
            report_date=report_date,
            raw_content=text,
            quality_metrics=quality_metrics
        )

        return report

    def _extract_ngs_method(self, text: str) -> Optional[str]:
        """Extract NGS panel/method information"""
        for pattern in self.ngs_method_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_report_date(self, text: str) -> Optional[str]:
        """Extract report date and convert to ISO format"""
        for pattern in self.report_date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self._convert_date_to_iso(date_str)
        return None

    @staticmethod
    def _convert_date_to_iso(date_str: str) -> str:
        """Convert DD/MM/YYYY to YYYY-MM-DD"""
        parts = re.split(r'[/-]', date_str)
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

    def _calculate_quality_metrics(
        self,
        patient: Patient,
        diagnosis: Diagnosis,
        variants: list,
        recommendations: list,
        tmb: Optional[float]
    ) -> QualityMetrics:
        """
        Calculate quality metrics for parsed report

        Tracks completeness and data quality indicators
        """
        metrics = QualityMetrics()

        # Count total expected fields
        expected_fields = [
            'patient.id', 'patient.age', 'patient.sex',
            'diagnosis.primary_diagnosis', 'diagnosis.stage',
            'tmb'
        ]
        metrics.total_fields = len(expected_fields) + len(variants) * 3  # gene, class, VAF per variant

        # Count filled fields
        filled = 0
        if patient.id:
            filled += 1
        if patient.age:
            filled += 1
        if patient.sex:
            filled += 1
        if diagnosis.primary_diagnosis:
            filled += 1
        if diagnosis.stage:
            filled += 1
        if tmb:
            filled += 1

        metrics.filled_fields = filled

        # Variant metrics
        metrics.variants_found = len(variants)
        metrics.variants_with_vaf = sum(1 for v in variants if v.vaf is not None)
        metrics.variants_classified = sum(1 for v in variants if v.classification)
        metrics.variants_with_gene_code = sum(1 for v in variants if v.gene_code)

        # Drug metrics
        metrics.drugs_identified = len(recommendations)
        metrics.drugs_mapped = sum(1 for r in recommendations if r.drug_code)

        # Diagnosis mapping
        metrics.diagnosis_mapped = diagnosis.icd_o_code is not None

        # Patient completeness
        metrics.patient_complete = patient.is_complete()

        # Warnings
        if metrics.variants_found == 0:
            metrics.add_warning("No variants extracted")
        if metrics.diagnosis_mapped is False:
            metrics.add_warning("Diagnosis not mapped to ICD-O")
        if not metrics.patient_complete:
            metrics.add_warning("Patient information incomplete")
        if tmb is None:
            metrics.add_warning("TMB not found")

        # Calculate completeness percentage
        metrics.calculate()

        return metrics


# Example usage and testing
if __name__ == "__main__":
    print("=== MTB Parser Test ===\n")

    # Initialize parser
    parser = MTBParser()

    # Sample Italian MTB report
    sample_report = """
    =====================================
    REPORT MOLECULAR TUMOR BOARD
    =====================================

    INFORMAZIONI PAZIENTE
    ID Paziente: 12345
    Età: 65 anni
    Sesso: M
    Data di nascita: 15/03/1958

    DIAGNOSI CLINICA
    Diagnosi: Adenocarcinoma polmonare stadio IV
    Istologia: Adenocarcinoma moderatamente differenziato
    Sede: Lobo superiore destro

    ANALISI GENOMICA
    Pannello: FoundationOne CDx (324 geni)
    Data report: 22/10/2025

    VARIANTI IDENTIFICATE:
    ┌─────────┬──────────────┬──────────────┬───────────────┬──────┐
    │ Gene    │ cDNA         │ Proteina     │ Classe        │ VAF  │
    ├─────────┼──────────────┼──────────────┼───────────────┼──────┤
    │ EGFR    │ c.2573T>G    │ p.Leu858Arg  │ Pathogenic    │ 45%  │
    │ TP53    │ c.733G>A     │ p.Gly245Ser  │ Pathogenic    │ 52%  │
    │ KRAS    │ -            │ G12D         │ VUS           │ 8%   │
    └─────────┴──────────────┴──────────────┴───────────────┴──────┘

    Fusioni geniche:
    - fusione ALK::EML4 (variante 3a/b)

    TMB: 8.5 mut/Mb (TMB-Medium)

    RACCOMANDAZIONI TERAPEUTICHE:
    1. Sensibilità a osimertinib (EGFR L858R - FDA approved per NSCLC)
    2. Potenziale sensibilità a alectinib (fusione ALK - FDA approved)

    Linee guida AIOM 2024 - NCCN Guidelines v3.2024
    """

    # Parse report
    report = parser.parse_report(sample_report)

    # Display results
    print(report.summary())

    print("\n=== Detailed Variant Information ===")
    for i, variant in enumerate(report.variants, 1):
        print(f"\n{i}. {variant.gene}")
        print(f"   cDNA: {variant.cdna_change or 'N/A'}")
        print(f"   Protein: {variant.protein_change or 'N/A'}")
        print(f"   Classification: {variant.classification or 'N/A'}")
        print(f"   VAF: {variant.vaf}%" if variant.vaf else "   VAF: N/A")
        print(f"   HGNC Code: {variant.gene_code.get('code') if variant.gene_code else 'Not mapped'}")
        print(f"   Fusion: {'Yes' if variant.is_fusion() else 'No'}")
        print(f"   Actionable: {'Yes' if variant.is_actionable() else 'No'}")

    print("\n=== Therapeutic Recommendations ===")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"\n{i}. {rec.drug.upper()}")
        print(f"   Target: {rec.gene_target}")
        print(f"   Evidence: {rec.evidence_level}")
        print(f"   RxNorm: {rec.drug_code.get('code') if rec.drug_code else 'Not mapped'}")

    print("\n=== Quality Metrics ===")
    print(report.quality_metrics.get_summary())

    # Test export to dict
    print("\n=== JSON Export (partial) ===")
    import json
    report_dict = report.to_dict()
    print(json.dumps({
        'patient_id': report_dict['patient']['id'],
        'diagnosis': report_dict['diagnosis']['primary_diagnosis'],
        'variants_count': len(report_dict['variants']),
        'tmb': report_dict['tmb'],
        'completeness': report_dict['quality_metrics']['completeness_pct']
    }, indent=2))
