#!/usr/bin/env python3
"""
Data Models for MTB Report Parser
Defines all dataclasses representing clinical and molecular entities
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Variant:
    """
    Represents a genomic variant extracted from MTB report

    Attributes:
        gene: Gene symbol (e.g., "EGFR", "ALK::EML4")
        cdna_change: cDNA nomenclature (e.g., "c.2573T>G")
        protein_change: Protein change (e.g., "p.Leu858Arg", "V600E")
        classification: Variant pathogenicity (Pathogenic, VUS, Benign, etc.)
        vaf: Variant Allele Frequency (VAF) as percentage
        raw_text: Original text where variant was extracted from
        gene_code: HGNC code information from vocabulary
    """
    gene: str
    cdna_change: Optional[str] = None
    protein_change: Optional[str] = None
    classification: Optional[str] = None
    vaf: Optional[float] = None
    raw_text: Optional[str] = None
    gene_code: Optional[Dict] = None

    def __post_init__(self):
        """Validate and normalize variant data"""
        # Normalize gene name to uppercase
        if self.gene:
            self.gene = self.gene.upper().strip()

        # Normalize classification
        if self.classification:
            self.classification = self._normalize_classification(self.classification)

    @staticmethod
    def _normalize_classification(classification: str) -> str:
        """Normalize variant classification to standard terms"""
        class_lower = classification.lower().strip()

        classification_map = {
            'patogenetica': 'Pathogenic',
            'likely pathogenic': 'Likely Pathogenic',
            'variante a significato incerto': 'VUS',
            'vus': 'VUS',
            'uncertain significance': 'VUS',
            'likely benign': 'Likely Benign',
            'benigna': 'Benign',
            'benign': 'Benign'
        }

        return classification_map.get(class_lower, classification.title())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def is_fusion(self) -> bool:
        """Check if variant is a gene fusion"""
        return '::' in self.gene or (
            self.protein_change and 'fusion' in self.protein_change.lower()
        )

    def is_actionable(self) -> bool:
        """Check if variant is actionable (has gene_code and is pathogenic)"""
        return (
            self.gene_code is not None and
            self.classification in ['Pathogenic', 'Likely Pathogenic']
        )


@dataclass
class Patient:
    """
    Patient demographic information

    Attributes:
        id: Patient identifier
        age: Age in years
        sex: Biological sex (M/F)
        birth_date: Date of birth (ISO format YYYY-MM-DD)
    """
    id: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    birth_date: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize patient data"""
        # Normalize sex
        if self.sex:
            sex_upper = self.sex.upper().strip()
            if sex_upper in ['M', 'MALE', 'MASCHIO']:
                self.sex = 'M'
            elif sex_upper in ['F', 'FEMALE', 'FEMMINA']:
                self.sex = 'F'

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def is_complete(self) -> bool:
        """Check if patient has all required fields"""
        return all([self.id, self.age, self.sex])


@dataclass
class Diagnosis:
    """
    Primary diagnosis information

    Attributes:
        primary_diagnosis: Main diagnosis text
        stage: Cancer stage (e.g., "IV", "IIIB")
        histology: Histological type
        icd_o_code: ICD-O code information from vocabulary
    """
    primary_diagnosis: Optional[str] = None
    stage: Optional[str] = None
    histology: Optional[str] = None
    icd_o_code: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def is_complete(self) -> bool:
        """Check if diagnosis has required fields"""
        return self.primary_diagnosis is not None


@dataclass
class TherapeuticRecommendation:
    """
    Therapeutic recommendation with evidence

    Attributes:
        drug: Drug name
        gene_target: Gene(s) targeted by the drug
        evidence_level: Evidence level (FDA Approved, Clinical Trial, etc.)
        clinical_trial: Clinical trial identifier if applicable
        rationale: Rationale for recommendation
        drug_code: RxNorm code information from vocabulary
    """
    drug: Optional[str] = None
    gene_target: Optional[str] = None
    evidence_level: Optional[str] = None
    clinical_trial: Optional[str] = None
    rationale: Optional[str] = None
    drug_code: Optional[Dict] = None

    def __post_init__(self):
        """Normalize drug name"""
        if self.drug:
            self.drug = self.drug.lower().strip()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def is_actionable(self) -> bool:
        """Check if recommendation is actionable (has drug and target)"""
        return self.drug is not None and self.gene_target is not None


@dataclass
class QualityMetrics:
    """
    Quality metrics for parsed MTB report

    Tracks completeness and accuracy of parsing

    Attributes:
        total_fields: Total number of expected fields
        filled_fields: Number of fields successfully filled
        completeness_pct: Percentage of fields completed
        variants_found: Number of variants extracted
        variants_with_vaf: Number of variants with VAF
        variants_classified: Number of variants with classification
        variants_with_gene_code: Number of variants with HGNC mapping
        drugs_identified: Number of drugs mentioned
        drugs_mapped: Number of drugs mapped to RxNorm
        diagnosis_mapped: Whether diagnosis was mapped to ICD-O
        patient_complete: Whether patient info is complete
        warnings: List of warnings encountered during parsing
    """
    total_fields: int = 0
    filled_fields: int = 0
    completeness_pct: float = 0.0
    variants_found: int = 0
    variants_with_vaf: int = 0
    variants_classified: int = 0
    variants_with_gene_code: int = 0
    drugs_identified: int = 0
    drugs_mapped: int = 0
    diagnosis_mapped: bool = False
    patient_complete: bool = False
    warnings: List[str] = field(default_factory=list)

    def calculate(self):
        """Calculate completeness percentage"""
        if self.total_fields > 0:
            self.completeness_pct = round((self.filled_fields / self.total_fields) * 100, 1)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def add_warning(self, warning: str):
        """Add a warning message"""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def get_summary(self) -> str:
        """Get human-readable summary"""
        summary = [
            f"Completeness: {self.completeness_pct}%",
            f"Variants: {self.variants_found} ({self.variants_with_vaf} with VAF, {self.variants_classified} classified)",
            f"Drugs: {self.drugs_identified} ({self.drugs_mapped} mapped)",
            f"Diagnosis mapped: {'Yes' if self.diagnosis_mapped else 'No'}",
            f"Patient complete: {'Yes' if self.patient_complete else 'No'}"
        ]
        if self.warnings:
            summary.append(f"Warnings: {len(self.warnings)}")
        return "\n".join(summary)


@dataclass
class MTBReport:
    """
    Complete MTB Report containing all extracted entities

    Attributes:
        patient: Patient demographic information
        diagnosis: Primary diagnosis
        variants: List of genomic variants
        recommendations: List of therapeutic recommendations
        tmb: Tumor Mutational Burden (mutations/Mb)
        ngs_method: NGS panel/method used
        report_date: Date of report (ISO format)
        raw_content: Original report text
        quality_metrics: Quality metrics for this parse
    """
    patient: Patient
    diagnosis: Diagnosis
    variants: List[Variant] = field(default_factory=list)
    recommendations: List[TherapeuticRecommendation] = field(default_factory=list)
    tmb: Optional[float] = None
    ngs_method: Optional[str] = None
    report_date: Optional[str] = None
    raw_content: Optional[str] = None
    quality_metrics: Optional[QualityMetrics] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary (recursively)"""
        return {
            'patient': self.patient.to_dict(),
            'diagnosis': self.diagnosis.to_dict(),
            'variants': [v.to_dict() for v in self.variants],
            'recommendations': [r.to_dict() for r in self.recommendations],
            'tmb': self.tmb,
            'ngs_method': self.ngs_method,
            'report_date': self.report_date,
            'quality_metrics': self.quality_metrics.to_dict() if self.quality_metrics else None
        }

    def get_actionable_variants(self) -> List[Variant]:
        """Get list of actionable variants"""
        return [v for v in self.variants if v.is_actionable()]

    def get_fusion_variants(self) -> List[Variant]:
        """Get list of gene fusions"""
        return [v for v in self.variants if v.is_fusion()]

    def has_high_tmb(self, threshold: float = 10.0) -> bool:
        """Check if TMB is high (default threshold 10 mut/Mb)"""
        return self.tmb is not None and self.tmb >= threshold

    def summary(self) -> str:
        """Get human-readable summary of report"""
        lines = [
            f"=== MTB Report Summary ===",
            f"Patient: {self.patient.id or 'Unknown'} (Age: {self.patient.age or 'Unknown'}, Sex: {self.patient.sex or 'Unknown'})",
            f"Diagnosis: {self.diagnosis.primary_diagnosis or 'Not specified'}",
            f"Variants: {len(self.variants)} total, {len(self.get_actionable_variants())} actionable",
            f"Fusions: {len(self.get_fusion_variants())}",
            f"TMB: {self.tmb if self.tmb else 'Not reported'} mut/Mb",
            f"Recommendations: {len(self.recommendations)}"
        ]

        if self.quality_metrics:
            lines.append(f"\n{self.quality_metrics.get_summary()}")

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Create sample patient
    patient = Patient(id="12345", age=65, sex="M", birth_date="1958-03-15")
    print(f"Patient complete: {patient.is_complete()}")

    # Create sample diagnosis
    diagnosis = Diagnosis(
        primary_diagnosis="Adenocarcinoma polmonare",
        stage="IV",
        histology="Adenocarcinoma"
    )

    # Create sample variants
    variant1 = Variant(
        gene="EGFR",
        cdna_change="c.2573T>G",
        protein_change="p.Leu858Arg",
        classification="Pathogenic",
        vaf=45.0
    )

    variant2 = Variant(
        gene="ALK::EML4",
        protein_change="fusion",
        classification="Pathogenic"
    )

    print(f"Variant 1 is fusion: {variant1.is_fusion()}")
    print(f"Variant 2 is fusion: {variant2.is_fusion()}")

    # Create sample recommendation
    recommendation = TherapeuticRecommendation(
        drug="osimertinib",
        gene_target="EGFR",
        evidence_level="FDA Approved"
    )

    # Create complete report
    report = MTBReport(
        patient=patient,
        diagnosis=diagnosis,
        variants=[variant1, variant2],
        recommendations=[recommendation],
        tmb=8.5
    )

    print(f"\n{report.summary()}")
    print(f"\nActionable variants: {len(report.get_actionable_variants())}")
    print(f"High TMB: {report.has_high_tmb()}")
