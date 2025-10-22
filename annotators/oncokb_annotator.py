#!/usr/bin/env python3
"""
OncoKB (Precision Oncology Knowledge Base) Annotator
Integrates with OncoKB for variant therapeutic/prognostic annotation

OncoKB Levels of Evidence:
- Level 1: FDA-recognized biomarker predictive of response to FDA-approved drug
- Level 2: Standard care biomarker recommended by NCCN or other guidelines
- Level 3A: Compelling clinical evidence for drug
- Level 3B: Standard care for different tumor type or preclinical evidence
- Level 4: Compelling biological evidence
- Level R1: Standard care resistance biomarker
- Level R2: Investigational resistance biomarker

References:
- OncoKB: https://www.oncokb.org/
- API: https://www.oncokb.org/api/
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class OncoKBLevel(Enum):
    """OncoKB evidence levels"""
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3A = "LEVEL_3A"
    LEVEL_3B = "LEVEL_3B"
    LEVEL_4 = "LEVEL_4"
    LEVEL_R1 = "LEVEL_R1"  # Resistance
    LEVEL_R2 = "LEVEL_R2"  # Resistance


@dataclass
class OncoKBTreatment:
    """OncoKB treatment recommendation"""
    drug_names: List[str]
    level: str
    cancer_type: str
    indication: str
    fda_approved: bool
    evidence_pmids: List[str] = field(default_factory=list)
    abstract: Optional[str] = None


@dataclass
class OncoKBAnnotation:
    """Complete OncoKB annotation for a variant"""
    gene: str
    variant: str
    oncogenic: Optional[str] = None  # Oncogenic, Likely Oncogenic, VUS, Likely Neutral
    mutation_effect: Optional[str] = None  # Gain-of-function, Loss-of-function, etc.
    treatments: List[OncoKBTreatment] = field(default_factory=list)
    diagnostic_implications: List[str] = field(default_factory=list)
    prognostic_implications: List[str] = field(default_factory=list)
    oncokb_url: Optional[str] = None
    highest_level: Optional[str] = None


class OncoKBAnnotator:
    """
    Annotator for querying OncoKB for variant therapeutic significance

    Note: This is a mock implementation. For production use:
    1. Register for OncoKB API token at https://www.oncokb.org/apiAccess
    2. Set environment variable: ONCOKB_API_TOKEN
    3. Implement actual API calls with authentication
    4. Add rate limiting (OncoKB has usage limits)
    5. Cache results to minimize API calls
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize OncoKB annotator

        Args:
            api_token: OncoKB API token (get from https://www.oncokb.org/apiAccess)
        """
        self.api_token = api_token
        self.api_url = "https://www.oncokb.org/api/v1"
        self.cache = {}

    def annotate_variant(
        self,
        gene: str,
        variant: str,
        tumor_type: Optional[str] = None,
        consequence: Optional[str] = None
    ) -> OncoKBAnnotation:
        """
        Annotate variant with OncoKB therapeutic implications

        Args:
            gene: Gene symbol (e.g., "EGFR")
            variant: Variant notation (e.g., "L858R")
            tumor_type: Cancer type (e.g., "Lung Adenocarcinoma")
            consequence: Mutation type (e.g., "missense_variant")

        Returns:
            OncoKBAnnotation with therapeutic levels
        """
        cache_key = f"{gene}_{variant}_{tumor_type}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query OncoKB (mock implementation)
        annotation = self._query_oncokb_mock(gene, variant, tumor_type, consequence)

        self.cache[cache_key] = annotation
        return annotation

    def _query_oncokb_mock(
        self,
        gene: str,
        variant: str,
        tumor_type: Optional[str],
        consequence: Optional[str]
    ) -> OncoKBAnnotation:
        """
        Mock OncoKB database with common actionable variants

        In production, replace with actual OncoKB API call:

        GET /annotate/mutations/byProteinChange?hugoSymbol={gene}&alteration={variant}&tumorType={tumor}
        Headers: Authorization: Bearer {token}
        """

        # Mock database of actionable variants
        oncokb_db = {
            ("EGFR", "L858R"): OncoKBAnnotation(
                gene="EGFR",
                variant="L858R",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/EGFR/L858R",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Osimertinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="Approved for EGFR L858R mutant NSCLC",
                        fda_approved=True,
                        evidence_pmids=["24065731", "26522272"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Gefitinib", "Erlotinib", "Afatinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="First-line treatment for EGFR-mutant NSCLC",
                        fda_approved=True,
                        evidence_pmids=["14645423", "15118073"]
                    )
                ],
                diagnostic_implications=["EGFR mutation testing recommended for NSCLC"],
                prognostic_implications=["Better response to EGFR TKIs"]
            ),
            ("EGFR", "T790M"): OncoKBAnnotation(
                gene="EGFR",
                variant="T790M",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/EGFR/T790M",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Osimertinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="T790M resistance mutation",
                        fda_approved=True,
                        evidence_pmids=["26522272"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Gefitinib", "Erlotinib"],
                        level="LEVEL_R1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="Resistance to first-generation EGFR TKIs",
                        fda_approved=False,
                        evidence_pmids=["15758012"]
                    )
                ]
            ),
            ("BRAF", "V600E"): OncoKBAnnotation(
                gene="BRAF",
                variant="V600E",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/BRAF/V600E",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Dabrafenib", "Trametinib"],
                        level="LEVEL_1",
                        cancer_type="Melanoma",
                        indication="BRAF V600E mutant melanoma",
                        fda_approved=True,
                        evidence_pmids=["22663011", "25399551"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Vemurafenib"],
                        level="LEVEL_1",
                        cancer_type="Melanoma",
                        indication="BRAF V600E mutant melanoma",
                        fda_approved=True,
                        evidence_pmids=["21639808"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Encorafenib", "Binimetinib"],
                        level="LEVEL_1",
                        cancer_type="Colorectal Cancer",
                        indication="BRAF V600E mutant CRC",
                        fda_approved=True,
                        evidence_pmids=["31566309"]
                    )
                ],
                diagnostic_implications=["BRAF V600E testing for melanoma and CRC"],
                prognostic_implications=["Poor prognosis in CRC", "Good response to BRAF inhibitors"]
            ),
            ("KRAS", "G12C"): OncoKBAnnotation(
                gene="KRAS",
                variant="G12C",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/KRAS/G12C",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Sotorasib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="KRAS G12C mutant NSCLC",
                        fda_approved=True,
                        evidence_pmids=["33658825"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Adagrasib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="KRAS G12C mutant NSCLC",
                        fda_approved=True,
                        evidence_pmids=["36070710"]
                    )
                ]
            ),
            ("KRAS", "G12D"): OncoKBAnnotation(
                gene="KRAS",
                variant="G12D",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_R1",
                oncokb_url="https://www.oncokb.org/gene/KRAS/G12D",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Cetuximab", "Panitumumab"],
                        level="LEVEL_R1",
                        cancer_type="Colorectal Cancer",
                        indication="Resistance to anti-EGFR therapy",
                        fda_approved=False,
                        evidence_pmids=["18316791"]
                    )
                ],
                diagnostic_implications=["KRAS testing required before anti-EGFR therapy in CRC"]
            ),
            ("ALK", "Fusion"): OncoKBAnnotation(
                gene="ALK",
                variant="Fusion",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/ALK",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Alectinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="ALK fusion-positive NSCLC",
                        fda_approved=True,
                        evidence_pmids=["28586279"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Crizotinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="ALK fusion-positive NSCLC",
                        fda_approved=True,
                        evidence_pmids=["23724913"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Ceritinib", "Brigatinib", "Lorlatinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="ALK fusion-positive NSCLC",
                        fda_approved=True,
                        evidence_pmids=["24675041", "28475456"]
                    )
                ]
            ),
            ("RET", "Fusion"): OncoKBAnnotation(
                gene="RET",
                variant="Fusion",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/RET",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Selpercatinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="RET fusion-positive NSCLC",
                        fda_approved=True,
                        evidence_pmids=["32846060"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Pralsetinib"],
                        level="LEVEL_1",
                        cancer_type="Non-Small Cell Lung Cancer",
                        indication="RET fusion-positive NSCLC",
                        fda_approved=True,
                        evidence_pmids=["32846062"]
                    )
                ]
            ),
            ("BRCA1", "Loss"): OncoKBAnnotation(
                gene="BRCA1",
                variant="Loss of Function",
                oncogenic="Oncogenic",
                mutation_effect="Loss-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/BRCA1",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Olaparib"],
                        level="LEVEL_1",
                        cancer_type="Ovarian Cancer",
                        indication="BRCA-mutated ovarian cancer",
                        fda_approved=True,
                        evidence_pmids=["24429876"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Niraparib", "Rucaparib"],
                        level="LEVEL_1",
                        cancer_type="Ovarian Cancer",
                        indication="BRCA-mutated ovarian cancer",
                        fda_approved=True,
                        evidence_pmids=["27074132", "27097256"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Talazoparib"],
                        level="LEVEL_1",
                        cancer_type="Breast Cancer",
                        indication="BRCA-mutated breast cancer",
                        fda_approved=True,
                        evidence_pmids=["30110579"]
                    )
                ]
            ),
            ("ERBB2", "Amplification"): OncoKBAnnotation(
                gene="ERBB2",
                variant="Amplification",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/ERBB2",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Trastuzumab"],
                        level="LEVEL_1",
                        cancer_type="Breast Cancer",
                        indication="HER2-positive breast cancer",
                        fda_approved=True,
                        evidence_pmids=["11231778"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Pertuzumab", "Trastuzumab"],
                        level="LEVEL_1",
                        cancer_type="Breast Cancer",
                        indication="HER2-positive metastatic breast cancer",
                        fda_approved=True,
                        evidence_pmids=["22149876"]
                    ),
                    OncoKBTreatment(
                        drug_names=["Trastuzumab Deruxtecan"],
                        level="LEVEL_1",
                        cancer_type="Breast Cancer",
                        indication="HER2-positive/low breast cancer",
                        fda_approved=True,
                        evidence_pmids=["35213103"]
                    )
                ]
            ),
            ("PIK3CA", "H1047R"): OncoKBAnnotation(
                gene="PIK3CA",
                variant="H1047R",
                oncogenic="Oncogenic",
                mutation_effect="Gain-of-function",
                highest_level="LEVEL_1",
                oncokb_url="https://www.oncokb.org/gene/PIK3CA/H1047R",
                treatments=[
                    OncoKBTreatment(
                        drug_names=["Alpelisib"],
                        level="LEVEL_1",
                        cancer_type="Breast Cancer",
                        indication="PIK3CA-mutated HR+ breast cancer",
                        fda_approved=True,
                        evidence_pmids=["31091374"]
                    )
                ]
            ),
        }

        # Normalize for lookup
        variant_norm = variant.upper().replace("P.", "").replace("C.", "")

        # Try exact match
        for (db_gene, db_variant), annotation in oncokb_db.items():
            if gene.upper() == db_gene and variant_norm in db_variant.upper():
                return annotation

        # Return empty annotation
        return OncoKBAnnotation(
            gene=gene,
            variant=variant,
            oncogenic="Unknown",
            mutation_effect="Unknown",
            treatments=[],
            oncokb_url=f"https://www.oncokb.org/gene/{gene}"
        )

    def get_therapeutic_summary(self, annotation: OncoKBAnnotation) -> Dict:
        """
        Generate therapeutic summary from OncoKB annotation

        Args:
            annotation: OncoKBAnnotation

        Returns:
            Summary dict with actionable information
        """
        if not annotation.treatments:
            return {
                "is_actionable": False,
                "highest_level": None,
                "fda_approved_drugs": [],
                "all_drugs": [],
                "resistance_drugs": []
            }

        # Extract drugs by level
        fda_approved = []
        all_drugs = []
        resistance_drugs = []

        for treatment in annotation.treatments:
            if treatment.fda_approved:
                fda_approved.extend(treatment.drug_names)

            if "R1" in treatment.level or "R2" in treatment.level:
                resistance_drugs.extend(treatment.drug_names)
            else:
                all_drugs.extend(treatment.drug_names)

        return {
            "is_actionable": annotation.highest_level in ["LEVEL_1", "LEVEL_2", "LEVEL_3A"],
            "highest_level": annotation.highest_level,
            "oncogenic": annotation.oncogenic,
            "mutation_effect": annotation.mutation_effect,
            "fda_approved_drugs": list(set(fda_approved)),
            "all_drugs": list(set(all_drugs)),
            "resistance_drugs": list(set(resistance_drugs)),
            "oncokb_url": annotation.oncokb_url
        }


# Example usage
if __name__ == "__main__":
    annotator = OncoKBAnnotator()

    test_variants = [
        ("EGFR", "L858R", "NSCLC"),
        ("BRAF", "V600E", "Melanoma"),
        ("KRAS", "G12C", "NSCLC"),
        ("ALK", "Fusion", "NSCLC"),
        ("BRCA1", "Loss", "Ovarian Cancer"),
    ]

    for gene, variant, cancer in test_variants:
        print(f"\n{'='*70}")
        print(f"OncoKB Annotation: {gene} {variant} in {cancer}")
        print('='*70)

        annotation = annotator.annotate_variant(gene, variant, cancer)
        summary = annotator.get_therapeutic_summary(annotation)

        print(f"\nOncogenic: {annotation.oncogenic}")
        print(f"Mutation Effect: {annotation.mutation_effect}")
        print(f"Highest Level: {summary['highest_level']}")
        print(f"Actionable: {summary['is_actionable']}")

        if summary['fda_approved_drugs']:
            print(f"\nFDA-Approved Drugs:")
            for drug in summary['fda_approved_drugs']:
                print(f"  - {drug}")

        if summary['resistance_drugs']:
            print(f"\nResistance to:")
            for drug in summary['resistance_drugs']:
                print(f"  - {drug}")

        print(f"\nURL: {annotation.oncokb_url}")
