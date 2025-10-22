#!/usr/bin/env python3
"""
Parse Single MTB Report - Simple interface
Usage: python3 parse_single_report.py <path_to_docx_file>
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_single_report.py <path_to_docx_file>")
        print("\nExample:")
        print("  python3 parse_single_report.py ~/Downloads/report.docx")
        sys.exit(1)

    # Input file
    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    print("=" * 80)
    print(f"MTBParser - Processing: {input_file.name}")
    print("=" * 80)

    # Read document
    print("\n📄 Reading document...")
    try:
        text = read_docx(input_file)
        print(f"✅ Document read: {len(text)} characters")

        # Show preview
        print(f"\n📋 Preview (first 300 chars):")
        print("-" * 80)
        print(text[:300] + "...")
        print("-" * 80)
    except Exception as e:
        print(f"❌ Error reading document: {e}")
        sys.exit(1)

    # Parse
    print("\n🔍 Parsing report...")
    parser = MTBParser()

    try:
        report = parser.parse_report(text)
        print("✅ Report parsed successfully!")
    except Exception as e:
        print(f"❌ Error parsing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Display results
    print("\n" + "=" * 80)
    print("📊 EXTRACTION RESULTS")
    print("=" * 80)

    # Patient
    print(f"\n👤 PATIENT:")
    print(f"   ID: {report.patient.id or '❌ Not found'}")
    print(f"   Age: {report.patient.age or '❌ Not found'}")
    print(f"   Sex: {report.patient.sex or '❌ Not found'}")
    print(f"   Birth Date: {report.patient.birth_date or '❌ Not found'}")

    # Diagnosis
    print(f"\n🏥 DIAGNOSIS:")
    diagnosis_text = report.diagnosis.primary_diagnosis or '❌ Not found'
    if len(diagnosis_text) > 80:
        diagnosis_text = diagnosis_text[:77] + "..."
    print(f"   Primary: {diagnosis_text}")
    print(f"   Stage: {report.diagnosis.stage or '❌ Not found'}")
    print(f"   ICD-O Code: {report.diagnosis.icd_o_code.get('code') if report.diagnosis.icd_o_code else '❌ Not mapped'}")

    # Variants
    print(f"\n🧬 VARIANTS ({len(report.variants)} found):")
    if report.variants:
        for i, variant in enumerate(report.variants[:10], 1):  # Show first 10
            gene_info = f"{variant.gene}"
            if variant.protein_change:
                gene_info += f" {variant.protein_change}"
            if variant.cdna_change:
                gene_info += f" ({variant.cdna_change})"

            print(f"   {i}. {gene_info}")

            details = []
            if variant.vaf:
                details.append(f"VAF: {variant.vaf}%")
            if variant.classification:
                details.append(f"Class: {variant.classification}")
            if variant.gene_code:
                details.append(f"HGNC: {variant.gene_code.get('code')}")

            if details:
                print(f"      {' | '.join(details)}")

        if len(report.variants) > 10:
            print(f"   ... and {len(report.variants) - 10} more variants")
    else:
        print("   ❌ No variants found")

    # TMB
    print(f"\n📈 TMB: {report.tmb if report.tmb else '❌ Not found'} mut/Mb")

    # NGS Method
    if report.ngs_method:
        ngs_text = report.ngs_method
        if len(ngs_text) > 60:
            ngs_text = ngs_text[:57] + "..."
        print(f"🔬 NGS Method: {ngs_text}")

    # Recommendations
    print(f"\n💊 THERAPEUTIC RECOMMENDATIONS ({len(report.recommendations)} found):")
    if report.recommendations:
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec.drug.upper()}")
            if rec.gene_target:
                print(f"      Target: {rec.gene_target}")
            if rec.evidence_level:
                print(f"      Evidence: {rec.evidence_level}")
            if rec.drug_code:
                print(f"      RxNorm: {rec.drug_code.get('code')}")
    else:
        print("   ❌ No recommendations found")

    # Quality Assessment
    print("\n" + "=" * 80)
    print("📊 QUALITY ASSESSMENT")
    print("=" * 80)

    assessor = QualityAssessor()
    quality_report = assessor.assess_report(report)

    print(f"\n⭐ Overall Score: {quality_report.overall_score:.1f}/100")
    print(f"📊 Quality Level: {quality_report.quality_level}")
    print(f"📈 Completeness: {quality_report.completeness_pct:.1f}%")

    print(f"\n🧬 Variant Quality:")
    print(f"   Total: {quality_report.variants_total}")
    print(f"   With HGVS: {quality_report.variants_with_hgvs}")
    print(f"   With VAF: {quality_report.variants_with_vaf}")
    print(f"   Classified: {quality_report.variants_classified}")
    print(f"   Actionable: {quality_report.variants_actionable}")

    print(f"\n🗺️  Mapping Quality:")
    print(f"   Diagnosis mapped: {'✅ Yes' if quality_report.diagnosis_mapped else '❌ No'}")
    print(f"   Genes mapped: {quality_report.genes_mapped_pct:.1f}%")
    print(f"   Drugs mapped: {quality_report.drugs_mapped_pct:.1f}%")

    if quality_report.warnings:
        print(f"\n⚠️  Warnings ({len(quality_report.warnings)}):")
        for warning in quality_report.warnings[:5]:
            print(f"   • {warning}")

    if quality_report.recommendations:
        print(f"\n💡 Recommendations ({len(quality_report.recommendations)}):")
        for rec in quality_report.recommendations[:3]:
            print(f"   • {rec}")

    # Create output directory
    output_dir = Path("output") / input_file.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create mappers and export
    print("\n" + "=" * 80)
    print("🔄 CREATING STANDARD MAPPINGS & EXPORTS")
    print("=" * 80)

    try:
        # FHIR
        fhir_mapper = FHIRMapper()
        fhir_bundle = fhir_mapper.create_fhir_bundle(report)
        print(f"✅ FHIR R4 Bundle: {len(fhir_bundle['entry'])} resources")

        # Phenopackets
        pheno_mapper = PhenopacketsMapper()
        phenopacket = pheno_mapper.create_phenopacket(report)
        print(f"✅ GA4GH Phenopacket v2: Created")

        # OMOP
        omop_mapper = OMOPMapper()
        omop_tables = omop_mapper.create_omop_tables(report)
        total_records = sum(len(records) for records in omop_tables.values())
        print(f"✅ OMOP CDM v5.4: {total_records} records")

        # JSON Export
        json_exporter = JSONExporter(pretty=True, include_raw=False)
        package = json_exporter.export_complete_package(
            report=report,
            fhir_bundle=fhir_bundle,
            phenopacket=phenopacket,
            omop_tables=omop_tables
        )

        json_file = output_dir / "complete_package.json"
        json_exporter.save_to_file(package, json_file)
        print(f"✅ JSON: {json_file} ({json_file.stat().st_size:,} bytes)")

        # CSV Export
        csv_exporter = CSVExporter()
        csv_dir = output_dir / "csv"
        csv_exporter.save_complete_export(report, csv_dir)
        csv_files = list(csv_dir.glob('*.csv'))
        print(f"✅ CSV: {len(csv_files)} files in {csv_dir}")

    except Exception as e:
        print(f"⚠️  Warning during export: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\n📁 Output saved to: {output_dir.absolute()}")
    print(f"\n📊 Summary:")
    print(f"   • Patient ID: {report.patient.id or 'Not found'}")
    print(f"   • Variants: {len(report.variants)}")
    print(f"   • Drugs: {len(report.recommendations)}")
    print(f"   • Quality: {quality_report.overall_score:.1f}/100 ({quality_report.quality_level})")
    print(f"\n📦 Files created:")
    print(f"   • complete_package.json (FHIR + Phenopackets + OMOP)")
    print(f"   • csv/patient_summary.csv")
    print(f"   • csv/variants.csv")
    print(f"   • csv/recommendations.csv")
    print()


if __name__ == "__main__":
    main()
