#!/usr/bin/env python3
"""
Simple Workflow Example - Demonstrates complete MTBParser workflow
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mtb_parser import MTBParser
from core.report_validator import ReportValidator
from interactive.interactive_editor import SimpleInteractiveEditor
from exporters.unified_exporter import UnifiedExporter, ExportFormat


def main():
    """
    Simple workflow example:
    1. Parse report
    2. Validate
    3. Fix issues if needed (interactive)
    4. Export to all formats
    """

    print("="*70)
    print("  MTBParser - Simple Workflow Example")
    print("="*70)

    # Sample report (you can replace with file read)
    sample_report = """
    Report Molecular Tumor Board

    ID Paziente: ABC123
    Età: 68 anni
    Sesso: F

    Diagnosi: Adenocarcinoma polmonare non a piccole cellule (NSCLC) stadio IVA

    Analisi Molecolare (Oncomine Comprehensive Assay v3):

    Varianti identificate:
    - EGFR esone 21: L858R, VAF 48%
    - TP53 esone 7: p.Arg248Gln, VAF 55%, Pathogenic

    TMB: 12.3 mut/Mb (alto)

    Raccomandazioni terapeutiche:
    1. Prima linea: Osimertinib (EGFR L858R sensibile)
    2. Combinazione immunoterapia + chemio (TMB alto)
    """

    # Step 1: Parse
    print("\n[STEP 1] Parsing report...")
    print("-" * 70)

    parser = MTBParser()
    report = parser.parse_report(sample_report)

    print("✓ Report parsed successfully")
    print(f"\nExtracted data:")
    print(f"  Patient ID: {report.patient.id}")
    print(f"  Age: {report.patient.age} years")
    print(f"  Sex: {report.patient.sex}")
    print(f"  Diagnosis: {report.diagnosis.primary_diagnosis}")
    print(f"  Stage: {report.diagnosis.stage}")
    print(f"  Variants: {len(report.variants)}")
    for i, v in enumerate(report.variants, 1):
        print(f"    {i}. {v.gene} {v.protein_change or v.cdna_change} "
              f"({v.vaf}% VAF)" if v.vaf else f"    {i}. {v.gene}")
    print(f"  TMB: {report.tmb} mut/Mb")
    print(f"  Recommendations: {len(report.recommendations)}")

    # Step 2: Validate
    print("\n[STEP 2] Validating report...")
    print("-" * 70)

    validator = ReportValidator()
    is_valid, issues = validator.validate(report)

    if issues:
        print(validator.format_validation_report())
    else:
        print("✓ No issues found - report is valid!")

    # Step 3: Interactive editing if needed
    if validator.needs_interactive_mode():
        print("\n[STEP 3] Starting interactive editing mode...")
        print("-" * 70)
        print("⚠️  Critical issues detected!")
        print("    The interactive editor will help you fix them.\n")

        # In a real scenario, this would start the interactive editor
        # For this example, we'll simulate it
        print("(In production, interactive editor would start here)")
        print("(User would fix issues one by one)")

        # Uncomment the following for real interactive mode:
        # editor = SimpleInteractiveEditor(report, issues)
        # report = editor.start()

    else:
        print("\n[STEP 3] Skipping interactive mode - no critical issues")
        print("-" * 70)

    # Step 4: Quality metrics
    print("\n[STEP 4] Quality Assessment...")
    print("-" * 70)

    if report.quality_metrics:
        qm = report.quality_metrics
        print(f"Report Quality Metrics:")
        print(f"  Completeness: {qm.completeness_pct}%")
        print(f"  Total fields: {qm.filled_fields}/{qm.total_fields}")
        print(f"  Variants found: {qm.variants_found}")
        print(f"  Variants with VAF: {qm.variants_with_vaf}/{qm.variants_found}")
        print(f"  Variants classified: {qm.variants_classified}/{qm.variants_found}")
        print(f"  Variants with HGNC codes: {qm.variants_with_gene_code}/{qm.variants_found}")
        print(f"  Drugs identified: {qm.drugs_identified}")
        print(f"  Drugs with RxNorm: {qm.drugs_mapped}/{qm.drugs_identified}")
        print(f"  Diagnosis mapped to ICD-O: {'Yes' if qm.diagnosis_mapped else 'No'}")

    # Step 5: Export to multiple formats
    print("\n[STEP 5] Exporting to interoperable formats...")
    print("-" * 70)

    exporter = UnifiedExporter(
        output_dir=Path("/tmp/mtb_simple_workflow"),
        pretty=True
    )

    # Export to all formats
    print("\nExporting to:")
    print("  - FHIR R4 (HL7 standard for EHR integration)")
    print("  - GA4GH Phenopackets v2 (Genomic research)")
    print("  - OMOP CDM v5.4 (Observational research)")
    print("  - Native JSON (MTBParser format)")
    print("  - CSV (Analysis in Excel/R/Python)")

    results = exporter.export(
        report,
        formats=[ExportFormat.ALL],
        save_to_file=True
    )

    print(f"\n✓ Export complete!")
    print(f"  Output directory: /tmp/mtb_simple_workflow/patient_{report.patient.id}/")

    # Step 6: Show what was created
    print("\n[STEP 6] Summary of created files...")
    print("-" * 70)

    patient_dir = Path(f"/tmp/mtb_simple_workflow/patient_{report.patient.id}")
    if patient_dir.exists():
        print("\nFiles created:")
        for file in sorted(patient_dir.rglob('*')):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                rel_path = file.relative_to(patient_dir)
                print(f"  {str(rel_path):40s} ({size_kb:6.1f} KB)")

    # Final summary
    print("\n" + "="*70)
    print("  Workflow Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review exported files in /tmp/mtb_simple_workflow/")
    print("  2. Use FHIR bundle for EHR integration")
    print("  3. Use Phenopacket for research databases")
    print("  4. Use OMOP tables for observational studies")
    print("  5. Use CSV for quick data analysis")
    print("\nFor more details:")
    print("  - See README_INTERACTIVE.md for complete documentation")
    print("  - See QUICK_REFERENCE.md for common commands")
    print("  - Run: python mtb_parser_cli.py --help")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
