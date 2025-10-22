#!/usr/bin/env python3
"""
Annotator Configuration Examples
Demonstrates how to use different annotator configurations based on licensing and use case
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from annotators.combined_annotator import CombinedAnnotator
from annotators.annotator_config import AnnotatorConfig


def print_section(title):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print('='*80)


def print_report(report, show_full=False):
    """Print clinical report summary"""
    print(f"\nVariant: {report['variant']}")
    print(f"Actionability Score: {report['actionability']['score']}/100")
    print(f"Evidence Level: {report['actionability']['level']}")
    print(f"Is Actionable: {'✓ Yes' if report['actionability']['is_actionable'] else '✗ No'}")

    escat = report['escat_classification']
    if escat['tier']:
        print(f"\nESCAT Classification:")
        print(f"  Tier: {escat['tier']}")
        print(f"  Score: {escat['score']}/100")
        print(f"  Description: {escat['description']}")

    onco = report['oncogenicity']
    if onco['classification']:
        print(f"\nOncogenicity:")
        print(f"  Classification: {onco['classification']}")
        if onco['mutation_effect']:
            print(f"  Mutation Effect: {onco['mutation_effect']}")

    print(f"\nEvidence Sources: {', '.join(report['evidence_sources']) if report['evidence_sources'] else 'None'}")

    therapies = report['therapeutic_options']
    if therapies['fda_approved']:
        print(f"\nFDA-Approved Therapies:")
        for drug in therapies['fda_approved'][:5]:  # Show first 5
            print(f"  ✓ {drug}")

    if therapies['guideline_recommended']:
        print(f"\nGuideline-Recommended:")
        for drug in therapies['guideline_recommended'][:3]:
            print(f"  • {drug}")

    if therapies['resistance']:
        print(f"\nResistance Markers:")
        for drug in therapies['resistance'][:3]:
            print(f"  ✗ {drug}")

    print(f"\n{'Recommendation:':^80}")
    print(f"  {report['recommendation']}")

    if show_full:
        refs = report['references']
        if refs['civic'] or refs['oncokb']:
            print(f"\nReferences:")
            if refs['civic']:
                print(f"  CIViC: {refs['civic']}")
            if refs['oncokb']:
                print(f"  OncoKB: {refs['oncokb']}")


def example_1_free_sources():
    """Example 1: Free sources only (CIViC + ESCAT) - DEFAULT"""
    print_section("EXAMPLE 1: FREE SOURCES ONLY (CIViC + ESCAT)")

    print("\nUse Case:")
    print("  - Academic research")
    print("  - Testing/development")
    print("  - Budget-constrained projects")
    print("  - Maximum coverage with free data")

    # Create configuration
    config = AnnotatorConfig.free_only()
    print(f"\n{config.summary()}")

    # Create annotator
    annotator = CombinedAnnotator(config=config)

    # Test variants
    test_cases = [
        ("EGFR", "L858R", "Lung Adenocarcinoma"),
        ("BRAF", "V600E", "Melanoma"),
        ("KRAS", "G12C", "NSCLC")
    ]

    for gene, variant, tumor_type in test_cases:
        print(f"\n{'-'*80}")
        result = annotator.annotate_variant(gene, variant, tumor_type)
        report = annotator.get_clinical_report(result)
        print_report(report)


def example_2_escat_only():
    """Example 2: ESCAT only (European standard)"""
    print_section("EXAMPLE 2: ESCAT ONLY (European Standard)")

    print("\nUse Case:")
    print("  - European hospitals")
    print("  - ESMO guideline compliance")
    print("  - EMA approval-focused decisions")
    print("  - Italian/European clinical practice")

    config = AnnotatorConfig.escat_only()
    print(f"\n{config.summary()}")

    annotator = CombinedAnnotator(config=config)

    # Test with Italian tumor types
    test_cases = [
        ("EGFR", "L858R", "NSCLC"),
        ("ALK", "Fusion", "adenocarcinoma polmonare"),
        ("BRAF", "V600E", "melanoma")
    ]

    for gene, variant, tumor_type in test_cases:
        print(f"\n{'-'*80}")
        result = annotator.annotate_variant(gene, variant, tumor_type)
        report = annotator.get_clinical_report(result)
        print_report(report)


def example_3_european_clinical():
    """Example 3: European clinical (ESCAT + CIViC)"""
    print_section("EXAMPLE 3: EUROPEAN CLINICAL (ESCAT + CIViC)")

    print("\nUse Case:")
    print("  - European hospitals")
    print("  - ESMO guideline compliance")
    print("  - Budget-conscious institutions")
    print("  - Avoiding OncoKB licensing costs")

    config = AnnotatorConfig.european_clinical()
    print(f"\nConfiguration: {', '.join(config.get_enabled_names())}")
    print(f"Prefer European standards: {config.prefer_european_standards}")

    annotator = CombinedAnnotator(config=config)

    # Test actionable variants
    result = annotator.annotate_variant("EGFR", "L858R", "NSCLC")
    report = annotator.get_clinical_report(result)

    print(f"\n{'-'*80}")
    print_report(report, show_full=True)


def example_4_all_sources():
    """Example 4: All sources (maximum validation)"""
    print_section("EXAMPLE 4: ALL SOURCES (Maximum Validation)")

    print("\nUse Case:")
    print("  - Molecular Tumor Boards")
    print("  - High-stakes clinical decisions")
    print("  - Triple-source validation")
    print("  - Maximum evidence concordance")

    print("\nNote: Using demo API key for OncoKB (mock data)")

    config = AnnotatorConfig.all_sources(oncokb_api_key="demo_key_12345")
    print(f"\nConfiguration: {', '.join(config.get_enabled_names())}")

    annotator = CombinedAnnotator(config=config)

    # Test with concordant evidence (all three sources agree)
    test_cases = [
        ("EGFR", "L858R", "NSCLC"),
        ("BRAF", "V600E", "Melanoma"),
        ("KRAS", "G12C", "NSCLC")
    ]

    for gene, variant, tumor_type in test_cases:
        print(f"\n{'-'*80}")
        result = annotator.annotate_variant(gene, variant, tumor_type)
        report = annotator.get_clinical_report(result)
        print_report(report)

        # Show concordance bonus
        if len(report['evidence_sources']) >= 2:
            print(f"\n  → Concordance bonus applied: {len(report['evidence_sources'])} sources agree")


def example_5_custom_configuration():
    """Example 5: Custom configuration"""
    print_section("EXAMPLE 5: CUSTOM CONFIGURATION")

    print("\nUse Case:")
    print("  - Specific institutional requirements")
    print("  - Testing different combinations")
    print("  - Performance optimization")

    # Create custom configuration
    from annotators.annotator_config import AnnotatorType

    config = AnnotatorConfig()
    config.enable(AnnotatorType.CIVIC)
    config.enable(AnnotatorType.ESCAT)
    config.prefer_european_standards = True
    config.enable_caching = True

    print(f"\nCustom Configuration:")
    print(f"  Enabled: {', '.join(config.get_enabled_names())}")
    print(f"  European standards: {config.prefer_european_standards}")
    print(f"  Caching: {config.enable_caching}")

    annotator = CombinedAnnotator(config=config)

    result = annotator.annotate_variant("ALK", "Fusion", "NSCLC")
    report = annotator.get_clinical_report(result)

    print(f"\n{'-'*80}")
    print_report(report)


def example_6_batch_annotation():
    """Example 6: Batch annotation with different configurations"""
    print_section("EXAMPLE 6: BATCH ANNOTATION")

    print("\nUse Case:")
    print("  - Processing multiple variants from MTB report")
    print("  - Comparing results across configurations")

    # Variants to test
    variants = [
        {"gene": "EGFR", "variant": "L858R", "tumor_type": "NSCLC"},
        {"gene": "KRAS", "variant": "G12D", "tumor_type": "Colorectal"},
        {"gene": "TP53", "variant": "R273H", "tumor_type": "Colorectal"},  # Non-actionable
        {"gene": "PIK3CA", "variant": "H1047R", "tumor_type": "Breast"}
    ]

    # Test with free sources
    config = AnnotatorConfig.free_only()
    annotator = CombinedAnnotator(config=config)

    print(f"\nAnnotating {len(variants)} variants with free sources (CIViC + ESCAT):")

    results = []
    for var in variants:
        result = annotator.annotate_variant(
            var['gene'],
            var['variant'],
            var['tumor_type']
        )
        report = annotator.get_clinical_report(result)
        results.append(report)

        print(f"\n{var['gene']} {var['variant']} ({var['tumor_type']}):")
        print(f"  Actionability: {report['actionability']['score']}/100")
        print(f"  ESCAT Tier: {report['escat_classification']['tier'] or 'N/A'}")
        print(f"  Sources: {', '.join(report['evidence_sources']) or 'None'}")
        print(f"  Actionable: {'✓ Yes' if report['actionability']['is_actionable'] else '✗ No'}")

    # Summary
    actionable_count = sum(1 for r in results if r['actionability']['is_actionable'])
    print(f"\n{'Summary:':^80}")
    print(f"  Total variants: {len(results)}")
    print(f"  Actionable: {actionable_count} ({actionable_count/len(results)*100:.1f}%)")
    print(f"  Non-actionable: {len(results) - actionable_count}")


def example_7_license_validation():
    """Example 7: License validation and information"""
    print_section("EXAMPLE 7: LICENSE VALIDATION")

    print("\nChecking license requirements for different configurations:\n")

    configurations = [
        ("Free Only", AnnotatorConfig.free_only()),
        ("ESCAT Only", AnnotatorConfig.escat_only()),
        ("European Clinical", AnnotatorConfig.european_clinical()),
        ("All Sources", AnnotatorConfig.all_sources(oncokb_api_key="demo_key"))
    ]

    for name, config in configurations:
        print(f"\n{'-'*80}")
        print(f"{name:^80}")
        print('-'*80)

        # Get licensing info
        licensing = config.get_licensing_info()
        for annotator, info in licensing.items():
            print(f"\n  {annotator}:")
            print(f"    License Type: {info['license'].upper()}")
            print(f"    Cost: {info['cost']}")
            print(f"    Requires API Key: {'Yes' if info['requires_api_key'] else 'No'}")
            if info['license_url']:
                print(f"    Info: {info['license_url']}")

        # Validation status
        validation = config.validate_licenses()
        print(f"\n  Validation Status:")
        for annotator, status in validation.items():
            if isinstance(status, bool):
                status_str = "✓ Valid" if status else "✗ Invalid"
            else:
                status_str = f"⚠ {status}"
            print(f"    {annotator}: {status_str}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("ANNOTATOR CONFIGURATION EXAMPLES")
    print("MTBParser System v1.1.0 - Clinical Annotation Configuration")
    print("="*80)

    print("\nThis script demonstrates different annotator configurations:")
    print("  1. Free sources only (CIViC + ESCAT) - DEFAULT")
    print("  2. ESCAT only (European standard)")
    print("  3. European clinical (ESCAT + CIViC)")
    print("  4. All sources (maximum validation)")
    print("  5. Custom configuration")
    print("  6. Batch annotation")
    print("  7. License validation")

    # Run examples
    example_1_free_sources()
    example_2_escat_only()
    example_3_european_clinical()
    example_4_all_sources()
    example_5_custom_configuration()
    example_6_batch_annotation()
    example_7_license_validation()

    # Final summary
    print_section("SUMMARY")
    print("\nKey Takeaways:")
    print("  ✓ CIViC and ESCAT are FREE - no API keys required")
    print("  ✓ OncoKB requires commercial license for clinical use")
    print("  ✓ Default configuration uses free sources only")
    print("  ✓ European hospitals: use european_clinical() preset")
    print("  ✓ US hospitals: use us_clinical() with OncoKB key")
    print("  ✓ Molecular Tumor Boards: use all_sources() for maximum validation")
    print("  ✓ Concordance bonus: +10% for 2 sources, +15% for 3 sources")

    print("\nFor more information:")
    print("  - See ANNOTATOR_CONFIGURATION.md")
    print("  - See ESCAT_INTEGRATION.md")
    print("  - CIViC: https://civicdb.org")
    print("  - OncoKB: https://www.oncokb.org")
    print("  - ESCAT: https://www.esmo.org/guidelines/precision-medicine")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
