#!/usr/bin/env python3
"""
Text Utilities - Text preprocessing and cleaning for MTB reports
"""

import re
from typing import Optional


class TextPreprocessor:
    """
    Utilities for preprocessing and cleaning clinical text
    """

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace (multiple spaces/tabs to single space)"""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def remove_extra_newlines(text: str) -> str:
        """Remove excessive newlines (more than 2 consecutive)"""
        return re.sub(r'\n{3,}', '\n\n', text)

    @staticmethod
    def normalize_italian_chars(text: str) -> str:
        """Normalize Italian special characters for better matching"""
        # Common Italian character normalizations
        replacements = {
            'à': 'a', 'è': 'e', 'é': 'e', 'ì': 'i',
            'ò': 'o', 'ù': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def extract_sections(text: str) -> dict:
        """
        Extract common report sections

        Returns:
            Dictionary with section names as keys
        """
        sections = {}

        # Define section headers
        section_patterns = {
            'patient_info': r'(?:INFORMAZIONI PAZIENTE|PATIENT INFO|DATI PAZIENTE)(.*?)(?=\n[A-Z\s]{10,}|\Z)',
            'diagnosis': r'(?:DIAGNOSI|DIAGNOSIS)(.*?)(?=\n[A-Z\s]{10,}|\Z)',
            'genomic_analysis': r'(?:ANALISI GENOMICA|GENOMIC ANALYSIS|VARIANTI)(.*?)(?=\n[A-Z\s]{10,}|\Z)',
            'recommendations': r'(?:RACCOMANDAZIONI|RECOMMENDATIONS|TERAPIA)(.*?)(?=\n[A-Z\s]{10,}|\Z)',
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()

        return sections

    @staticmethod
    def clean_gene_name(gene: str) -> str:
        """Clean and normalize gene name"""
        # Remove common prefixes/suffixes
        gene = gene.strip().upper()
        gene = re.sub(r'^GENE[\s:]', '', gene, flags=re.IGNORECASE)
        return gene

    @staticmethod
    def clean_drug_name(drug: str) -> str:
        """Clean and normalize drug name"""
        drug = drug.strip().lower()
        # Remove common suffixes like mg, dosage info
        drug = re.sub(r'\s+\d+\s*mg.*$', '', drug)
        drug = re.sub(r'\s+\(.*\)$', '', drug)  # Remove parenthetical info
        return drug

    @staticmethod
    def preprocess_report(text: str) -> str:
        """
        Full preprocessing pipeline for MTB report

        Args:
            text: Raw report text

        Returns:
            Cleaned and normalized text
        """
        # Remove excessive whitespace
        text = TextPreprocessor.normalize_whitespace(text)

        # Remove extra newlines
        text = TextPreprocessor.remove_extra_newlines(text)

        # Remove common artifacts
        text = re.sub(r'Page \d+ of \d+', '', text)  # Page numbers
        text = re.sub(r'\f', '\n', text)  # Form feed to newline

        return text.strip()


# Example usage
if __name__ == "__main__":
    sample_text = """
    Page 1 of 3


    INFORMAZIONI     PAZIENTE

    Paziente:   12345
    Età:  65   anni



    DIAGNOSI   CLINICA

    Adenocarcinoma    polmonare


    """

    print("=== Text Preprocessing Test ===\n")
    print("Original:")
    print(repr(sample_text))

    preprocessor = TextPreprocessor()
    cleaned = preprocessor.preprocess_report(sample_text)

    print("\nCleaned:")
    print(repr(cleaned))

    print("\nSections extracted:")
    sections = preprocessor.extract_sections(sample_text)
    for name, content in sections.items():
        print(f"  {name}: {content[:50]}...")
