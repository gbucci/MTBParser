#!/usr/bin/env python3
"""
Configuration Module - System configuration and settings
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """
    Global configuration for MTB Parser System
    """

    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    VOCABULARIES_DIR = BASE_DIR / 'vocabularies'
    CORE_DIR = BASE_DIR / 'core'
    MAPPERS_DIR = BASE_DIR / 'mappers'
    EXPORTERS_DIR = BASE_DIR / 'exporters'
    QUALITY_DIR = BASE_DIR / 'quality'
    UTILS_DIR = BASE_DIR / 'utils'

    # Vocabulary files
    VOCAB_ICD_O = VOCABULARIES_DIR / 'icd_o_diagnoses.json'
    VOCAB_RXNORM = VOCABULARIES_DIR / 'rxnorm_drugs.json'
    VOCAB_HGNC = VOCABULARIES_DIR / 'hgnc_genes.json'
    VOCAB_SNOMED = VOCABULARIES_DIR / 'snomed_ct_terms.json'

    # Parser settings
    DEFAULT_LANGUAGE = 'it'  # Italian
    SUPPORTED_LANGUAGES = ['it', 'en']

    # Quality thresholds
    MIN_COMPLETENESS_PCT = 60.0
    MIN_VARIANT_CLASSIFICATION_PCT = 50.0
    MIN_GENE_MAPPING_PCT = 80.0
    MIN_DRUG_MAPPING_PCT = 80.0

    # TMB thresholds (mutations/Mb)
    TMB_HIGH_THRESHOLD = 10.0
    TMB_MEDIUM_THRESHOLD = 6.0
    TMB_LOW_THRESHOLD = 0.0

    # Export settings
    EXPORT_PRETTY_JSON = True
    EXPORT_INCLUDE_RAW = False
    CSV_DELIMITER = ','
    CSV_ENCODING = 'utf-8'

    # FHIR settings
    FHIR_BASE_URL = "urn:uuid:"
    FHIR_VERSION = "R4"

    # Phenopackets settings
    PHENOPACKETS_SCHEMA_VERSION = "2.0"

    # OMOP settings
    OMOP_CDM_VERSION = "5.4"

    # Logging
    LOG_LEVEL = os.getenv('MTB_PARSER_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def get_vocab_path(cls, vocab_type: str) -> Path:
        """Get path to vocabulary file"""
        vocab_paths = {
            'icd_o': cls.VOCAB_ICD_O,
            'rxnorm': cls.VOCAB_RXNORM,
            'hgnc': cls.VOCAB_HGNC,
            'snomed': cls.VOCAB_SNOMED
        }
        return vocab_paths.get(vocab_type.lower())

    @classmethod
    def validate_paths(cls) -> bool:
        """Validate that required paths exist"""
        required_paths = [
            cls.VOCABULARIES_DIR,
            cls.VOCAB_ICD_O,
            cls.VOCAB_RXNORM,
            cls.VOCAB_HGNC,
            cls.VOCAB_SNOMED
        ]

        all_exist = True
        for path in required_paths:
            if not path.exists():
                print(f"Warning: Required path does not exist: {path}")
                all_exist = False

        return all_exist


# Example usage
if __name__ == "__main__":
    print("=== MTB Parser Configuration ===\n")

    print(f"Base Directory: {Config.BASE_DIR}")
    print(f"Vocabularies Directory: {Config.VOCABULARIES_DIR}")
    print(f"\nVocabulary Files:")
    print(f"  ICD-O: {Config.VOCAB_ICD_O}")
    print(f"  RxNorm: {Config.VOCAB_RXNORM}")
    print(f"  HGNC: {Config.VOCAB_HGNC}")
    print(f"  SNOMED-CT: {Config.VOCAB_SNOMED}")

    print(f"\nQuality Thresholds:")
    print(f"  Min Completeness: {Config.MIN_COMPLETENESS_PCT}%")
    print(f"  Min Gene Mapping: {Config.MIN_GENE_MAPPING_PCT}%")
    print(f"  TMB High: ≥{Config.TMB_HIGH_THRESHOLD} mut/Mb")

    print(f"\nStandards:")
    print(f"  FHIR: {Config.FHIR_VERSION}")
    print(f"  Phenopackets: v{Config.PHENOPACKETS_SCHEMA_VERSION}")
    print(f"  OMOP CDM: v{Config.OMOP_CDM_VERSION}")

    print(f"\nValidating paths...")
    if Config.validate_paths():
        print("✅ All required paths exist")
    else:
        print("⚠️  Some paths are missing")
