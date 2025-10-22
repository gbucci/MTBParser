#!/usr/bin/env python3
"""
Vocabulary Loader - Dynamic loading and management of controlled vocabularies
Supports ICD-O, RxNorm, HGNC, SNOMED-CT
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from difflib import get_close_matches


class VocabularyLoader:
    """
    Loads and manages controlled vocabularies from JSON files.
    Supports fuzzy matching for robust clinical text parsing.
    """

    def __init__(self, vocab_dir: Optional[str] = None):
        """
        Initialize vocabulary loader

        Args:
            vocab_dir: Directory containing vocabulary JSON files.
                      If None, uses the vocabularies/ directory relative to this file.
        """
        if vocab_dir is None:
            # Default to vocabularies/ directory in the same location as this file
            vocab_dir = Path(__file__).parent
        else:
            vocab_dir = Path(vocab_dir)

        self.vocab_dir = vocab_dir
        self.icd_o_diagnoses = {}
        self.rxnorm_drugs = {}
        self.hgnc_genes = {}
        self.snomed_ct_terms = {}

        # Metadata from vocabularies
        self.metadata = {}

        # Load all vocabularies
        self._load_vocabularies()

    def _load_vocabularies(self):
        """Load all vocabulary JSON files"""
        try:
            # Load ICD-O diagnoses
            with open(self.vocab_dir / 'icd_o_diagnoses.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.icd_o_diagnoses = data.get('diagnoses', {})
                self.metadata['icd_o'] = data.get('metadata', {})

            # Load RxNorm drugs
            with open(self.vocab_dir / 'rxnorm_drugs.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rxnorm_drugs = data.get('drugs', {})
                self.metadata['rxnorm'] = data.get('metadata', {})

            # Load HGNC genes
            with open(self.vocab_dir / 'hgnc_genes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.hgnc_genes = data.get('genes', {})
                self.metadata['hgnc'] = data.get('metadata', {})

            # Load SNOMED-CT terms
            with open(self.vocab_dir / 'snomed_ct_terms.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.snomed_ct_terms = data
                self.metadata['snomed_ct'] = data.get('metadata', {})

        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Vocabulary file not found: {e.filename}. "
                f"Ensure all vocabulary JSON files are in {self.vocab_dir}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in vocabulary file: {e}")

    def map_diagnosis(self, diagnosis_text: str, fuzzy: bool = True, cutoff: float = 0.6) -> Optional[Dict]:
        """
        Map diagnosis text to ICD-O code

        Args:
            diagnosis_text: Italian or English diagnosis text
            fuzzy: Enable fuzzy matching for partial matches
            cutoff: Similarity threshold for fuzzy matching (0.0-1.0)

        Returns:
            Dictionary with code, system, display, topography, or None
        """
        diagnosis_lower = diagnosis_text.lower().strip()

        # Exact match first
        if diagnosis_lower in self.icd_o_diagnoses:
            return self.icd_o_diagnoses[diagnosis_lower]

        # Substring match
        for key, value in self.icd_o_diagnoses.items():
            if key in diagnosis_lower or diagnosis_lower in key:
                return value

        # Fuzzy match if enabled
        if fuzzy:
            matches = get_close_matches(
                diagnosis_lower,
                self.icd_o_diagnoses.keys(),
                n=1,
                cutoff=cutoff
            )
            if matches:
                return self.icd_o_diagnoses[matches[0]]

        return None

    def map_drug(self, drug_name: str, fuzzy: bool = True, cutoff: float = 0.8) -> Optional[Dict]:
        """
        Map drug name to RxNorm code

        Args:
            drug_name: Drug name (generic name preferred)
            fuzzy: Enable fuzzy matching
            cutoff: Similarity threshold for fuzzy matching

        Returns:
            Dictionary with code, system, display, target, indication, evidence_level
        """
        drug_lower = drug_name.lower().strip()

        # Exact match
        if drug_lower in self.rxnorm_drugs:
            return self.rxnorm_drugs[drug_lower]

        # Fuzzy match
        if fuzzy:
            matches = get_close_matches(
                drug_lower,
                self.rxnorm_drugs.keys(),
                n=1,
                cutoff=cutoff
            )
            if matches:
                return self.rxnorm_drugs[matches[0]]

        return None

    def map_gene(self, gene_name: str) -> Optional[Dict]:
        """
        Map gene symbol to HGNC code

        Args:
            gene_name: Gene symbol (e.g., "EGFR", "ALK::EML4")

        Returns:
            Dictionary with code, system, name, chromosome, cancer_types, actionable
        """
        gene_upper = gene_name.upper().strip()

        # Handle fusion genes - map first gene
        if '::' in gene_upper:
            gene_upper = gene_upper.split('::')[0]

        return self.hgnc_genes.get(gene_upper)

    def map_variant_classification(self, classification_text: str) -> Optional[Dict]:
        """
        Map Italian/English variant classification to standard terms

        Args:
            classification_text: Classification text (Italian or English)

        Returns:
            Dictionary with code, display, acmg_class
        """
        class_lower = classification_text.lower().strip()

        variant_class = self.snomed_ct_terms.get('variant_classification', {})

        # Direct lookup
        if class_lower in variant_class:
            return variant_class[class_lower]

        # Partial match for Italian terms
        for key, value in variant_class.items():
            if key in class_lower or class_lower in key:
                return value

        return None

    def get_drugs_by_target(self, gene: str) -> List[Dict]:
        """
        Get all drugs targeting a specific gene

        Args:
            gene: Gene symbol

        Returns:
            List of drug dictionaries with their information
        """
        gene_upper = gene.upper()
        matching_drugs = []

        for drug_name, drug_info in self.rxnorm_drugs.items():
            targets = drug_info.get('target', [])
            if gene_upper in targets:
                matching_drugs.append({
                    'name': drug_name,
                    **drug_info
                })

        return matching_drugs

    def get_actionable_genes(self) -> List[str]:
        """
        Get list of all actionable genes (genes with targeted therapies)

        Returns:
            List of gene symbols
        """
        return [
            gene for gene, info in self.hgnc_genes.items()
            if info.get('actionable', False)
        ]

    def get_metadata(self, vocab_type: str) -> Dict:
        """
        Get metadata for a specific vocabulary

        Args:
            vocab_type: One of 'icd_o', 'rxnorm', 'hgnc', 'snomed_ct'

        Returns:
            Metadata dictionary
        """
        return self.metadata.get(vocab_type, {})

    def reload(self):
        """Reload all vocabularies from disk (useful after updates)"""
        self._load_vocabularies()

    def get_vocabulary_stats(self) -> Dict:
        """
        Get statistics about loaded vocabularies

        Returns:
            Dictionary with counts and metadata
        """
        return {
            'icd_o_diagnoses_count': len(self.icd_o_diagnoses),
            'rxnorm_drugs_count': len(self.rxnorm_drugs),
            'hgnc_genes_count': len(self.hgnc_genes),
            'actionable_genes_count': len(self.get_actionable_genes()),
            'metadata': self.metadata
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize loader
    loader = VocabularyLoader()

    # Test diagnosis mapping
    print("=== Testing Diagnosis Mapping ===")
    diagnosis = loader.map_diagnosis("adenocarcinoma polmonare")
    print(f"Adenocarcinoma polmonare: {diagnosis}")

    # Test drug mapping
    print("\n=== Testing Drug Mapping ===")
    drug = loader.map_drug("osimertinib")
    print(f"Osimertinib: {drug}")

    # Test gene mapping
    print("\n=== Testing Gene Mapping ===")
    gene = loader.map_gene("EGFR")
    print(f"EGFR: {gene}")

    # Test fusion gene
    fusion = loader.map_gene("ALK::EML4")
    print(f"ALK::EML4 fusion: {fusion}")

    # Test variant classification
    print("\n=== Testing Variant Classification ===")
    classification = loader.map_variant_classification("patogenetica")
    print(f"Patogenetica: {classification}")

    # Get drugs by target
    print("\n=== Testing Drugs by Target ===")
    egfr_drugs = loader.get_drugs_by_target("EGFR")
    print(f"EGFR-targeted drugs: {[d['name'] for d in egfr_drugs]}")

    # Get actionable genes
    print("\n=== Actionable Genes ===")
    actionable = loader.get_actionable_genes()
    print(f"Actionable genes ({len(actionable)}): {actionable[:10]}...")

    # Get stats
    print("\n=== Vocabulary Statistics ===")
    stats = loader.get_vocabulary_stats()
    print(json.dumps(stats, indent=2, default=str))
