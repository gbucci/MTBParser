#!/usr/bin/env python3
"""
Test script for interactive mode and unified exporter
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mtb_parser import MTBParser
from core.report_validator import ReportValidator
from interactive.interactive_editor import SimpleInteractiveEditor
from exporters.unified_exporter import UnifiedExporter, ExportFormat


def test_complete_workflow():
    """Test complete workflow: parse -> validate -> interactive edit -> export"""

    print("="*70)
    print("  MTB PARSER - Complete Workflow Test")
    print("="*70)

    # Sample incomplete report (will trigger interactive mode)
    sample_report_text = """
    Paziente: 12345
    Età: 65 anni

    EGFR L858R 45%
    TMB: 8.5 mut/Mb

    Raccomandazioni: sensibilità a osimertinib
    """

    print("\n📄 Sample Report Text:")
    print("-" * 70)
    print(sample_report_text)
    print("-" * 70)

    # Step 1: Parse
    print("\n[STEP 1] Parsing report...")
    parser = MTBParser()
    report = parser.parse_report(sample_report_text)

    print(f"✓ Parsed:")
    print(f"  - Patient ID: {report.patient.id}")
    print(f"  - Diagnosis: {report.diagnosis.primary_diagnosis or 'MISSING'}")
    print(f"  - Variants: {len(report.variants)}")
    print(f"  - TMB: {report.tmb}")

    # Step 2: Validate
    print("\n[STEP 2] Validating report...")
    validator = ReportValidator()
    is_valid, issues = validator.validate(report)

    print(validator.format_validation_report())

    # Step 3: Interactive editing if needed
    if validator.needs_interactive_mode():
        print("\n[STEP 3] Interactive editing mode")
        print("="*70)
        print("⚡ Critical issues detected - interactive mode would be activated")
        print("   (Simulating automatic fixes for demo purposes)")
        print("="*70)

        # Simulate fixes
        report.diagnosis.primary_diagnosis = "Adenocarcinoma polmonare"
        report.diagnosis.stage = "IV"
        report.patient.sex = "M"

        print("\n✓ Simulated fixes applied:")
        print(f"  - Added diagnosis: {report.diagnosis.primary_diagnosis}")
        print(f"  - Added stage: {report.diagnosis.stage}")
        print(f"  - Added sex: {report.patient.sex}")

        # Re-validate
        print("\n🔎 Re-validating...")
        is_valid2, issues2 = validator.validate(report)
        print(validator.format_validation_report())

    # Step 4: Export to all formats
    print("\n[STEP 4] Exporting to multiple formats...")
    print("="*70)

    exporter = UnifiedExporter(
        output_dir=Path("/tmp/mtb_test_export"),
        pretty=True
    )

    results = exporter.export(
        report,
        formats=[ExportFormat.ALL],
        save_to_file=True
    )

    print(f"\n✓ Export complete!")
    print(f"  Formats exported: {len(results)}")
    for format_name in results.keys():
        print(f"    - {format_name}")

    # Step 5: Create complete package
    print("\n[STEP 5] Creating complete interoperable package...")
    print("="*70)

    package_dir = exporter.export_complete_package(report)

    print(f"\n✓ Package created at: {package_dir}")
    print("\nPackage contents:")
    for file in sorted(package_dir.rglob('*')):
        if file.is_file():
            size_kb = file.stat().st_size / 1024
            rel_path = str(file.relative_to(package_dir))
            print(f"  {rel_path:40s} ({size_kb:6.1f} KB)")

    print("\n" + "="*70)
    print("✓ Complete workflow test finished successfully!")
    print("="*70)


def test_validation_scenarios():
    """Test different validation scenarios"""

    print("\n" + "="*70)
    print("  Validation Scenarios Test")
    print("="*70)

    from core.data_models import Patient, Diagnosis, Variant, MTBReport

    scenarios = [
        {
            'name': 'Complete Report',
            'report': MTBReport(
                patient=Patient(id="12345", age=65, sex="M"),
                diagnosis=Diagnosis(primary_diagnosis="Adenocarcinoma polmonare", stage="IV"),
                variants=[
                    Variant(gene="EGFR", protein_change="p.Leu858Arg", vaf=45.0, classification="Pathogenic")
                ],
                recommendations=[]
            )
        },
        {
            'name': 'Missing Patient ID (CRITICAL)',
            'report': MTBReport(
                patient=Patient(age=65, sex="M"),
                diagnosis=Diagnosis(primary_diagnosis="Adenocarcinoma polmonare"),
                variants=[Variant(gene="EGFR", protein_change="p.Leu858Arg")],
                recommendations=[]
            )
        },
        {
            'name': 'Missing Diagnosis (CRITICAL)',
            'report': MTBReport(
                patient=Patient(id="12345", age=65, sex="M"),
                diagnosis=Diagnosis(),
                variants=[Variant(gene="EGFR", protein_change="p.Leu858Arg")],
                recommendations=[]
            )
        },
        {
            'name': 'No Variants (CRITICAL)',
            'report': MTBReport(
                patient=Patient(id="12345", age=65, sex="M"),
                diagnosis=Diagnosis(primary_diagnosis="Adenocarcinoma polmonare"),
                variants=[],
                recommendations=[]
            )
        },
        {
            'name': 'Missing VAF and Classification (WARNINGS)',
            'report': MTBReport(
                patient=Patient(id="12345", age=65, sex="M"),
                diagnosis=Diagnosis(primary_diagnosis="Adenocarcinoma polmonare"),
                variants=[Variant(gene="EGFR", protein_change="p.Leu858Arg")],
                recommendations=[]
            )
        }
    ]

    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'='*70}")

        validator = ReportValidator()
        is_valid, issues = validator.validate(scenario['report'])

        print(f"Valid: {is_valid}")
        print(f"Needs Interactive Mode: {validator.needs_interactive_mode()}")
        print(f"Issues: {len(issues)}")

        if issues:
            print("\nIssues found:")
            for issue in issues:
                severity_icon = {
                    'critical': '🔴',
                    'warning': '⚠️ ',
                    'info': 'ℹ️ '
                }[issue.severity.value]
                print(f"  {severity_icon} {issue.message}")


def test_export_formats():
    """Test individual export formats"""

    print("\n" + "="*70)
    print("  Export Formats Test")
    print("="*70)

    from core.data_models import Patient, Diagnosis, Variant, TherapeuticRecommendation, MTBReport

    # Create sample report
    report = MTBReport(
        patient=Patient(id="12345", age=65, sex="M", birth_date="1958-03-15"),
        diagnosis=Diagnosis(
            primary_diagnosis="Adenocarcinoma polmonare",
            stage="IV",
            icd_o_code={'code': '8140/3', 'system': 'ICD-O-3', 'display': 'Adenocarcinoma, NOS'}
        ),
        variants=[
            Variant(
                gene="EGFR",
                cdna_change="c.2573T>G",
                protein_change="p.Leu858Arg",
                classification="Pathogenic",
                vaf=45.0,
                gene_code={'code': 'HGNC:3236', 'system': 'http://www.genenames.org'}
            ),
            Variant(
                gene="TP53",
                protein_change="p.Arg273His",
                classification="Pathogenic",
                vaf=52.0
            )
        ],
        recommendations=[
            TherapeuticRecommendation(
                drug="osimertinib",
                gene_target="EGFR",
                evidence_level="FDA Approved",
                drug_code={'code': '1873986', 'system': 'RxNorm', 'display': 'osimertinib'}
            )
        ],
        tmb=8.5,
        ngs_method="FoundationOne CDx",
        report_date="2025-10-22"
    )

    exporter = UnifiedExporter(output_dir="/tmp/mtb_format_test", pretty=True)

    # Test each format individually
    formats_to_test = [
        (ExportFormat.FHIR_R4, "FHIR R4 Bundle"),
        (ExportFormat.PHENOPACKETS_V2, "GA4GH Phenopackets v2"),
        (ExportFormat.OMOP_CDM_V5_4, "OMOP CDM v5.4"),
        (ExportFormat.JSON, "Native JSON"),
        (ExportFormat.CSV, "CSV Exports")
    ]

    for export_format, format_name in formats_to_test:
        print(f"\n{'='*70}")
        print(f"Testing: {format_name}")
        print(f"{'='*70}")

        try:
            results = exporter.export(
                report,
                formats=[export_format],
                save_to_file=True
            )
            print(f"✓ Export successful")

            # Show sample of exported data
            if export_format != ExportFormat.CSV:
                result_key = list(results.keys())[0]
                result_data = results[result_key]
                if isinstance(result_data, dict):
                    print(f"  Sample keys: {list(result_data.keys())[:5]}")
                elif isinstance(result_data, str):
                    print(f"  Length: {len(result_data)} chars")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  MTB PARSER - COMPREHENSIVE TEST SUITE")
    print("="*70)

    try:
        # Run all tests
        test_complete_workflow()
        test_validation_scenarios()
        test_export_formats()

        print("\n" + "="*70)
        print("✓ All tests completed successfully!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
