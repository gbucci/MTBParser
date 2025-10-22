#!/usr/bin/env python3
"""
Quality Metrics Module - Advanced quality assessment for MTB parsing
Provides detailed metrics, scoring, and quality reports
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# Handle imports
try:
    from core.data_models import MTBReport, QualityMetrics
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, QualityMetrics


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    POOR = "Poor"
    CRITICAL = "Critical"


@dataclass
class DetailedQualityReport:
    """
    Comprehensive quality report with scoring and recommendations
    """
    overall_score: float = 0.0
    quality_level: str = QualityLevel.POOR.value

    # Section scores (0-100)
    patient_score: float = 0.0
    diagnosis_score: float = 0.0
    variants_score: float = 0.0
    therapeutics_score: float = 0.0

    # Detailed metrics
    total_fields_expected: int = 0
    total_fields_filled: int = 0
    completeness_pct: float = 0.0

    # Variant quality
    variants_total: int = 0
    variants_with_hgvs: int = 0
    variants_with_vaf: int = 0
    variants_classified: int = 0
    variants_actionable: int = 0
    variants_with_hgnc: int = 0

    # Mapping quality
    diagnosis_mapped: bool = False
    drugs_mapped_pct: float = 0.0
    genes_mapped_pct: float = 0.0

    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = [
            f"=== Quality Assessment Report ===",
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Quality Level: {self.quality_level}",
            f"",
            f"Section Scores:",
            f"  Patient Data: {self.patient_score:.1f}/100",
            f"  Diagnosis: {self.diagnosis_score:.1f}/100",
            f"  Variants: {self.variants_score:.1f}/100",
            f"  Therapeutics: {self.therapeutics_score:.1f}/100",
            f"",
            f"Completeness: {self.completeness_pct:.1f}% ({self.total_fields_filled}/{self.total_fields_expected} fields)",
            f"",
            f"Variant Quality:",
            f"  Total variants: {self.variants_total}",
            f"  With HGVS: {self.variants_with_hgvs}",
            f"  With VAF: {self.variants_with_vaf}",
            f"  Classified: {self.variants_classified}",
            f"  Actionable: {self.variants_actionable}",
            f"  HGNC mapped: {self.variants_with_hgnc}",
            f"",
            f"Mapping Quality:",
            f"  Diagnosis mapped: {'Yes' if self.diagnosis_mapped else 'No'}",
            f"  Drugs mapped: {self.drugs_mapped_pct:.1f}%",
            f"  Genes mapped: {self.genes_mapped_pct:.1f}%",
        ]

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:
                lines.append(f"  ❌ {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                lines.append(f"  ⚠️  {warning}")

        if self.recommendations:
            lines.append(f"\nRecommendations ({len(self.recommendations)}):")
            for rec in self.recommendations[:5]:
                lines.append(f"  💡 {rec}")

        return "\n".join(lines)


class QualityAssessor:
    """
    Advanced quality assessment for MTB reports
    """

    def __init__(self):
        """Initialize quality assessor"""
        pass

    def assess_report(self, report: MTBReport) -> DetailedQualityReport:
        """
        Perform comprehensive quality assessment

        Args:
            report: Parsed MTB Report

        Returns:
            Detailed quality report with scores and recommendations
        """
        quality_report = DetailedQualityReport()

        # 1. Assess patient data
        quality_report.patient_score = self._assess_patient(report, quality_report)

        # 2. Assess diagnosis
        quality_report.diagnosis_score = self._assess_diagnosis(report, quality_report)

        # 3. Assess variants
        quality_report.variants_score = self._assess_variants(report, quality_report)

        # 4. Assess therapeutics
        quality_report.therapeutics_score = self._assess_therapeutics(report, quality_report)

        # 5. Calculate overall metrics
        self._calculate_overall_metrics(report, quality_report)

        # 6. Calculate overall score
        quality_report.overall_score = self._calculate_overall_score(quality_report)

        # 7. Determine quality level
        quality_report.quality_level = self._determine_quality_level(quality_report.overall_score)

        # 8. Generate recommendations
        self._generate_recommendations(quality_report)

        return quality_report

    def _assess_patient(self, report: MTBReport, quality_report: DetailedQualityReport) -> float:
        """Assess patient data quality (0-100)"""
        score = 0.0
        patient = report.patient

        # ID (30 points)
        if patient.id:
            score += 30
        else:
            quality_report.errors.append("Patient ID missing")

        # Age (25 points)
        if patient.age:
            score += 25
        else:
            quality_report.warnings.append("Patient age missing")

        # Sex (25 points)
        if patient.sex:
            score += 25
        else:
            quality_report.warnings.append("Patient sex missing")

        # Birth date (20 points)
        if patient.birth_date:
            score += 20
        else:
            quality_report.warnings.append("Patient birth date missing")

        return score

    def _assess_diagnosis(self, report: MTBReport, quality_report: DetailedQualityReport) -> float:
        """Assess diagnosis quality (0-100)"""
        score = 0.0
        diagnosis = report.diagnosis

        # Primary diagnosis (40 points)
        if diagnosis.primary_diagnosis:
            score += 40
        else:
            quality_report.errors.append("Primary diagnosis missing")

        # ICD-O mapping (30 points)
        if diagnosis.icd_o_code:
            score += 30
            quality_report.diagnosis_mapped = True
        else:
            quality_report.warnings.append("Diagnosis not mapped to ICD-O")

        # Stage (20 points)
        if diagnosis.stage:
            score += 20
        else:
            quality_report.warnings.append("Cancer stage missing")

        # Histology (10 points)
        if diagnosis.histology:
            score += 10

        return score

    def _assess_variants(self, report: MTBReport, quality_report: DetailedQualityReport) -> float:
        """Assess variants quality (0-100)"""
        if not report.variants:
            quality_report.errors.append("No variants found in report")
            return 0.0

        score = 0.0
        variants = report.variants

        # Number of variants (20 points if >= 1)
        if len(variants) >= 1:
            score += 20

        # Count quality indicators
        quality_report.variants_total = len(variants)
        quality_report.variants_with_hgvs = sum(
            1 for v in variants if v.protein_change or v.cdna_change
        )
        quality_report.variants_with_vaf = sum(1 for v in variants if v.vaf is not None)
        quality_report.variants_classified = sum(1 for v in variants if v.classification)
        quality_report.variants_actionable = len(report.get_actionable_variants())
        quality_report.variants_with_hgnc = sum(1 for v in variants if v.gene_code)

        # HGVS nomenclature (20 points)
        hgvs_pct = (quality_report.variants_with_hgvs / len(variants)) * 100
        score += (hgvs_pct / 100) * 20

        if hgvs_pct < 50:
            quality_report.warnings.append("Less than 50% of variants have HGVS nomenclature")

        # VAF (20 points)
        vaf_pct = (quality_report.variants_with_vaf / len(variants)) * 100
        score += (vaf_pct / 100) * 20

        if vaf_pct < 50:
            quality_report.warnings.append("Less than 50% of variants have VAF")

        # Classification (20 points)
        class_pct = (quality_report.variants_classified / len(variants)) * 100
        score += (class_pct / 100) * 20

        if class_pct < 50:
            quality_report.warnings.append("Less than 50% of variants are classified")

        # HGNC mapping (20 points)
        hgnc_pct = (quality_report.variants_with_hgnc / len(variants)) * 100
        quality_report.genes_mapped_pct = hgnc_pct
        score += (hgnc_pct / 100) * 20

        if hgnc_pct < 80:
            quality_report.warnings.append("Less than 80% of genes mapped to HGNC")

        return score

    def _assess_therapeutics(self, report: MTBReport, quality_report: DetailedQualityReport) -> float:
        """Assess therapeutic recommendations quality (0-100)"""
        if not report.recommendations:
            quality_report.warnings.append("No therapeutic recommendations found")
            return 50.0  # Not critical if no variants are actionable

        score = 0.0
        recommendations = report.recommendations

        # Has recommendations (30 points)
        score += 30

        # Drug mapping (40 points)
        drugs_mapped = sum(1 for r in recommendations if r.drug_code)
        drugs_mapped_pct = (drugs_mapped / len(recommendations)) * 100
        quality_report.drugs_mapped_pct = drugs_mapped_pct
        score += (drugs_mapped_pct / 100) * 40

        if drugs_mapped_pct < 80:
            quality_report.warnings.append("Less than 80% of drugs mapped to RxNorm")

        # Gene targets (20 points)
        with_targets = sum(1 for r in recommendations if r.gene_target)
        target_pct = (with_targets / len(recommendations)) * 100
        score += (target_pct / 100) * 20

        # Evidence level (10 points)
        with_evidence = sum(1 for r in recommendations if r.evidence_level)
        evidence_pct = (with_evidence / len(recommendations)) * 100
        score += (evidence_pct / 100) * 10

        return score

    def _calculate_overall_metrics(self, report: MTBReport, quality_report: DetailedQualityReport):
        """Calculate overall completeness metrics"""
        # Count expected vs filled fields
        expected_fields = [
            'patient.id', 'patient.age', 'patient.sex', 'patient.birth_date',
            'diagnosis.primary_diagnosis', 'diagnosis.stage', 'diagnosis.icd_o_code',
            'tmb'
        ]

        filled = 0
        if report.patient.id: filled += 1
        if report.patient.age: filled += 1
        if report.patient.sex: filled += 1
        if report.patient.birth_date: filled += 1
        if report.diagnosis.primary_diagnosis: filled += 1
        if report.diagnosis.stage: filled += 1
        if report.diagnosis.icd_o_code: filled += 1
        if report.tmb: filled += 1

        quality_report.total_fields_expected = len(expected_fields)
        quality_report.total_fields_filled = filled
        quality_report.completeness_pct = (filled / len(expected_fields)) * 100

    def _calculate_overall_score(self, quality_report: DetailedQualityReport) -> float:
        """Calculate weighted overall score"""
        weights = {
            'patient': 0.20,
            'diagnosis': 0.25,
            'variants': 0.35,
            'therapeutics': 0.20
        }

        overall = (
            quality_report.patient_score * weights['patient'] +
            quality_report.diagnosis_score * weights['diagnosis'] +
            quality_report.variants_score * weights['variants'] +
            quality_report.therapeutics_score * weights['therapeutics']
        )

        return round(overall, 1)

    @staticmethod
    def _determine_quality_level(score: float) -> str:
        """Determine quality level from score"""
        if score >= 90:
            return QualityLevel.EXCELLENT.value
        elif score >= 75:
            return QualityLevel.GOOD.value
        elif score >= 60:
            return QualityLevel.ACCEPTABLE.value
        elif score >= 40:
            return QualityLevel.POOR.value
        else:
            return QualityLevel.CRITICAL.value

    def _generate_recommendations(self, quality_report: DetailedQualityReport):
        """Generate actionable recommendations"""
        # Patient data recommendations
        if quality_report.patient_score < 80:
            quality_report.recommendations.append(
                "Improve patient data completeness (ID, age, sex, birth date)"
            )

        # Diagnosis recommendations
        if not quality_report.diagnosis_mapped:
            quality_report.recommendations.append(
                "Map diagnosis to ICD-O codes for better interoperability"
            )

        # Variant recommendations
        if quality_report.variants_with_hgvs < quality_report.variants_total:
            quality_report.recommendations.append(
                "Use HGVS nomenclature (c./p.) for all variants"
            )

        if quality_report.variants_with_vaf < quality_report.variants_total * 0.8:
            quality_report.recommendations.append(
                "Include VAF (Variant Allele Frequency) for variants when available"
            )

        if quality_report.genes_mapped_pct < 90:
            quality_report.recommendations.append(
                "Verify gene symbols match HGNC nomenclature"
            )

        # Therapeutic recommendations
        if quality_report.drugs_mapped_pct < 80:
            quality_report.recommendations.append(
                "Use standard drug names mappable to RxNorm"
            )

        # Overall recommendations
        if quality_report.overall_score < 60:
            quality_report.recommendations.append(
                "Review report format to ensure all key fields are extractable"
            )


# Example usage
if __name__ == "__main__":
    print("=== Quality Metrics Test ===\n")

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

    Raccomandazioni: osimertinib
    """

    # Parse report
    parser = MTBParser()
    report = parser.parse_report(sample_text)

    # Assess quality
    assessor = QualityAssessor()
    quality_report = assessor.assess_report(report)

    # Display
    print(quality_report.get_summary())

    print("\n=== JSON Export ===")
    print(json.dumps(quality_report.to_dict(), indent=2))
