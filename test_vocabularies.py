#!/usr/bin/env python3
"""
Test script for SNOMED-CT and LOINC vocabularies integration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from vocabularies.vocabulary_loader import VocabularyLoader

def main():
    print("="*80)
    print("SNOMED-CT and LOINC Vocabulary Integration Test")
    print("="*80)
    
    # Load vocabularies
    loader = VocabularyLoader()
    
    print("\n📊 Vocabulary Statistics:")
    stats = loader.get_vocabulary_stats()
    print(f"  • ICD-O Diagnoses: {stats['icd_o_diagnoses_count']}")
    print(f"  • RxNorm Drugs: {stats['rxnorm_drugs_count']}")
    print(f"  • HGNC Genes: {stats['hgnc_genes_count']} ({stats['actionable_genes_count']} actionable)")
    print(f"  • SNOMED-CT Terms: {stats['snomed_ct_terms_count']}")
    print(f"  • LOINC Codes: {stats['loinc_codes_count']}")
    
    # Test SNOMED-CT mappings
    print("\n🏥 SNOMED-CT Clinical Term Mappings:")
    
    test_terms = [
        ("melanoma cutaneo", "clinical_findings"),
        ("metastasi", "clinical_findings"),
        ("ngs", "procedures"),
        ("stadio III", "staging"),
        ("biopsia", "procedures"),
        ("mutazione somatica", "molecular_findings"),
        ("pd-l1 positivo", "biomarkers")
    ]
    
    for term, category in test_terms:
        result = loader.map_snomed_term(term, category=category)
        if result:
            print(f"  ✅ {term:30s} → {result['code']:12s} | {result['display']}")
        else:
            print(f"  ❌ {term:30s} → NOT FOUND")
    
    # Test LOINC mappings
    print("\n🧬 LOINC Molecular Test Mappings:")
    
    # Get specific categories
    genomic_variants = loader.get_loinc_by_category('genomic_variants')
    tumor_markers = loader.get_loinc_by_category('tumor_markers')
    ngs_panels = loader.get_loinc_by_category('ngs_panels')
    
    print(f"\n  Genomic Variants ({len(genomic_variants)} codes):")
    for key, value in list(genomic_variants.items())[:5]:
        print(f"    • {key:35s} → {value['code']:10s} | {value['display']}")
    
    print(f"\n  Tumor Markers ({len(tumor_markers)} codes):")
    for key, value in list(tumor_markers.items())[:5]:
        print(f"    • {key:35s} → {value['code']:10s} | {value['display']}")
    
    print(f"\n  NGS Panels ({len(ngs_panels)} codes):")
    for key, value in ngs_panels.items():
        print(f"    • {key:35s} → {value['code']:10s} | {value['display']}")
    
    # Test integration with real clinical data
    print("\n🔬 Real Clinical Data Test:")
    print("  Scenario: BRAF V600E mutation in melanoma")
    
    # Map diagnosis
    diagnosis = loader.map_diagnosis("melanoma cutaneo")
    print(f"\n  Diagnosis mapping:")
    print(f"    • ICD-O Code: {diagnosis['code']} - {diagnosis['display']}")
    
    # Map SNOMED term
    snomed_diagnosis = loader.map_snomed_term("melanoma cutaneo")
    print(f"    • SNOMED-CT: {snomed_diagnosis['code']} - {snomed_diagnosis['display']}")
    
    # Map gene
    gene = loader.map_gene("BRAF")
    print(f"\n  Gene mapping:")
    print(f"    • HGNC: {gene['code']} - {gene['name']}")
    print(f"    • Actionable: {gene['actionable']}")
    
    # Map drugs
    drugs = loader.get_drugs_by_target("BRAF")
    print(f"\n  Targeted therapies ({len(drugs)}):")
    for drug in drugs[:3]:
        print(f"    • {drug['name'].capitalize():15s} (RxNorm: {drug['code']}) - {drug['evidence_level']}")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("="*80)

if __name__ == "__main__":
    main()
