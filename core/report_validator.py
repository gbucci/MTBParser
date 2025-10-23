#!/usr/bin/env python3
"""
Report Validator - Validates MTB reports and identifies missing/incomplete data
Triggers interactive mode when critical fields are missing
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Handle imports
try:
    from core.data_models import MTBReport, Patient, Diagnosis, Variant
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Patient, Diagnosis, Variant


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"  # Triggers interactive mode automatically
    WARNING = "warning"    # Shows warning but allows continuation
    INFO = "info"         # Informational only


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    field_path: str
    field_name: str
    severity: ValidationSeverity
    message: str
    current_value: Optional[str] = None
    suggested_action: Optional[str] = None


class ReportValidator:
    """
    Validates MTB reports and identifies incomplete/missing data

    Critical fields (trigger interactive mode if missing):
    - At least one diagnosis
    - At least one variant or marker
    - Patient ID

    Important fields (warnings):
    - Patient age, sex
    - Variant VAF
    - Variant classification
    """

    # Define required fields
    CRITICAL_FIELDS = {
        'diagnosis': 'At least one diagnosis must be present',
        'variants': 'At least one genomic variant must be identified',
        'patient_id': 'Patient ID is required for data tracking'
    }

    IMPORTANT_FIELDS = {
        'patient.age': 'Patient age helps with treatment decisions',
        'patient.sex': 'Patient sex is important for genomic analysis',
        'diagnosis.stage': 'Disease stage guides therapeutic strategy',
        'variants.vaf': 'Variant Allele Frequency indicates clonality',
        'variants.classification': 'Variant classification indicates pathogenicity'
    }

    def __init__(self):
        """Initialize validator"""
        self.issues: List[ValidationIssue] = []

    def validate(self, report: MTBReport) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate MTB report

        Args:
            report: Parsed MTB Report

        Returns:
            Tuple of (is_valid, list_of_issues)
            is_valid is False if any CRITICAL issues found
        """
        self.issues = []

        # Validate patient info
        self._validate_patient(report.patient)

        # Validate diagnosis (CRITICAL)
        self._validate_diagnosis(report.diagnosis)

        # Validate variants (CRITICAL)
        self._validate_variants(report.variants)

        # Validate recommendations
        self._validate_recommendations(report)

        # Check if any critical issues
        has_critical = any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)

        return (not has_critical, self.issues)

    def _validate_patient(self, patient: Patient):
        """Validate patient information"""
        # Patient ID (CRITICAL)
        if not patient.id or patient.id.strip() == "":
            self.issues.append(ValidationIssue(
                field_path="patient.id",
                field_name="Patient ID",
                severity=ValidationSeverity.CRITICAL,
                message="Patient ID is missing",
                current_value=None,
                suggested_action="Enter a unique patient identifier"
            ))

        # Age (WARNING)
        if not patient.age:
            self.issues.append(ValidationIssue(
                field_path="patient.age",
                field_name="Patient Age",
                severity=ValidationSeverity.WARNING,
                message="Patient age not found",
                current_value=None,
                suggested_action="Enter patient age in years"
            ))

        # Sex (WARNING)
        if not patient.sex:
            self.issues.append(ValidationIssue(
                field_path="patient.sex",
                field_name="Patient Sex",
                severity=ValidationSeverity.WARNING,
                message="Patient sex not specified",
                current_value=None,
                suggested_action="Enter M or F"
            ))
        elif patient.sex not in ['M', 'F']:
            self.issues.append(ValidationIssue(
                field_path="patient.sex",
                field_name="Patient Sex",
                severity=ValidationSeverity.WARNING,
                message=f"Invalid sex value: {patient.sex}",
                current_value=patient.sex,
                suggested_action="Enter M or F"
            ))

    def _validate_diagnosis(self, diagnosis: Diagnosis):
        """Validate diagnosis (CRITICAL)"""
        if not diagnosis.primary_diagnosis or diagnosis.primary_diagnosis.strip() == "":
            self.issues.append(ValidationIssue(
                field_path="diagnosis.primary_diagnosis",
                field_name="Primary Diagnosis",
                severity=ValidationSeverity.CRITICAL,
                message="No diagnosis found in report",
                current_value=None,
                suggested_action="Enter the primary cancer diagnosis"
            ))

        # Stage (WARNING)
        if diagnosis.primary_diagnosis and not diagnosis.stage:
            self.issues.append(ValidationIssue(
                field_path="diagnosis.stage",
                field_name="Disease Stage",
                severity=ValidationSeverity.WARNING,
                message="Disease stage not specified",
                current_value=None,
                suggested_action="Enter stage (e.g., IV, IIIA)"
            ))

        # ICD-O mapping (INFO)
        if diagnosis.primary_diagnosis and not diagnosis.icd_o_code:
            self.issues.append(ValidationIssue(
                field_path="diagnosis.icd_o_code",
                field_name="ICD-O Code",
                severity=ValidationSeverity.INFO,
                message="Diagnosis not mapped to ICD-O standard code",
                current_value=diagnosis.primary_diagnosis,
                suggested_action="Diagnosis will be exported with text only"
            ))

    def _validate_variants(self, variants: List[Variant]):
        """Validate genomic variants (CRITICAL if none found)"""
        if not variants or len(variants) == 0:
            self.issues.append(ValidationIssue(
                field_path="variants",
                field_name="Genomic Variants",
                severity=ValidationSeverity.CRITICAL,
                message="No genomic variants or alterations found",
                current_value=None,
                suggested_action="Enter at least one genomic variant (e.g., EGFR L858R)"
            ))
            return

        # Validate each variant
        for i, variant in enumerate(variants):
            variant_id = f"variants[{i}]"

            # Gene name required
            if not variant.gene:
                self.issues.append(ValidationIssue(
                    field_path=f"{variant_id}.gene",
                    field_name=f"Variant {i+1} Gene",
                    severity=ValidationSeverity.WARNING,
                    message=f"Variant {i+1} missing gene name",
                    current_value=None,
                    suggested_action="Enter gene symbol (e.g., EGFR, KRAS)"
                ))

            # VAF (WARNING if missing)
            if variant.vaf is None and not variant.is_fusion():
                self.issues.append(ValidationIssue(
                    field_path=f"{variant_id}.vaf",
                    field_name=f"Variant {i+1} VAF",
                    severity=ValidationSeverity.WARNING,
                    message=f"Variant {variant.gene} missing VAF (Variant Allele Frequency)",
                    current_value=None,
                    suggested_action="Enter VAF percentage (e.g., 45.0)"
                ))

            # Classification (WARNING if missing)
            if not variant.classification:
                self.issues.append(ValidationIssue(
                    field_path=f"{variant_id}.classification",
                    field_name=f"Variant {i+1} Classification",
                    severity=ValidationSeverity.WARNING,
                    message=f"Variant {variant.gene} missing pathogenicity classification",
                    current_value=None,
                    suggested_action="Enter classification (Pathogenic, VUS, Benign)"
                ))

            # HGNC mapping (INFO)
            if variant.gene and not variant.gene_code:
                self.issues.append(ValidationIssue(
                    field_path=f"{variant_id}.gene_code",
                    field_name=f"Variant {i+1} HGNC Code",
                    severity=ValidationSeverity.INFO,
                    message=f"Gene {variant.gene} not mapped to HGNC",
                    current_value=variant.gene,
                    suggested_action="Gene may not be in standard nomenclature"
                ))

    def _validate_recommendations(self, report: MTBReport):
        """Validate therapeutic recommendations"""
        # Check for actionable variants without recommendations
        actionable_variants = report.get_actionable_variants()

        if len(actionable_variants) > 0 and len(report.recommendations) == 0:
            self.issues.append(ValidationIssue(
                field_path="recommendations",
                field_name="Therapeutic Recommendations",
                severity=ValidationSeverity.WARNING,
                message=f"Found {len(actionable_variants)} actionable variants but no therapeutic recommendations",
                current_value=None,
                suggested_action="Add therapeutic recommendations for actionable variants"
            ))

    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get only critical issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]

    def get_warning_issues(self) -> List[ValidationIssue]:
        """Get only warning issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]

    def get_info_issues(self) -> List[ValidationIssue]:
        """Get only info issues"""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]

    def needs_interactive_mode(self) -> bool:
        """Check if interactive mode should be triggered"""
        return len(self.get_critical_issues()) > 0

    def format_validation_report(self) -> str:
        """Format validation issues as human-readable report"""
        if not self.issues:
            return "✓ Report validation passed - no issues found"

        report_lines = ["=== MTB Report Validation ===\n"]

        # Critical issues
        critical = self.get_critical_issues()
        if critical:
            report_lines.append(f"🔴 CRITICAL Issues ({len(critical)}):")
            for issue in critical:
                report_lines.append(f"  • {issue.message}")
                report_lines.append(f"    Field: {issue.field_name}")
                if issue.suggested_action:
                    report_lines.append(f"    Action: {issue.suggested_action}")
            report_lines.append("")

        # Warnings
        warnings = self.get_warning_issues()
        if warnings:
            report_lines.append(f"⚠️  Warnings ({len(warnings)}):")
            for issue in warnings:
                report_lines.append(f"  • {issue.message}")
                if issue.suggested_action:
                    report_lines.append(f"    Suggestion: {issue.suggested_action}")
            report_lines.append("")

        # Info
        info = self.get_info_issues()
        if info:
            report_lines.append(f"ℹ️  Info ({len(info)}):")
            for issue in info:
                report_lines.append(f"  • {issue.message}")
            report_lines.append("")

        # Summary
        if critical:
            report_lines.append("⚡ Interactive editing mode will be activated to fix critical issues.")

        return "\n".join(report_lines)


# Example usage
if __name__ == "__main__":
    print("=== Report Validator Test ===\n")

    from core.data_models import Patient, Diagnosis, Variant, MTBReport

    # Test 1: Complete report (should pass)
    print("Test 1: Complete report")
    complete_report = MTBReport(
        patient=Patient(id="12345", age=65, sex="M"),
        diagnosis=Diagnosis(primary_diagnosis="Adenocarcinoma polmonare", stage="IV"),
        variants=[
            Variant(gene="EGFR", protein_change="p.Leu858Arg", vaf=45.0, classification="Pathogenic")
        ],
        recommendations=[],
        tmb=8.5
    )

    validator = ReportValidator()
    is_valid, issues = validator.validate(complete_report)

    print(f"Valid: {is_valid}")
    print(validator.format_validation_report())
    print()

    # Test 2: Incomplete report (missing critical fields)
    print("\nTest 2: Incomplete report (missing critical fields)")
    incomplete_report = MTBReport(
        patient=Patient(age=65, sex="M"),  # Missing ID
        diagnosis=Diagnosis(),  # Missing diagnosis
        variants=[],  # No variants
        recommendations=[]
    )

    validator2 = ReportValidator()
    is_valid2, issues2 = validator2.validate(incomplete_report)

    print(f"Valid: {is_valid2}")
    print(f"Needs interactive mode: {validator2.needs_interactive_mode()}")
    print(validator2.format_validation_report())
