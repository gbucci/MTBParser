#!/usr/bin/env python3
"""
Test MTBParser with real MTB reports from DUMTB
"""

import sys
from pathlib import Path
from docx import Document
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.mtb_parser import MTBParser
from mappers.fhir_mapper import FHIRMapper
from mappers.phenopackets_mapper import PhenopacketsMapper
from mappers.omop_mapper import OMOPMapper
from quality.quality_metrics import QualityAssessor
from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter


def read_docx(filepath):
    """Extract text from .docx file"""
    doc = Document(filepath)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def test_single_report(report_path, output_dir):
    """Test parsing a single report"""
    print(f"\n{'=' * 80}")
    print(f"Processing: {report_path.name}")
    print(f"{'=' * 80}")

    # Read report
    try:
        text = read_docx(report_path)
        print(f"✅ Document read: {len(text)} characters")

        # Show first 500 chars
        print(f"\nFirst 500 characters:")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)

    except Exception as e:
        print(f"❌ Error reading document: {e}")
        return None

    # Parse report
    parser = MTBParser()
    try:
        report = parser.parse_report(text)
        print(f"\n✅ Report parsed successfully")
    except Exception as e:
        print(f"❌ Error parsing report: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Display extracted data
    print(f"\n📊 EXTRACTED DATA:")
    print(f"{'─' * 80}")
    print(f"Patient ID: {report.patient.id or 'Not found'}")
    print(f"Age: {report.patient.age or 'Not found'}")
    print(f"Sex: {report.patient.sex or 'Not found'}")
    print(f"Birth Date: {report.patient.birth_date or 'Not found'}")
    print(f"\nDiagnosis: {report.diagnosis.primary_diagnosis or 'Not found'}")
    print(f"Stage: {report.diagnosis.stage or 'Not found'}")
    print(f"ICD-O mapped: {'Yes' if report.diagnosis.icd_o_code else 'No'}")

    print(f"\nVariants found: {len(report.variants)}")
    for i, variant in enumerate(report.variants[:5], 1):  # Show first 5
        print(f"  {i}. {variant.gene} {variant.protein_change or variant.cdna_change or ''}")
        if variant.vaf:
            print(f"     VAF: {variant.vaf}%")
        if variant.classification:
            print(f"     Class: {variant.classification}")
        if variant.gene_code:
            print(f"     HGNC: {variant.gene_code.get('code')}")

    if len(report.variants) > 5:
        print(f"  ... and {len(report.variants) - 5} more")

    print(f"\nTMB: {report.tmb if report.tmb else 'Not found'} mut/Mb")
    print(f"NGS Method: {report.ngs_method or 'Not found'}")

    print(f"\nRecommendations: {len(report.recommendations)}")
    for i, rec in enumerate(report.recommendations[:3], 1):  # Show first 3
        print(f"  {i}. {rec.drug}")
        if rec.gene_target:
            print(f"     Target: {rec.gene_target}")
        if rec.evidence_level:
            print(f"     Evidence: {rec.evidence_level}")

    if len(report.recommendations) > 3:
        print(f"  ... and {len(report.recommendations) - 3} more")

    # Quality assessment
    assessor = QualityAssessor()
    quality_report = assessor.assess_report(report)

    print(f"\n📈 QUALITY ASSESSMENT:")
    print(f"{'─' * 80}")
    print(f"Overall Score: {quality_report.overall_score}/100")
    print(f"Quality Level: {quality_report.quality_level}")
    print(f"Completeness: {quality_report.completeness_pct}%")
    print(f"Variants with HGVS: {quality_report.variants_with_hgvs}/{quality_report.variants_total}")
    print(f"Variants with VAF: {quality_report.variants_with_vaf}/{quality_report.variants_total}")
    print(f"Genes mapped: {quality_report.genes_mapped_pct:.1f}%")
    print(f"Drugs mapped: {quality_report.drugs_mapped_pct:.1f}%")

    if quality_report.warnings:
        print(f"\nWarnings: {len(quality_report.warnings)}")
        for warning in quality_report.warnings[:3]:
            print(f"  ⚠️  {warning}")

    if quality_report.recommendations:
        print(f"\nRecommendations: {len(quality_report.recommendations)}")
        for rec in quality_report.recommendations[:3]:
            print(f"  💡 {rec}")

    # Create mappers
    print(f"\n🔄 CREATING STANDARD MAPPINGS:")
    print(f"{'─' * 80}")

    try:
        fhir_mapper = FHIRMapper()
        fhir_bundle = fhir_mapper.create_fhir_bundle(report)
        print(f"✅ FHIR Bundle: {len(fhir_bundle['entry'])} resources")
    except Exception as e:
        print(f"❌ FHIR mapping error: {e}")
        fhir_bundle = None

    try:
        pheno_mapper = PhenopacketsMapper()
        phenopacket = pheno_mapper.create_phenopacket(report)
        print(f"✅ Phenopacket v2: Created")
    except Exception as e:
        print(f"❌ Phenopacket mapping error: {e}")
        phenopacket = None

    try:
        omop_mapper = OMOPMapper()
        omop_tables = omop_mapper.create_omop_tables(report)
        total_records = sum(len(records) for records in omop_tables.values())
        print(f"✅ OMOP CDM: {total_records} records across {len(omop_tables)} tables")
    except Exception as e:
        print(f"❌ OMOP mapping error: {e}")
        omop_tables = None

    # Export
    report_output_dir = output_dir / report_path.stem
    report_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n💾 EXPORTING:")
    print(f"{'─' * 80}")

    # JSON export
    json_exporter = JSONExporter(pretty=True, include_raw=False)
    package = json_exporter.export_complete_package(
        report=report,
        fhir_bundle=fhir_bundle,
        phenopacket=phenopacket,
        omop_tables=omop_tables
    )

    json_file = report_output_dir / "complete_package.json"
    json_exporter.save_to_file(package, json_file)
    print(f"✅ JSON: {json_file} ({json_file.stat().st_size:,} bytes)")

    # CSV export
    csv_exporter = CSVExporter()
    csv_dir = report_output_dir / "csv"
    csv_exporter.save_complete_export(report, csv_dir)
    csv_files = list(csv_dir.glob('*.csv'))
    print(f"✅ CSV: {len(csv_files)} files in {csv_dir}")

    return {
        'filename': report_path.name,
        'quality_score': quality_report.overall_score,
        'quality_level': quality_report.quality_level,
        'variants': len(report.variants),
        'recommendations': len(report.recommendations),
        'patient_id': report.patient.id,
        'diagnosis': report.diagnosis.primary_diagnosis
    }


def main():
    """Test all reports in DUMTB directory"""
    print("=" * 80)
    print("MTB PARSER - REAL REPORTS TEST")
    print("=" * 80)

    # Input directory
    dumtb_dir = Path("/Users/bucci.gabriele/Documents/Tumor Molecular Board/DUMTB/")

    if not dumtb_dir.exists():
        print(f"❌ Directory not found: {dumtb_dir}")
        return

    # Output directory
    output_dir = Path("/Users/bucci.gabriele/Documents/MTBParser/test_output_real")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nInput:  {dumtb_dir}")
    print(f"Output: {output_dir}")

    # Get all .docx files
    docx_files = list(dumtb_dir.glob("*.docx"))
    print(f"\nFound {len(docx_files)} .docx files")

    # Test each report
    results = []
    for docx_file in docx_files:
        try:
            result = test_single_report(docx_file, output_dir)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n❌ Critical error processing {docx_file.name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if results:
        print(f"\nSuccessfully processed: {len(results)}/{len(docx_files)} reports")
        print(f"\nResults:")
        print(f"{'─' * 80}")
        print(f"{'File':<40} {'Quality':<15} {'Variants':<10} {'Drugs':<10}")
        print(f"{'─' * 80}")

        for r in results:
            filename = r['filename'][:38]
            quality = f"{r['quality_score']:.0f}/100 ({r['quality_level']})"
            print(f"{filename:<40} {quality:<15} {r['variants']:<10} {r['recommendations']:<10}")

        # Statistics
        avg_quality = sum(r['quality_score'] for r in results) / len(results)
        total_variants = sum(r['variants'] for r in results)
        total_drugs = sum(r['recommendations'] for r in results)

        print(f"{'─' * 80}")
        print(f"\nStatistics:")
        print(f"  Average Quality Score: {avg_quality:.1f}/100")
        print(f"  Total Variants Extracted: {total_variants}")
        print(f"  Total Drug Recommendations: {total_drugs}")

        # Save summary
        summary_file = output_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'total_reports': len(docx_files),
                'successful': len(results),
                'average_quality': avg_quality,
                'total_variants': total_variants,
                'total_recommendations': total_drugs,
                'reports': results
            }, f, indent=2)

        print(f"\n✅ Summary saved to: {summary_file}")
    else:
        print("\n❌ No reports were successfully processed")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
