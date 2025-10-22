#!/usr/bin/env python3
"""
Combined Clinical Annotator
Integrates multiple clinical evidence sources (CIViC + OncoKB + ESCAT) for comprehensive variant annotation
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .civic_annotator import CIViCAnnotator, CIViCVariantAnnotation
from .oncokb_annotator import OncoKBAnnotator, OncoKBAnnotation
from .escat_annotator import ESCATAnnotator, ESCATAnnotation
from .annotator_config import AnnotatorConfig, AnnotatorType


@dataclass
class CombinedEvidence:
    """Combined evidence from multiple sources"""
    gene: str
    variant: str

    # Source annotations
    civic_annotation: Optional[CIViCVariantAnnotation] = None
    oncokb_annotation: Optional[OncoKBAnnotation] = None
    escat_annotation: Optional[ESCATAnnotation] = None

    # Aggregated evidence
    is_actionable: bool = False
    actionability_score: float = 0.0  # 0-100 score

    # Therapeutic recommendations
    fda_approved_therapies: List[str] = field(default_factory=list)
    guideline_therapies: List[str] = field(default_factory=list)
    investigational_therapies: List[str] = field(default_factory=list)
    resistance_therapies: List[str] = field(default_factory=list)

    # Evidence levels
    highest_evidence_level: Optional[str] = None  # OncoKB, CIViC, or ESCAT level
    evidence_sources: List[str] = field(default_factory=list)

    # Clinical context
    oncogenic_classification: Optional[str] = None
    mutation_effect: Optional[str] = None

    # ESCAT classification
    escat_tier: Optional[str] = None
    escat_score: float = 0.0

    # Links
    civic_url: Optional[str] = None
    oncokb_url: Optional[str] = None


class CombinedAnnotator:
    """
    Combined annotator integrating CIViC, OncoKB, and ESCAT for comprehensive variant interpretation

    Supports configurable annotation sources based on license availability and user preferences.
    """

    def __init__(
        self,
        config: Optional[AnnotatorConfig] = None,
        oncokb_token: Optional[str] = None  # Deprecated, use config instead
    ):
        """
        Initialize combined annotator with configurable sources

        Args:
            config: AnnotatorConfig specifying which sources to use.
                   If None, uses free sources only (CIViC + ESCAT)
            oncokb_token: (Deprecated) OncoKB API token. Use config.oncokb_api_key instead.

        Examples:
            # Free sources only (default)
            annotator = CombinedAnnotator()

            # ESCAT only
            annotator = CombinedAnnotator(config=AnnotatorConfig.escat_only())

            # All sources with OncoKB
            config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")
            annotator = CombinedAnnotator(config=config)

            # European clinical (ESCAT + CIViC)
            annotator = CombinedAnnotator(config=AnnotatorConfig.european_clinical())
        """
        # Handle deprecated oncokb_token parameter
        if config is None:
            if oncokb_token is not None:
                import warnings
                warnings.warn(
                    "oncokb_token parameter is deprecated. "
                    "Use config=AnnotatorConfig.all_sources(oncokb_api_key='...') instead",
                    DeprecationWarning
                )
                config = AnnotatorConfig.all_sources(oncokb_api_key=oncokb_token)
            else:
                # Default: free sources only
                config = AnnotatorConfig.free_only()

        self.config = config

        # Initialize only enabled annotators
        self.civic = None
        self.oncokb = None
        self.escat = None

        if config.is_enabled(AnnotatorType.CIVIC):
            self.civic = CIViCAnnotator()

        if config.is_enabled(AnnotatorType.ONCOKB):
            self.oncokb = OncoKBAnnotator(api_token=config.oncokb_api_key)

        if config.is_enabled(AnnotatorType.ESCAT):
            self.escat = ESCATAnnotator()

    def annotate_variant(
        self,
        gene: str,
        variant: str,
        tumor_type: Optional[str] = None
    ) -> CombinedEvidence:
        """
        Annotate variant with combined evidence from CIViC, OncoKB, and ESCAT

        Args:
            gene: Gene symbol
            variant: Variant notation
            tumor_type: Cancer type for context-specific recommendations

        Returns:
            CombinedEvidence with aggregated annotations
        """
        # Query only enabled sources
        civic_ann = None
        oncokb_ann = None
        escat_ann = None

        if self.civic:
            civic_ann = self.civic.annotate_variant(gene, variant, tumor_type)

        if self.oncokb:
            oncokb_ann = self.oncokb.annotate_variant(gene, variant, tumor_type)

        if self.escat:
            escat_ann = self.escat.annotate_variant(gene, variant, tumor_type or "")

        # Create combined evidence
        combined = CombinedEvidence(
            gene=gene,
            variant=variant,
            civic_annotation=civic_ann,
            oncokb_annotation=oncokb_ann,
            escat_annotation=escat_ann
        )

        # Aggregate evidence from enabled sources
        self._aggregate_therapeutic_evidence(combined, civic_ann, oncokb_ann, escat_ann)
        self._calculate_actionability(combined, civic_ann, oncokb_ann, escat_ann)
        self._determine_oncogenicity(combined, civic_ann, oncokb_ann)

        # Set ESCAT classification if enabled
        if escat_ann:
            combined.escat_tier = escat_ann.highest_tier
            combined.escat_score = escat_ann.escat_score

        # Set URLs for enabled sources
        if civic_ann:
            combined.civic_url = civic_ann.variant_url
        if oncokb_ann:
            combined.oncokb_url = oncokb_ann.oncokb_url

        return combined

    def _aggregate_therapeutic_evidence(
        self,
        combined: CombinedEvidence,
        civic: Optional[CIViCVariantAnnotation],
        oncokb: Optional[OncoKBAnnotation],
        escat: Optional[ESCATAnnotation]
    ):
        """Aggregate therapeutic recommendations from enabled sources"""

        fda_approved = set()
        guideline = set()
        investigational = set()
        resistance = set()

        # Extract from CIViC (if enabled)
        if civic:
            for evidence in civic.evidence_items:
                drugs = evidence.drug_names

                if evidence.evidence_level == "A":
                    fda_approved.update(drugs)
                elif evidence.evidence_level == "B":
                    guideline.update(drugs)
                elif evidence.evidence_level in ["C", "D"]:
                    investigational.update(drugs)

                if evidence.clinical_significance == "Resistance":
                    resistance.update(drugs)

        # Extract from OncoKB (if enabled)
        if oncokb:
            for treatment in oncokb.treatments:
                drugs = treatment.drug_names
                level = treatment.level

                if level == "LEVEL_1" and treatment.fda_approved:
                    fda_approved.update(drugs)
                elif level in ["LEVEL_1", "LEVEL_2"]:
                    guideline.update(drugs)
                elif level in ["LEVEL_3A", "LEVEL_3B", "LEVEL_4"]:
                    investigational.update(drugs)
                elif "R1" in level or "R2" in level:
                    resistance.update(drugs)

        # Extract from ESCAT (if enabled)
        if escat:
            for evidence in escat.evidence_items:
                drugs = evidence.drug_names
                tier = evidence.tier

                if tier == "I-A":
                    fda_approved.update(drugs)
                elif tier in ["I-B", "I-C"]:
                    guideline.update(drugs)
                elif tier in ["II-A", "II-B", "III-A"]:
                    investigational.update(drugs)
                elif tier == "X":
                    resistance.update(drugs)

        # Set combined evidence
        combined.fda_approved_therapies = sorted(list(fda_approved))
        combined.guideline_therapies = sorted(list(guideline - fda_approved))
        combined.investigational_therapies = sorted(list(investigational - guideline - fda_approved))
        combined.resistance_therapies = sorted(list(resistance))

        # Track evidence sources (only enabled annotators with evidence)
        if civic and civic.evidence_items:
            combined.evidence_sources.append("CIViC")
        if oncokb and oncokb.treatments:
            combined.evidence_sources.append("OncoKB")
        if escat and escat.evidence_items:
            combined.evidence_sources.append("ESCAT")

    def _calculate_actionability(
        self,
        combined: CombinedEvidence,
        civic: Optional[CIViCVariantAnnotation],
        oncokb: Optional[OncoKBAnnotation],
        escat: Optional[ESCATAnnotation]
    ):
        """
        Calculate actionability score (0-100) based on evidence strength from enabled sources

        Scoring priority (if configured):
        1. ESCAT (European standard) - if prefer_european_standards
        2. OncoKB (US/FDA standard)
        3. CIViC (Community curated)

        Scoring:
        - FDA-approved therapy: 100
        - Guideline therapy (Level 2/B/I-B): 80-90
        - Clinical evidence (Level 3A/C/II-A): 60-70
        - Preclinical (Level 3B/D/II-B): 40
        - Biological (Level 4/E/IV): 20
        """

        score = 0.0
        source = None

        # ESCAT scoring (priority for European context if configured)
        if escat and escat.highest_tier:
            escat_scores = {
                "I-A": 100,
                "I-B": 90,
                "I-C": 80,
                "II-A": 70,
                "II-B": 60,
                "III-A": 50,
                "IV": 30,
                "V": 20,
                "X": 0
            }
            escat_score = escat_scores.get(escat.highest_tier, 0)
            if escat_score > score:
                score = escat_score
                source = f"ESCAT_{escat.highest_tier}"

        # OncoKB scoring (if enabled)
        if oncokb and oncokb.highest_level:
            level_scores = {
                "LEVEL_1": 100,
                "LEVEL_2": 80,
                "LEVEL_3A": 60,
                "LEVEL_3B": 40,
                "LEVEL_4": 20
            }
            oncokb_score = level_scores.get(oncokb.highest_level, 0)
            if oncokb_score > score:
                score = oncokb_score
                source = oncokb.highest_level

        # CIViC scoring (if enabled)
        if civic and self.civic:
            civic_summary = self.civic.get_evidence_summary(civic)
            if civic_summary["max_evidence_level"]:
                civic_scores = {
                    "A": 100,
                    "B": 80,
                    "C": 60,
                    "D": 40,
                    "E": 20
                }
                civic_score = civic_scores.get(civic_summary["max_evidence_level"], 0)
                if civic_score > score:
                    score = civic_score
                    source = f"CIViC_{civic_summary['max_evidence_level']}"

        # Set highest evidence level
        combined.highest_evidence_level = source

        # Bonus for multiple concordant evidence sources
        if len(combined.evidence_sources) >= 2:
            score = min(100, score * 1.1)  # 10% bonus
        if len(combined.evidence_sources) >= 3:
            score = min(100, score * 1.15)  # 15% bonus for all three

        combined.actionability_score = round(score, 1)
        combined.is_actionable = score >= 50  # Actionable if ≥ ESCAT Tier III-A or equivalent

    def _determine_oncogenicity(
        self,
        combined: CombinedEvidence,
        civic: Optional[CIViCVariantAnnotation],
        oncokb: Optional[OncoKBAnnotation]
    ):
        """Determine oncogenic classification from available evidence"""

        # Prefer OncoKB oncogenicity (more standardized) if enabled
        if oncokb and oncokb.oncogenic and oncokb.oncogenic != "Unknown":
            combined.oncogenic_classification = oncokb.oncogenic
            combined.mutation_effect = oncokb.mutation_effect
        # Fall back to CIViC if available and enabled
        elif civic and civic.evidence_items:
            # Infer from CIViC evidence
            pathogenic_count = sum(
                1 for e in civic.evidence_items
                if e.clinical_significance in ["Sensitivity/Response", "Sensitivity", "Resistance"]
            )
            if pathogenic_count > 0:
                combined.oncogenic_classification = "Likely Oncogenic"
            else:
                combined.oncogenic_classification = "Uncertain Significance"
        else:
            combined.oncogenic_classification = "Unknown"

    def get_clinical_report(self, combined: CombinedEvidence) -> Dict:
        """
        Generate structured clinical report from combined evidence

        Args:
            combined: CombinedEvidence

        Returns:
            Dictionary with clinical interpretation
        """

        report = {
            "variant": f"{combined.gene} {combined.variant}",
            "actionability": {
                "is_actionable": combined.is_actionable,
                "score": combined.actionability_score,
                "level": combined.highest_evidence_level
            },
            "escat_classification": {
                "tier": combined.escat_tier,
                "score": combined.escat_score,
                "description": self._get_escat_description(combined.escat_tier)
            },
            "oncogenicity": {
                "classification": combined.oncogenic_classification,
                "mutation_effect": combined.mutation_effect
            },
            "therapeutic_options": {
                "fda_approved": combined.fda_approved_therapies,
                "guideline_recommended": combined.guideline_therapies,
                "investigational": combined.investigational_therapies,
                "resistance": combined.resistance_therapies
            },
            "evidence_sources": combined.evidence_sources,
            "references": {
                "civic": combined.civic_url,
                "oncokb": combined.oncokb_url
            }
        }

        # Add clinical recommendation
        if combined.is_actionable:
            if combined.fda_approved_therapies:
                report["recommendation"] = (
                    f"FDA-approved targeted therapy available: "
                    f"{', '.join(combined.fda_approved_therapies[:3])}"
                )
            elif combined.guideline_therapies:
                report["recommendation"] = (
                    f"Guideline-recommended therapy: "
                    f"{', '.join(combined.guideline_therapies[:3])}"
                )
            else:
                report["recommendation"] = (
                    "Investigational therapies available - consider clinical trial enrollment"
                )
        else:
            report["recommendation"] = "No high-level evidence for targeted therapy"

        return report

    def _get_escat_description(self, tier: Optional[str]) -> str:
        """Get ESCAT tier description"""
        descriptions = {
            'I-A': 'Target ready for routine use - Regulatory approval',
            'I-B': 'Target ready for routine use - Clinical guidelines',
            'I-C': 'Target ready for routine use - Different indication',
            'II-A': 'Investigational target - Clinical evidence',
            'II-B': 'Investigational target - Preclinical evidence',
            'III-A': 'Benefit demonstrated in other tumor type',
            'IV': 'Preclinical evidence of actionability',
            'V': 'Evidence from co-occurring genomic events',
            'X': 'Lack of evidence or resistance marker'
        }
        return descriptions.get(tier, 'Not classified')


# Example usage
if __name__ == "__main__":
    annotator = CombinedAnnotator()

    test_variants = [
        ("EGFR", "L858R", "Lung Adenocarcinoma"),
        ("BRAF", "V600E", "Melanoma"),
        ("KRAS", "G12C", "NSCLC"),
        ("ALK", "Fusion", "NSCLC"),
        ("TP53", "R273H", "Colorectal Cancer"),  # Non-actionable
    ]

    print("="*80)
    print("COMBINED CLINICAL ANNOTATION REPORT")
    print("="*80)

    for gene, variant, tumor_type in test_variants:
        print(f"\n{'='*80}")
        print(f"Variant: {gene} {variant}")
        print(f"Tumor Type: {tumor_type}")
        print('='*80)

        combined = annotator.annotate_variant(gene, variant, tumor_type)
        report = annotator.get_clinical_report(combined)

        print(f"\nActionability Score: {report['actionability']['score']}/100")
        print(f"Evidence Level: {report['actionability']['level']}")
        print(f"Oncogenic: {report['oncogenicity']['classification']}")
        print(f"Mutation Effect: {report['oncogenicity']['mutation_effect']}")

        print(f"\nEvidence Sources: {', '.join(report['evidence_sources'])}")

        if report['therapeutic_options']['fda_approved']:
            print(f"\nFDA-Approved Therapies:")
            for drug in report['therapeutic_options']['fda_approved']:
                print(f"  ✓ {drug}")

        if report['therapeutic_options']['guideline_recommended']:
            print(f"\nGuideline-Recommended:")
            for drug in report['therapeutic_options']['guideline_recommended']:
                print(f"  • {drug}")

        if report['therapeutic_options']['resistance']:
            print(f"\nResistance Markers:")
            for drug in report['therapeutic_options']['resistance']:
                print(f"  ✗ {drug}")

        print(f"\n{'Recommendation:'}")
        print(f"  {report['recommendation']}")

        print(f"\nReferences:")
        if report['references']['civic']:
            print(f"  CIViC: {report['references']['civic']}")
        if report['references']['oncokb']:
            print(f"  OncoKB: {report['references']['oncokb']}")
