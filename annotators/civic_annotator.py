#!/usr/bin/env python3
"""
CIViC (Clinical Interpretations of Variants in Cancer) Annotator
Integrates with CIViC API for variant clinical significance annotation

CIViC provides curated cancer variant interpretations with evidence levels:
- Level A: FDA/EMA approved therapies
- Level B: Clinical evidence in multiple studies
- Level C: Case reports or preclinical evidence
- Level D: Preclinical evidence only
- Level E: Indirect evidence

References:
- CIViC API: https://civicdb.org/api/graphql
- Documentation: https://docs.civicdb.org/
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CIViCEvidence:
    """CIViC evidence item"""
    evidence_id: str
    evidence_type: str  # Diagnostic, Prognostic, Predictive
    evidence_level: str  # A, B, C, D, E
    evidence_direction: str  # Supports, Does not support
    clinical_significance: str  # Sensitivity/Response, Resistance, etc.
    drug_names: List[str]
    disease: str
    source_type: str  # PubMed, ASCO, etc.
    citation: str
    rating: Optional[float] = None


@dataclass
class CIViCVariantAnnotation:
    """Complete CIViC annotation for a variant"""
    gene: str
    variant_name: str
    civic_id: Optional[str] = None
    variant_types: List[str] = None
    evidence_items: List[CIViCEvidence] = None
    civic_score: Optional[float] = None
    variant_url: Optional[str] = None

    def __post_init__(self):
        if self.variant_types is None:
            self.variant_types = []
        if self.evidence_items is None:
            self.evidence_items = []


class CIViCAnnotator:
    """
    Annotator for querying CIViC database for variant clinical significance

    Note: This is a mock implementation. For production use:
    1. Register for CIViC API access
    2. Implement GraphQL queries to CIViC API
    3. Add rate limiting and caching
    4. Handle API authentication if required
    """

    def __init__(self, api_url: str = "https://civicdb.org/api/graphql"):
        """
        Initialize CIViC annotator

        Args:
            api_url: CIViC GraphQL API endpoint
        """
        self.api_url = api_url
        self.cache = {}  # Simple in-memory cache

    def annotate_variant(self, gene: str, variant: str, disease: Optional[str] = None) -> CIViCVariantAnnotation:
        """
        Annotate a variant with CIViC clinical evidence

        Args:
            gene: Gene symbol (e.g., "EGFR", "BRAF")
            variant: Variant notation (e.g., "L858R", "V600E")
            disease: Optional disease context (e.g., "Lung Adenocarcinoma")

        Returns:
            CIViCVariantAnnotation with evidence items
        """
        cache_key = f"{gene}_{variant}_{disease or 'any'}"

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query CIViC (mock implementation with common variants)
        annotation = self._query_civic_mock(gene, variant, disease)

        # Cache result
        self.cache[cache_key] = annotation

        return annotation

    def _query_civic_mock(self, gene: str, variant: str, disease: Optional[str] = None) -> CIViCVariantAnnotation:
        """
        Mock CIViC query with common actionable variants

        In production, replace with actual CIViC GraphQL query:

        query {
          variants(entrezSymbol: "EGFR", name: "L858R") {
            id
            name
            variantTypes { name }
            evidenceItems {
              id
              evidenceType
              evidenceLevel
              clinicalSignificance
              drugs { name }
              disease { name }
            }
          }
        }
        """

        # Mock database of common actionable variants
        civic_db = {
            ("EGFR", "L858R"): CIViCVariantAnnotation(
                gene="EGFR",
                variant_name="L858R",
                civic_id="VID12",
                variant_types=["Missense Variant"],
                civic_score=85.5,
                variant_url="https://civicdb.org/variants/12",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID123",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Osimertinib", "Gefitinib", "Erlotinib", "Afatinib"],
                        disease="Lung Adenocarcinoma",
                        source_type="PubMed",
                        citation="PMID:24065731",
                        rating=4.5
                    )
                ]
            ),
            ("EGFR", "T790M"): CIViCVariantAnnotation(
                gene="EGFR",
                variant_name="T790M",
                civic_id="VID13",
                variant_types=["Missense Variant"],
                civic_score=90.0,
                variant_url="https://civicdb.org/variants/13",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID124",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Osimertinib"],
                        disease="Non-Small Cell Lung Cancer",
                        source_type="PubMed",
                        citation="PMID:26522272",
                        rating=5.0
                    ),
                    CIViCEvidence(
                        evidence_id="EID125",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Resistance",
                        drug_names=["Gefitinib", "Erlotinib"],
                        disease="Non-Small Cell Lung Cancer",
                        source_type="PubMed",
                        citation="PMID:15758012",
                        rating=4.8
                    )
                ]
            ),
            ("BRAF", "V600E"): CIViCVariantAnnotation(
                gene="BRAF",
                variant_name="V600E",
                civic_id="VID24",
                variant_types=["Missense Variant"],
                civic_score=92.3,
                variant_url="https://civicdb.org/variants/24",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID200",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Vemurafenib", "Dabrafenib", "Encorafenib"],
                        disease="Melanoma",
                        source_type="FDA",
                        citation="FDA Label",
                        rating=5.0
                    ),
                    CIViCEvidence(
                        evidence_id="EID201",
                        evidence_type="Predictive",
                        evidence_level="B",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Dabrafenib", "Trametinib"],
                        disease="Colorectal Cancer",
                        source_type="PubMed",
                        citation="PMID:25399551",
                        rating=4.2
                    )
                ]
            ),
            ("KRAS", "G12C"): CIViCVariantAnnotation(
                gene="KRAS",
                variant_name="G12C",
                civic_id="VID45",
                variant_types=["Missense Variant"],
                civic_score=88.0,
                variant_url="https://civicdb.org/variants/45",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID300",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Sotorasib", "Adagrasib"],
                        disease="Non-Small Cell Lung Cancer",
                        source_type="FDA",
                        citation="FDA Approval 2021",
                        rating=5.0
                    )
                ]
            ),
            ("ALK", "fusion"): CIViCVariantAnnotation(
                gene="ALK",
                variant_name="Fusion",
                civic_id="VID78",
                variant_types=["Gene Fusion"],
                civic_score=95.0,
                variant_url="https://civicdb.org/variants/78",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID400",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Crizotinib", "Alectinib", "Ceritinib", "Brigatinib", "Lorlatinib"],
                        disease="Non-Small Cell Lung Cancer",
                        source_type="FDA",
                        citation="FDA Label",
                        rating=5.0
                    )
                ]
            ),
            ("RET", "fusion"): CIViCVariantAnnotation(
                gene="RET",
                variant_name="Fusion",
                civic_id="VID89",
                variant_types=["Gene Fusion"],
                civic_score=90.5,
                variant_url="https://civicdb.org/variants/89",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID450",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Selpercatinib", "Pralsetinib"],
                        disease="Non-Small Cell Lung Cancer",
                        source_type="FDA",
                        citation="FDA Approval 2020",
                        rating=5.0
                    )
                ]
            ),
            ("BRCA1", "Loss"): CIViCVariantAnnotation(
                gene="BRCA1",
                variant_name="Loss of Function",
                civic_id="VID150",
                variant_types=["Loss of Function"],
                civic_score=87.0,
                variant_url="https://civicdb.org/variants/150",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID500",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Olaparib", "Niraparib", "Rucaparib", "Talazoparib"],
                        disease="Ovarian Cancer",
                        source_type="FDA",
                        citation="FDA Label",
                        rating=5.0
                    )
                ]
            ),
            ("ERBB2", "amplification"): CIViCVariantAnnotation(
                gene="ERBB2",
                variant_name="Amplification",
                civic_id="VID200",
                variant_types=["Amplification"],
                civic_score=93.0,
                variant_url="https://civicdb.org/variants/200",
                evidence_items=[
                    CIViCEvidence(
                        evidence_id="EID600",
                        evidence_type="Predictive",
                        evidence_level="A",
                        evidence_direction="Supports",
                        clinical_significance="Sensitivity/Response",
                        drug_names=["Trastuzumab", "Pertuzumab", "Trastuzumab Deruxtecan"],
                        disease="Breast Cancer",
                        source_type="FDA",
                        citation="FDA Label",
                        rating=5.0
                    )
                ]
            ),
        }

        # Normalize variant name for matching
        variant_normalized = variant.upper().replace("P.", "").replace("C.", "")

        # Try exact match
        for (db_gene, db_variant), annotation in civic_db.items():
            if gene.upper() == db_gene and variant_normalized in db_variant.upper():
                return annotation

        # Return empty annotation if not found
        return CIViCVariantAnnotation(
            gene=gene,
            variant_name=variant,
            civic_id=None,
            variant_types=[],
            evidence_items=[],
            civic_score=None,
            variant_url=None
        )

    def get_evidence_summary(self, annotation: CIViCVariantAnnotation) -> Dict:
        """
        Generate summary of evidence for a variant

        Args:
            annotation: CIViCVariantAnnotation

        Returns:
            Dictionary with evidence summary
        """
        if not annotation.evidence_items:
            return {
                "has_evidence": False,
                "evidence_count": 0,
                "max_evidence_level": None,
                "actionable_drugs": [],
                "resistance_drugs": []
            }

        # Extract actionable drugs
        actionable_drugs = set()
        resistance_drugs = set()

        for evidence in annotation.evidence_items:
            if evidence.clinical_significance in ["Sensitivity/Response", "Sensitivity"]:
                actionable_drugs.update(evidence.drug_names)
            elif evidence.clinical_significance == "Resistance":
                resistance_drugs.update(evidence.drug_names)

        # Determine max evidence level (A > B > C > D > E)
        levels = [e.evidence_level for e in annotation.evidence_items]
        level_order = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
        max_level = min(levels, key=lambda x: level_order.get(x, 99)) if levels else None

        return {
            "has_evidence": True,
            "evidence_count": len(annotation.evidence_items),
            "max_evidence_level": max_level,
            "actionable_drugs": list(actionable_drugs),
            "resistance_drugs": list(resistance_drugs),
            "civic_url": annotation.variant_url,
            "civic_score": annotation.civic_score
        }


# Example usage
if __name__ == "__main__":
    annotator = CIViCAnnotator()

    # Test annotations
    test_variants = [
        ("EGFR", "L858R", "Lung Adenocarcinoma"),
        ("BRAF", "V600E", "Melanoma"),
        ("KRAS", "G12C", "NSCLC"),
        ("ALK", "fusion", "NSCLC"),
    ]

    for gene, variant, disease in test_variants:
        print(f"\n{'='*60}")
        print(f"Annotating: {gene} {variant} in {disease}")
        print('='*60)

        annotation = annotator.annotate_variant(gene, variant, disease)
        summary = annotator.get_evidence_summary(annotation)

        print(f"\nCIViC ID: {annotation.civic_id}")
        print(f"CIViC Score: {annotation.civic_score}")
        print(f"Evidence Items: {summary['evidence_count']}")
        print(f"Max Evidence Level: {summary['max_evidence_level']}")
        print(f"Actionable Drugs: {', '.join(summary['actionable_drugs'])}")

        if summary['resistance_drugs']:
            print(f"Resistance to: {', '.join(summary['resistance_drugs'])}")

        print(f"\nURL: {annotation.variant_url}")
