#!/usr/bin/env python3
"""
Example: Enhanced MTB Parsing with Clinical Annotations
Demonstrates integration of pattern extraction with CIViC/OncoKB annotations
"""

from core.mtb_parser import MTBParser
from core.data_models import MTBReport
from annotators.combined_annotator import CombinedAnnotator
from vocabularies.vocabulary_loader import VocabularyLoader
import json


def parse_and_annotate_report(report_text: str, tumor_type: str = None):
    """
    Parse MTB report and annotate variants with clinical evidence

    Args:
        report_text: Raw MTB report text
        tumor_type: Cancer type for context-specific recommendations

    Returns:
        Dictionary with parsed data and clinical annotations
    """
    # Initialize parser and annotator
    parser = MTBParser()
    annotator = CombinedAnnotator()

    # Parse report
    print("Parsing MTB report...")
    mtb_report = parser.parse_report(report_text)

    # Annotate each variant
    print(f"\nAnnotating {len(mtb_report.variants)} variants...")
    annotated_variants = []

    for variant in mtb_report.variants:
        # Determine variant name for annotation
        variant_name = variant.protein_change or variant.cdna_change or "Unknown"

        # Get clinical annotations
        annotation = annotator.annotate_variant(
            gene=variant.gene,
            variant=variant_name,
            tumor_type=tumor_type or mtb_report.diagnosis.primary_diagnosis
        )

        # Generate clinical report
        clinical_report = annotator.get_clinical_report(annotation)

        # Combine parsed variant with clinical annotation
        annotated_variant = {
            "gene": variant.gene,
            "variant": variant_name,
            "cdna_change": variant.cdna_change,
            "protein_change": variant.protein_change,
            "vaf": variant.vaf,
            "classification": variant.classification,
            "hgnc_code": variant.gene_code,
            "clinical_annotation": clinical_report
        }

        annotated_variants.append(annotated_variant)

    # Compile results
    results = {
        "patient": {
            "id": mtb_report.patient.id,
            "age": mtb_report.patient.age,
            "sex": mtb_report.patient.sex,
            "birth_date": mtb_report.patient.birth_date
        },
        "diagnosis": {
            "primary_diagnosis": mtb_report.diagnosis.primary_diagnosis,
            "stage": mtb_report.diagnosis.stage,
            "icd_o_code": mtb_report.diagnosis.icd_o_code
        },
        "variants": annotated_variants,
        "tmb": mtb_report.tmb,
        "ngs_method": mtb_report.ngs_method,
        "quality_metrics": {
            "completeness_pct": mtb_report.quality_metrics.completeness_pct,
            "variants_found": mtb_report.quality_metrics.variants_found,
            "diagnosis_mapped": mtb_report.quality_metrics.diagnosis_mapped,
            "warnings": mtb_report.quality_metrics.warnings
        }
    }

    return results


def print_clinical_summary(results: dict):
    """Print formatted clinical summary"""

    print("\n" + "="*80)
    print("MTB REPORT - CLINICAL SUMMARY")
    print("="*80)

    # Patient Info
    patient = results["patient"]
    print(f"\nPatient ID: {patient['id']}")
    print(f"Age: {patient['age']} years, Sex: {patient['sex']}")

    # Diagnosis
    diagnosis = results["diagnosis"]
    print(f"\nDiagnosis: {diagnosis['primary_diagnosis']}")
    if diagnosis['stage']:
        print(f"Stage: {diagnosis['stage']}")
    if diagnosis['icd_o_code']:
        print(f"ICD-O: {diagnosis['icd_o_code']['code']} - {diagnosis['icd_o_code']['display']}")

    # TMB
    if results['tmb']:
        print(f"\nTumor Mutational Burden: {results['tmb']} mut/Mb")

    # Variants with Clinical Annotations
    print(f"\n{'='*80}")
    print(f"GENOMIC VARIANTS ({len(results['variants'])} found)")
    print('='*80)

    actionable_count = 0

    for i, var in enumerate(results['variants'], 1):
        clinical = var['clinical_annotation']

        print(f"\n{i}. {var['gene']} {var['variant']}")

        if var['vaf']:
            print(f"   VAF: {var['vaf']}%")

        if var['classification']:
            print(f"   Classification: {var['classification']}")

        # Clinical Actionability
        actionability = clinical['actionability']
        print(f"\n   Actionability: {'✓ ACTIONABLE' if actionability['is_actionable'] else '✗ Not actionable'}")
        print(f"   Score: {actionability['score']}/100")
        print(f"   Evidence: {actionability['level'] or 'No evidence'}")

        if actionability['is_actionable']:
            actionable_count += 1

        # Oncogenicity
        oncogenicity = clinical['oncogenicity']
        print(f"   Oncogenic: {oncogenicity['classification']}")
        if oncogenicity['mutation_effect']:
            print(f"   Effect: {oncogenicity['mutation_effect']}")

        # Therapeutic Options
        therapies = clinical['therapeutic_options']

        if therapies['fda_approved']:
            print(f"\n   FDA-Approved Therapies:")
            for drug in therapies['fda_approved']:
                print(f"     ✓ {drug}")

        if therapies['guideline_recommended']:
            print(f"\n   Guideline-Recommended:")
            for drug in therapies['guideline_recommended']:
                print(f"     • {drug}")

        if therapies['investigational']:
            print(f"\n   Investigational:")
            for drug in therapies['investigational'][:3]:  # Show top 3
                print(f"     ○ {drug}")

        if therapies['resistance']:
            print(f"\n   Resistance to:")
            for drug in therapies['resistance']:
                print(f"     ✗ {drug}")

        # Recommendation
        print(f"\n   📋 {clinical['recommendation']}")

        # References
        refs = clinical['references']
        if refs['civic'] or refs['oncokb']:
            print(f"\n   References:")
            if refs['civic']:
                print(f"     CIViC: {refs['civic']}")
            if refs['oncokb']:
                print(f"     OncoKB: {refs['oncokb']}")

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print('='*80)
    print(f"Total variants: {len(results['variants'])}")
    print(f"Actionable variants: {actionable_count}")
    print(f"Report completeness: {results['quality_metrics']['completeness_pct']}%")

    if results['quality_metrics']['warnings']:
        print(f"\nWarnings:")
        for warning in results['quality_metrics']['warnings']:
            print(f"  {warning}")


# Example usage
if __name__ == "__main__":
    # Sample MTB report
    sample_report = """
    RAPPORTO MOLECOLARE - TUMOR BOARD

    Paziente: 12345
    Età: 62 anni
    Sesso: M
    Data di nascita: 15/03/1962

    Diagnosi: Adenocarcinoma polmonare stadio IV

    Metodica: Oncomine Comprehensive Assay v3

    VARIANTI GENOMICHE IDENTIFICATE:

    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    EGFR c.2369C>T p.Thr790Met Pathogenic 12%
    KRAS G12C 8%

    TMB: 6.2 mut/Mb

    FUSIONI GENICHE:
    Nessuna fusione identificata

    RACCOMANDAZIONI TERAPEUTICHE:
    Sensibilità prevista a osimertinib per mutazioni EGFR L858R e T790M.
    Potenziale sensibilità a sotorasib per mutazione KRAS G12C.

    Firma: Dr. Rossi
    Data: 2024-01-15
    """

    print("Enhanced MTB Report Parser with Clinical Annotations\n")

    # Parse and annotate
    results = parse_and_annotate_report(
        report_text=sample_report,
        tumor_type="Lung Adenocarcinoma"
    )

    # Print clinical summary
    print_clinical_summary(results)

    # Optional: Export to JSON
    print(f"\n{'='*80}")
    print("Exporting results to JSON...")
    with open("annotated_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("✓ Results saved to annotated_report.json")
