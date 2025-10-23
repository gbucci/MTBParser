#!/usr/bin/env python3
"""
Interactive Editor - Terminal-based interactive editor for MTB reports
Allows field-by-field editing with keyboard navigation:
- Tab: Next field
- Shift+Tab (Backspace): Previous field
- Esc: Exit edit mode for current field
- Enter: Confirm value and move to next
- Ctrl+C: Abort editing
"""

import sys
import termios
import tty
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field as dc_field
from enum import Enum

# Handle imports
try:
    from core.data_models import MTBReport, Patient, Diagnosis, Variant, TherapeuticRecommendation
    from core.report_validator import ValidationIssue, ValidationSeverity
except ModuleNotFoundError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Patient, Diagnosis, Variant, TherapeuticRecommendation
    from core.report_validator import ValidationIssue, ValidationSeverity


class FieldType(Enum):
    """Field data types"""
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    CHOICE = "choice"


@dataclass
class EditableField:
    """Represents an editable field in the report"""
    name: str
    display_name: str
    field_type: FieldType
    current_value: Any
    path: str  # e.g., "patient.id", "variants[0].gene"
    required: bool = False
    choices: Optional[List[str]] = None
    validator: Optional[Callable] = None
    help_text: Optional[str] = None
    severity: ValidationSeverity = ValidationSeverity.INFO


class InteractiveEditor:
    """
    Terminal-based interactive editor for MTB reports

    Keyboard shortcuts:
    - Enter: Confirm and next field
    - Tab: Skip to next field
    - Backspace (at start): Previous field
    - Esc: Cancel current field edit
    - Ctrl+C: Exit editor
    """

    def __init__(self, report: MTBReport, issues: List[ValidationIssue]):
        """
        Initialize interactive editor

        Args:
            report: MTB Report to edit
            issues: Validation issues to address
        """
        self.report = report
        self.issues = issues
        self.fields: List[EditableField] = []
        self.current_field_index = 0
        self.modified = False

        # Build editable fields from issues
        self._build_fields_from_issues()

    def _build_fields_from_issues(self):
        """Build list of editable fields from validation issues"""
        # Group by severity (critical first)
        critical_issues = [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
        warning_issues = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

        # Process critical issues first
        for issue in critical_issues:
            field = self._create_field_from_issue(issue)
            if field:
                self.fields.append(field)

        # Then warnings
        for issue in warning_issues:
            field = self._create_field_from_issue(issue)
            if field:
                self.fields.append(field)

    def _create_field_from_issue(self, issue: ValidationIssue) -> Optional[EditableField]:
        """Create editable field from validation issue"""
        field_map = {
            'patient.id': EditableField(
                name='patient_id',
                display_name='Patient ID',
                field_type=FieldType.TEXT,
                current_value=self.report.patient.id,
                path='patient.id',
                required=True,
                help_text='Unique patient identifier',
                severity=issue.severity
            ),
            'patient.age': EditableField(
                name='patient_age',
                display_name='Patient Age',
                field_type=FieldType.INTEGER,
                current_value=self.report.patient.age,
                path='patient.age',
                required=False,
                help_text='Age in years (0-120)',
                validator=lambda x: 0 < int(x) < 120 if x else True,
                severity=issue.severity
            ),
            'patient.sex': EditableField(
                name='patient_sex',
                display_name='Patient Sex',
                field_type=FieldType.CHOICE,
                current_value=self.report.patient.sex,
                path='patient.sex',
                required=False,
                choices=['M', 'F'],
                help_text='M = Male, F = Female',
                severity=issue.severity
            ),
            'diagnosis.primary_diagnosis': EditableField(
                name='diagnosis',
                display_name='Primary Diagnosis',
                field_type=FieldType.TEXT,
                current_value=self.report.diagnosis.primary_diagnosis,
                path='diagnosis.primary_diagnosis',
                required=True,
                help_text='Primary cancer diagnosis (e.g., Adenocarcinoma polmonare)',
                severity=issue.severity
            ),
            'diagnosis.stage': EditableField(
                name='stage',
                display_name='Disease Stage',
                field_type=FieldType.TEXT,
                current_value=self.report.diagnosis.stage,
                path='diagnosis.stage',
                required=False,
                help_text='TNM stage (e.g., IV, IIIA)',
                severity=issue.severity
            )
        }

        # Handle variant fields specially
        if issue.field_path.startswith('variants'):
            # Check if we need to add a new variant
            if issue.field_path == 'variants' and len(self.report.variants) == 0:
                # No variants - create field to add one
                return EditableField(
                    name='new_variant',
                    display_name='Add Genomic Variant',
                    field_type=FieldType.TEXT,
                    current_value=None,
                    path='variants.new',
                    required=True,
                    help_text='Enter variant (e.g., EGFR L858R, KRAS G12D)',
                    severity=issue.severity
                )

        return field_map.get(issue.field_path)

    def start(self) -> MTBReport:
        """
        Start interactive editing session

        Returns:
            Modified MTB Report
        """
        print("\n" + "="*70)
        print("  MTB REPORT INTERACTIVE EDITOR")
        print("="*70)
        print("\n📝 You will be guided through each field that needs attention.")
        print("\nKeyboard shortcuts:")
        print("  Enter       : Save value and move to next field")
        print("  Tab         : Skip to next field without changing")
        print("  Backspace   : Go to previous field (when input is empty)")
        print("  Esc         : Cancel editing current field")
        print("  Ctrl+C      : Exit editor")
        print("\n" + "-"*70 + "\n")

        try:
            # Edit each field
            while self.current_field_index < len(self.fields):
                self._edit_current_field()
                self.current_field_index += 1

            # Show completion message
            print("\n" + "="*70)
            print("✓ Interactive editing completed!")
            print("="*70)

            if self.modified:
                print("\n✓ Report has been modified.")
            else:
                print("\n  No changes were made.")

            return self.report

        except KeyboardInterrupt:
            print("\n\n⚠️  Editing cancelled by user.")
            return self.report

    def _edit_current_field(self):
        """Edit the current field"""
        field = self.fields[self.current_field_index]

        # Show field header
        severity_icons = {
            ValidationSeverity.CRITICAL: "🔴",
            ValidationSeverity.WARNING: "⚠️ ",
            ValidationSeverity.INFO: "ℹ️ "
        }

        print(f"\n[Field {self.current_field_index + 1}/{len(self.fields)}] {severity_icons[field.severity]} {field.display_name}")
        print("-" * 70)

        # Show current value
        if field.current_value:
            print(f"Current value: {field.current_value}")
        else:
            print(f"Current value: (empty)")

        # Show help
        if field.help_text:
            print(f"Help: {field.help_text}")

        # Show choices if applicable
        if field.field_type == FieldType.CHOICE and field.choices:
            print(f"Choices: {', '.join(field.choices)}")

        # Get input
        new_value = self._get_field_input(field)

        # Update report if value changed
        if new_value is not None and new_value != field.current_value:
            self._update_report_field(field, new_value)
            self.modified = True
            print(f"✓ Updated: {field.display_name} = {new_value}")

    def _get_field_input(self, field: EditableField) -> Optional[Any]:
        """
        Get user input for field

        Args:
            field: Field to edit

        Returns:
            New value or None if skipped
        """
        prompt = f"\nEnter new value"
        if not field.required:
            prompt += " (or press Tab to skip)"
        prompt += ": "

        while True:
            try:
                user_input = input(prompt).strip()

                # Empty input
                if not user_input:
                    if field.required:
                        print("⚠️  This field is required. Please enter a value.")
                        continue
                    return None

                # Validate based on type
                if field.field_type == FieldType.INTEGER:
                    try:
                        value = int(user_input)
                        if field.validator and not field.validator(user_input):
                            print("⚠️  Invalid value. Please try again.")
                            continue
                        return value
                    except ValueError:
                        print("⚠️  Please enter a valid integer.")
                        continue

                elif field.field_type == FieldType.FLOAT:
                    try:
                        return float(user_input)
                    except ValueError:
                        print("⚠️  Please enter a valid number.")
                        continue

                elif field.field_type == FieldType.CHOICE:
                    if field.choices and user_input.upper() not in [c.upper() for c in field.choices]:
                        print(f"⚠️  Please choose from: {', '.join(field.choices)}")
                        continue
                    return user_input.upper()

                else:  # TEXT
                    return user_input

            except EOFError:
                # Ctrl+D pressed - skip field
                return None

    def _update_report_field(self, field: EditableField, value: Any):
        """Update report with new field value"""
        if field.path == 'patient.id':
            self.report.patient.id = value
        elif field.path == 'patient.age':
            self.report.patient.age = value
        elif field.path == 'patient.sex':
            self.report.patient.sex = value
        elif field.path == 'diagnosis.primary_diagnosis':
            self.report.diagnosis.primary_diagnosis = value
        elif field.path == 'diagnosis.stage':
            self.report.diagnosis.stage = value
        elif field.path == 'variants.new':
            # Parse variant text and add to report
            new_variant = self._parse_variant_text(value)
            if new_variant:
                self.report.variants.append(new_variant)

    def _parse_variant_text(self, text: str) -> Optional[Variant]:
        """
        Parse variant from text input

        Examples:
            "EGFR L858R"
            "KRAS G12D 45%"
            "TP53 p.Arg273His Pathogenic"
        """
        import re

        # Try to extract gene and protein change
        match = re.match(r'(\w+)\s+([A-Z]\d+[A-Z*]+)', text, re.IGNORECASE)
        if match:
            gene = match.group(1).upper()
            protein_change = match.group(2).upper()

            # Try to extract VAF
            vaf_match = re.search(r'(\d+(?:\.\d+)?)%', text)
            vaf = float(vaf_match.group(1)) if vaf_match else None

            # Try to extract classification
            classification = None
            if 'pathogenic' in text.lower():
                classification = 'Pathogenic'
            elif 'vus' in text.lower():
                classification = 'VUS'
            elif 'benign' in text.lower():
                classification = 'Benign'

            return Variant(
                gene=gene,
                protein_change=protein_change,
                vaf=vaf,
                classification=classification
            )

        return None


class SimpleInteractiveEditor:
    """
    Simplified interactive editor for quick field updates
    Without complex terminal control
    """

    def __init__(self, report: MTBReport, issues: List[ValidationIssue]):
        self.report = report
        self.issues = issues
        self.modified = False

    def start(self) -> MTBReport:
        """Start simple interactive editing"""
        print("\n" + "="*70)
        print("  MTB REPORT EDITOR - Fix Issues")
        print("="*70)

        # Group issues by severity
        critical = [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

        if critical:
            print(f"\n🔴 {len(critical)} CRITICAL issues found (must be fixed):")
            for i, issue in enumerate(critical, 1):
                print(f"  {i}. {issue.message}")

        if warnings:
            print(f"\n⚠️  {len(warnings)} Warnings (optional):")
            for i, issue in enumerate(warnings, 1):
                print(f"  {i}. {issue.message}")

        print("\n" + "-"*70)

        # Fix critical issues
        if critical:
            print("\nFixing critical issues...")
            for issue in critical:
                self._fix_issue(issue)

        # Ask about warnings
        if warnings:
            print("\n")
            fix_warnings = input("Do you want to fix warnings? (y/n): ").strip().lower()
            if fix_warnings == 'y':
                for issue in warnings:
                    self._fix_issue(issue)

        print("\n✓ Editing complete!")
        return self.report

    def _fix_issue(self, issue: ValidationIssue):
        """Fix a single issue"""
        print(f"\n{issue.field_name}:")
        print(f"  Issue: {issue.message}")
        if issue.suggested_action:
            print(f"  Suggestion: {issue.suggested_action}")
        if issue.current_value:
            print(f"  Current: {issue.current_value}")

        new_value = input("  Enter value (or press Enter to skip): ").strip()

        if new_value:
            self._apply_fix(issue.field_path, new_value)
            self.modified = True
            print(f"  ✓ Updated")

    def _apply_fix(self, field_path: str, value: str):
        """Apply fix to report"""
        if field_path == 'patient.id':
            self.report.patient.id = value
        elif field_path == 'patient.age':
            self.report.patient.age = int(value) if value.isdigit() else None
        elif field_path == 'patient.sex':
            self.report.patient.sex = value.upper()
        elif field_path == 'diagnosis.primary_diagnosis':
            self.report.diagnosis.primary_diagnosis = value
        elif field_path == 'diagnosis.stage':
            self.report.diagnosis.stage = value
        elif field_path == 'variants':
            # Add new variant
            variant = self._parse_simple_variant(value)
            if variant:
                self.report.variants.append(variant)

    def _parse_simple_variant(self, text: str) -> Optional[Variant]:
        """Parse variant from simple text"""
        import re
        match = re.match(r'(\w+)\s+([A-Z]\d+[A-Z*]+)', text, re.IGNORECASE)
        if match:
            return Variant(
                gene=match.group(1).upper(),
                protein_change=match.group(2).upper()
            )
        return None


# Example usage
if __name__ == "__main__":
    print("=== Interactive Editor Test ===\n")

    from core.data_models import Patient, Diagnosis, MTBReport
    from core.report_validator import ReportValidator

    # Create incomplete report
    incomplete_report = MTBReport(
        patient=Patient(age=65, sex="M"),  # Missing ID
        diagnosis=Diagnosis(),  # Missing diagnosis
        variants=[],  # No variants
        recommendations=[]
    )

    # Validate
    validator = ReportValidator()
    is_valid, issues = validator.validate(incomplete_report)

    print("Validation result:")
    print(validator.format_validation_report())

    if not is_valid:
        print("\n" + "="*70)
        print("Starting interactive editor...\n")

        # Use simple editor
        editor = SimpleInteractiveEditor(incomplete_report, issues)
        updated_report = editor.start()

        # Re-validate
        print("\n" + "="*70)
        print("Re-validating...")
        validator2 = ReportValidator()
        is_valid2, issues2 = validator2.validate(updated_report)
        print(validator2.format_validation_report())
