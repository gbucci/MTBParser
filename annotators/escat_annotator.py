#!/usr/bin/env python3
"""
ESCAT (ESMO Scale for Clinical Actionability of molecular Targets) Annotator

ESCAT è il sistema di classificazione ESMO per l'actionability clinica delle alterazioni molecolari.
Definisce 6 livelli tier-based per guidare le decisioni terapeutiche nella pratica oncologica.

ESCAT Tiers:
- Tier I: Targets ready for routine use
  - I-A: Biomarker approvato da agenzie regolatorie (EMA/FDA) in questa indicazione
  - I-B: Linee guida cliniche (ESMO-MCBS ≥4)
  - I-C: Farmaco approvato ma in diversa indicazione tumorale

- Tier II: Investigational targets - likely clinically actionable
  - II-A: Prove cliniche consistenti in tumori resistenti/refrattari
  - II-B: Evidenza preclinica robusta con rilevanza clinica

- Tier III: Clinical benefit previously demonstrated in other tumor types
  - III-A: Beneficio in altro tipo tumorale con stesso target

- Tier IV: Preclinical evidence of actionability

- Tier V: Evidence of actionability from co-occurring genomic events

- Tier X: Lack of evidence for actionability

References:
- Mateo J, et al. A framework to rank genomic alterations as targets for cancer precision medicine:
  the ESMO Scale for Clinical Actionability of molecular Targets (ESCAT). Ann Oncol. 2018;29(9):1895-1902.
- ESMO Guidelines: https://www.esmo.org/guidelines/precision-medicine
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ESCATTier(Enum):
    """ESCAT tier classification"""
    TIER_I_A = "I-A"
    TIER_I_B = "I-B"
    TIER_I_C = "I-C"
    TIER_II_A = "II-A"
    TIER_II_B = "II-B"
    TIER_III_A = "III-A"
    TIER_IV = "IV"
    TIER_V = "V"
    TIER_X = "X"


@dataclass
class ESCATEvidence:
    """ESCAT evidence item"""
    tier: str
    alteration: str
    gene: str
    cancer_type: str
    drug_names: List[str]
    approval_agency: Optional[str] = None  # EMA, FDA, AIFA
    guideline_source: Optional[str] = None  # ESMO, NCCN, AIOM
    esmo_mcbs_score: Optional[int] = None  # ESMO Magnitude of Clinical Benefit Scale
    evidence_description: str = ""
    clinical_trial_phase: Optional[str] = None
    pmid_references: List[str] = field(default_factory=list)


@dataclass
class ESCATAnnotation:
    """Complete ESCAT annotation for a variant"""
    gene: str
    alteration: str
    tumor_type: str
    highest_tier: Optional[str] = None
    escat_score: float = 0.0  # 0-100 derived from tier
    evidence_items: List[ESCATEvidence] = field(default_factory=list)
    is_actionable: bool = False  # True for Tier I-III
    clinical_recommendation: str = ""
    alternative_indications: List[Dict] = field(default_factory=list)


class ESCATAnnotator:
    """
    Annotator implementing ESMO ESCAT classification system

    Classifies molecular alterations according to ESCAT tiers based on:
    - Regulatory approval status (EMA/FDA/AIFA)
    - Clinical guideline recommendations (ESMO, NCCN, AIOM)
    - Clinical trial evidence
    - Preclinical evidence
    """

    def __init__(self):
        """Initialize ESCAT annotator with knowledge base"""
        self.cache = {}
        self._init_escat_knowledge_base()

    def _init_escat_knowledge_base(self):
        """
        Initialize ESCAT knowledge base with tier-classified alterations

        This is a curated database based on:
        - EMA/FDA/AIFA approvals
        - ESMO Clinical Practice Guidelines
        - AIOM (Italian) Guidelines
        - Published clinical trials
        """

        self.escat_db = {
            # ============================================================
            # TIER I-A: EMA/FDA approved in this indication
            # ============================================================

            ("EGFR", "L858R", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="L858R",
                gene="EGFR",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Osimertinib", "Gefitinib", "Erlotinib", "Afatinib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved first-line therapy for EGFR-mutant NSCLC",
                pmid_references=["24065731", "26522272"]
            ),

            ("EGFR", "exon 19 deletion", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="Exon 19 deletion",
                gene="EGFR",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Osimertinib", "Gefitinib", "Erlotinib", "Afatinib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=5,
                evidence_description="EMA/FDA approved first-line therapy for EGFR exon 19 del NSCLC",
                pmid_references=["24065731", "28586279"]
            ),

            ("EGFR", "T790M", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="T790M",
                gene="EGFR",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Osimertinib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved for EGFR T790M resistance mutation",
                pmid_references=["26522272"]
            ),

            ("ALK", "Fusion", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="ALK fusion",
                gene="ALK",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Alectinib", "Crizotinib", "Ceritinib", "Brigatinib", "Lorlatinib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=5,
                evidence_description="EMA/FDA approved for ALK+ NSCLC",
                pmid_references=["23724913", "28586279"]
            ),

            ("ROS1", "Fusion", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="ROS1 fusion",
                gene="ROS1",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Crizotinib", "Entrectinib"],
                approval_agency="EMA, FDA",
                guideline_source="ESMO",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved for ROS1+ NSCLC",
                pmid_references=["25264305"]
            ),

            ("BRAF", "V600E", "Melanoma"): ESCATEvidence(
                tier="I-A",
                alteration="V600E",
                gene="BRAF",
                cancer_type="Melanoma",
                drug_names=["Dabrafenib + Trametinib", "Vemurafenib + Cobimetinib", "Encorafenib + Binimetinib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=5,
                evidence_description="EMA/FDA approved for BRAF V600E melanoma",
                pmid_references=["22663011", "25399551"]
            ),

            ("BRAF", "V600E", "Colorectal Cancer"): ESCATEvidence(
                tier="I-A",
                alteration="V600E",
                gene="BRAF",
                cancer_type="Colorectal Cancer",
                drug_names=["Encorafenib + Cetuximab"],
                approval_agency="EMA, FDA",
                guideline_source="ESMO",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved for BRAF V600E mCRC",
                pmid_references=["31566309"]
            ),

            ("KRAS", "G12C", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="G12C",
                gene="KRAS",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Sotorasib", "Adagrasib"],
                approval_agency="FDA, EMA",
                guideline_source="ESMO, NCCN",
                esmo_mcbs_score=3,
                evidence_description="FDA/EMA approved for KRAS G12C NSCLC",
                pmid_references=["33658825", "36070710"]
            ),

            ("ERBB2", "Amplification", "Breast Cancer"): ESCATEvidence(
                tier="I-A",
                alteration="Amplification",
                gene="ERBB2",
                cancer_type="Breast Cancer",
                drug_names=["Trastuzumab", "Pertuzumab", "Trastuzumab Deruxtecan", "T-DM1"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=5,
                evidence_description="EMA/FDA approved for HER2+ breast cancer",
                pmid_references=["11231778", "22149876", "35213103"]
            ),

            ("ERBB2", "Amplification", "Gastric Cancer"): ESCATEvidence(
                tier="I-A",
                alteration="Amplification",
                gene="ERBB2",
                cancer_type="Gastric Cancer",
                drug_names=["Trastuzumab"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved for HER2+ gastric cancer",
                pmid_references=["20728210"]
            ),

            ("BRCA1", "Loss", "Ovarian Cancer"): ESCATEvidence(
                tier="I-A",
                alteration="Loss of function",
                gene="BRCA1",
                cancer_type="Ovarian Cancer",
                drug_names=["Olaparib", "Niraparib", "Rucaparib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved PARP inhibitors for BRCA-mutant ovarian cancer",
                pmid_references=["24429876", "27074132"]
            ),

            ("BRCA2", "Loss", "Ovarian Cancer"): ESCATEvidence(
                tier="I-A",
                alteration="Loss of function",
                gene="BRCA2",
                cancer_type="Ovarian Cancer",
                drug_names=["Olaparib", "Niraparib", "Rucaparib"],
                approval_agency="EMA, FDA, AIFA",
                guideline_source="ESMO, AIOM",
                esmo_mcbs_score=4,
                evidence_description="EMA/FDA approved PARP inhibitors for BRCA-mutant ovarian cancer",
                pmid_references=["24429876", "27074132"]
            ),

            ("RET", "Fusion", "NSCLC"): ESCATEvidence(
                tier="I-A",
                alteration="RET fusion",
                gene="RET",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Selpercatinib", "Pralsetinib"],
                approval_agency="EMA, FDA",
                guideline_source="ESMO",
                esmo_mcbs_score=4,
                evidence_description="FDA/EMA approved for RET fusion+ NSCLC",
                pmid_references=["32846060", "32846062"]
            ),

            ("NTRK1", "Fusion", "Solid Tumors"): ESCATEvidence(
                tier="I-A",
                alteration="NTRK fusion",
                gene="NTRK1",
                cancer_type="Solid Tumors",
                drug_names=["Larotrectinib", "Entrectinib"],
                approval_agency="EMA, FDA",
                guideline_source="ESMO",
                esmo_mcbs_score=5,
                evidence_description="Tissue-agnostic FDA/EMA approval for NTRK fusion+ tumors",
                pmid_references=["29513132", "30093503"]
            ),

            # ============================================================
            # TIER I-B: Clinical practice guidelines (ESMO-MCBS ≥4)
            # ============================================================

            ("PIK3CA", "H1047R", "Breast Cancer"): ESCATEvidence(
                tier="I-B",
                alteration="H1047R",
                gene="PIK3CA",
                cancer_type="Breast Cancer",
                drug_names=["Alpelisib + Fulvestrant"],
                approval_agency="FDA, EMA",
                guideline_source="ESMO, NCCN",
                esmo_mcbs_score=3,
                evidence_description="FDA approved, ESMO guidelines for PIK3CA-mutant HR+ breast cancer",
                pmid_references=["31091374"]
            ),

            ("MET", "exon 14 skipping", "NSCLC"): ESCATEvidence(
                tier="I-B",
                alteration="MET exon 14 skipping",
                gene="MET",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Capmatinib", "Tepotinib"],
                approval_agency="FDA, EMA",
                guideline_source="ESMO",
                esmo_mcbs_score=4,
                evidence_description="FDA/EMA approved for MET exon 14 skipping NSCLC",
                pmid_references=["32469185"]
            ),

            # ============================================================
            # TIER I-C: Off-label use in different tumor type
            # ============================================================

            ("BRAF", "V600E", "NSCLC"): ESCATEvidence(
                tier="I-C",
                alteration="V600E",
                gene="BRAF",
                cancer_type="Non-Small Cell Lung Cancer",
                drug_names=["Dabrafenib + Trametinib"],
                approval_agency="FDA (melanoma approved)",
                guideline_source="ESMO",
                esmo_mcbs_score=3,
                evidence_description="FDA approved in melanoma, compelling evidence in NSCLC",
                pmid_references=["27959684"]
            ),

            # ============================================================
            # TIER II-A: Clinical evidence in refractory/resistant tumors
            # ============================================================

            ("FGFR2", "Fusion", "Cholangiocarcinoma"): ESCATEvidence(
                tier="II-A",
                alteration="FGFR2 fusion",
                gene="FGFR2",
                cancer_type="Cholangiocarcinoma",
                drug_names=["Pemigatinib", "Infigratinib"],
                approval_agency="FDA",
                guideline_source="NCCN",
                evidence_description="FDA breakthrough designation, Phase 2 evidence",
                clinical_trial_phase="Phase 2",
                pmid_references=["32203698"]
            ),

            ("FGFR3", "Mutation", "Bladder Cancer"): ESCATEvidence(
                tier="II-A",
                alteration="Activating mutations",
                gene="FGFR3",
                cancer_type="Bladder Cancer",
                drug_names=["Erdafitinib"],
                approval_agency="FDA",
                evidence_description="FDA approved for FGFR3-altered urothelial cancer",
                clinical_trial_phase="Phase 2",
                pmid_references=["30694700"]
            ),

            # ============================================================
            # TIER III-A: Benefit in other tumor type
            # ============================================================

            ("ERBB2", "Amplification", "Colorectal Cancer"): ESCATEvidence(
                tier="III-A",
                alteration="Amplification",
                gene="ERBB2",
                cancer_type="Colorectal Cancer",
                drug_names=["Trastuzumab + Pertuzumab"],
                evidence_description="Approved in breast/gastric, evidence in HER2+ mCRC",
                clinical_trial_phase="Phase 2",
                pmid_references=["32767915"]
            ),

            # ============================================================
            # TIER X: Resistance markers (important for negative selection)
            # ============================================================

            ("KRAS", "G12D", "Colorectal Cancer"): ESCATEvidence(
                tier="X",
                alteration="G12D",
                gene="KRAS",
                cancer_type="Colorectal Cancer",
                drug_names=["Cetuximab", "Panitumumab"],
                evidence_description="KRAS mutations confer resistance to anti-EGFR therapy",
                pmid_references=["18316791"]
            ),
        }

    def annotate_variant(
        self,
        gene: str,
        alteration: str,
        tumor_type: str
    ) -> ESCATAnnotation:
        """
        Annotate variant according to ESCAT classification

        Args:
            gene: Gene symbol (e.g., "EGFR")
            alteration: Alteration type (e.g., "L858R", "Fusion", "Amplification")
            tumor_type: Cancer type (e.g., "NSCLC", "Breast Cancer")

        Returns:
            ESCATAnnotation with tier classification
        """
        cache_key = f"{gene}_{alteration}_{tumor_type}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query ESCAT database
        annotation = self._query_escat(gene, alteration, tumor_type)

        # Calculate ESCAT score and actionability
        self._calculate_escat_metrics(annotation)

        # Generate clinical recommendation
        self._generate_recommendation(annotation)

        self.cache[cache_key] = annotation
        return annotation

    def _query_escat(
        self,
        gene: str,
        alteration: str,
        tumor_type: str
    ) -> ESCATAnnotation:
        """Query ESCAT database for variant classification"""

        annotation = ESCATAnnotation(
            gene=gene,
            alteration=alteration,
            tumor_type=tumor_type
        )

        # Normalize inputs
        gene_norm = gene.upper()
        tumor_norm = self._normalize_tumor_type(tumor_type)
        alt_norm = self._normalize_alteration(alteration)

        # Try exact match
        for (db_gene, db_alt, db_tumor), evidence in self.escat_db.items():
            if gene_norm == db_gene.upper():
                # Check alteration match
                if self._alteration_matches(alt_norm, db_alt):
                    # Check tumor type match
                    if self._tumor_matches(tumor_norm, db_tumor):
                        annotation.evidence_items.append(evidence)

        # Sort evidence by tier priority
        if annotation.evidence_items:
            annotation.evidence_items.sort(key=lambda x: self._tier_priority(x.tier))
            annotation.highest_tier = annotation.evidence_items[0].tier

        # Look for alternative indications (same gene/alt, different tumor)
        self._find_alternative_indications(annotation, gene_norm, alt_norm, tumor_norm)

        return annotation

    def _normalize_tumor_type(self, tumor_type: str) -> str:
        """Normalize tumor type for matching"""
        if not tumor_type:
            return ""

        tumor_lower = tumor_type.lower()

        # Map Italian/English variations
        mappings = {
            'polmonare': 'lung',
            'nsclc': 'lung',
            'adenocarcinoma polmonare': 'nsclc',
            'mammella': 'breast',
            'mammario': 'breast',
            'colon-retto': 'colorectal',
            'colonretto': 'colorectal',
            'melanoma': 'melanoma',
            'ovarico': 'ovarian',
            'gastrico': 'gastric',
            'colangiocarcinoma': 'cholangiocarcinoma',
            'vescica': 'bladder',
        }

        for pattern, normalized in mappings.items():
            if pattern in tumor_lower:
                return normalized

        return tumor_lower

    def _normalize_alteration(self, alteration: str) -> str:
        """Normalize alteration notation"""
        if not alteration:
            return ""

        alt_upper = alteration.upper().strip()

        # Remove prefixes
        alt_upper = alt_upper.replace("P.", "").replace("C.", "")

        # Normalize common patterns
        if "FUSION" in alt_upper or "RIARRANGIAMENTO" in alt_upper:
            return "FUSION"
        if "AMPLIF" in alt_upper:
            return "AMPLIFICATION"
        if "DELET" in alt_upper or "DELEZ" in alt_upper:
            return "DELETION"
        if "LOSS" in alt_upper or "LOF" in alt_upper:
            return "LOSS"
        if "EXON 19" in alt_upper and "DEL" in alt_upper:
            return "EXON 19 DELETION"
        if "EXON 14" in alt_upper and "SKIP" in alt_upper:
            return "EXON 14 SKIPPING"

        return alt_upper

    def _alteration_matches(self, alt1: str, alt2: str) -> bool:
        """Check if alterations match"""
        alt1_norm = self._normalize_alteration(alt1)
        alt2_norm = self._normalize_alteration(alt2)

        # Exact match
        if alt1_norm == alt2_norm:
            return True

        # Partial match for common terms
        if alt1_norm in alt2_norm or alt2_norm in alt1_norm:
            return True

        return False

    def _tumor_matches(self, tumor1: str, tumor2: str) -> bool:
        """Check if tumor types match"""
        tumor1_norm = self._normalize_tumor_type(tumor1)
        tumor2_norm = self._normalize_tumor_type(tumor2)

        # Check for "Solid Tumors" (tissue-agnostic)
        if "solid" in tumor2_norm.lower():
            return True

        # Exact match
        if tumor1_norm == tumor2_norm:
            return True

        # Partial match
        if tumor1_norm in tumor2_norm or tumor2_norm in tumor1_norm:
            return True

        return False

    def _find_alternative_indications(
        self,
        annotation: ESCATAnnotation,
        gene: str,
        alteration: str,
        tumor_type: str
    ):
        """Find evidence for same alteration in different tumor types"""
        alternatives = []

        for (db_gene, db_alt, db_tumor), evidence in self.escat_db.items():
            if db_gene.upper() == gene and self._alteration_matches(alteration, db_alt):
                if not self._tumor_matches(tumor_type, db_tumor):
                    alternatives.append({
                        'tumor_type': db_tumor,
                        'tier': evidence.tier,
                        'drugs': evidence.drug_names,
                        'evidence': evidence.evidence_description
                    })

        annotation.alternative_indications = alternatives

    def _tier_priority(self, tier: str) -> int:
        """Return priority for tier sorting (lower = higher priority)"""
        priority_map = {
            'I-A': 1,
            'I-B': 2,
            'I-C': 3,
            'II-A': 4,
            'II-B': 5,
            'III-A': 6,
            'IV': 7,
            'V': 8,
            'X': 9
        }
        return priority_map.get(tier, 99)

    def _calculate_escat_metrics(self, annotation: ESCATAnnotation):
        """Calculate ESCAT score and actionability"""

        if not annotation.highest_tier:
            annotation.escat_score = 0.0
            annotation.is_actionable = False
            return

        # ESCAT score mapping (0-100)
        score_map = {
            'I-A': 100,
            'I-B': 90,
            'I-C': 80,
            'II-A': 70,
            'II-B': 60,
            'III-A': 50,
            'IV': 30,
            'V': 20,
            'X': 0
        }

        annotation.escat_score = score_map.get(annotation.highest_tier, 0)

        # Actionable = Tier I-III
        annotation.is_actionable = annotation.highest_tier in ['I-A', 'I-B', 'I-C', 'II-A', 'II-B', 'III-A']

    def _generate_recommendation(self, annotation: ESCATAnnotation):
        """Generate clinical recommendation based on ESCAT tier"""

        if not annotation.highest_tier:
            annotation.clinical_recommendation = (
                "Nessuna evidenza ESCAT disponibile per questa alterazione. "
                "Considerare consultazione con Molecular Tumor Board."
            )
            return

        tier = annotation.highest_tier
        evidence = annotation.evidence_items[0] if annotation.evidence_items else None

        if tier == 'I-A':
            drugs = ", ".join(evidence.drug_names[:3]) if evidence else "farmaci approvati"
            annotation.clinical_recommendation = (
                f"ESCAT Tier I-A: Uso routinario raccomandato. {drugs} approvato/i da EMA/FDA "
                f"per questa indicazione. Terapia standard secondo linee guida ESMO/AIOM."
            )

        elif tier == 'I-B':
            drugs = ", ".join(evidence.drug_names[:3]) if evidence else "farmaci"
            annotation.clinical_recommendation = (
                f"ESCAT Tier I-B: Raccomandato dalle linee guida cliniche (ESMO-MCBS ≥4). "
                f"Considerare {drugs} secondo protocolli ESMO."
            )

        elif tier == 'I-C':
            drugs = ", ".join(evidence.drug_names[:2]) if evidence else "farmaci"
            annotation.clinical_recommendation = (
                f"ESCAT Tier I-C: Farmaco approvato in diversa indicazione tumorale. "
                f"Considerare uso off-label di {drugs} previo consenso informato."
            )

        elif tier == 'II-A':
            drugs = ", ".join(evidence.drug_names[:2]) if evidence else "farmaci"
            annotation.clinical_recommendation = (
                f"ESCAT Tier II-A: Evidenza clinica in tumori resistenti/refrattari. "
                f"Considerare {drugs} in contesto di early access program o clinical trial."
            )

        elif tier == 'II-B':
            annotation.clinical_recommendation = (
                f"ESCAT Tier II-B: Evidenza preclinica robusta. "
                f"Eleggibile per clinical trial se disponibili."
            )

        elif tier == 'III-A':
            drugs = ", ".join(evidence.drug_names[:2]) if evidence else "farmaci"
            alt_tumors = [a['tumor_type'] for a in annotation.alternative_indications[:2]]
            if alt_tumors:
                annotation.clinical_recommendation = (
                    f"ESCAT Tier III-A: Beneficio dimostrato in {', '.join(alt_tumors)}. "
                    f"Considerare {drugs} in contesto off-label o basket trial."
                )
            else:
                annotation.clinical_recommendation = (
                    f"ESCAT Tier III-A: Beneficio in altro tipo tumorale. "
                    f"Valutare in Molecular Tumor Board."
                )

        elif tier == 'IV':
            annotation.clinical_recommendation = (
                "ESCAT Tier IV: Solo evidenza preclinica. "
                "Considerare arruolamento in trial clinici fase I/II."
            )

        elif tier == 'V':
            annotation.clinical_recommendation = (
                "ESCAT Tier V: Evidenza da eventi genomici co-occorrenti. "
                "Valutare profilo genomico completo."
            )

        elif tier == 'X':
            annotation.clinical_recommendation = (
                "ESCAT Tier X: Marker di resistenza o nessuna evidenza di actionability. "
                "Evitare terapie non efficaci. Considerare alternative terapeutiche."
            )

    def get_escat_report(self, annotation: ESCATAnnotation) -> Dict:
        """
        Generate structured ESCAT clinical report

        Args:
            annotation: ESCATAnnotation

        Returns:
            Dictionary with ESCAT report
        """

        # Extract drugs by tier
        tier_i_drugs = []
        tier_ii_drugs = []
        tier_iii_drugs = []

        for evidence in annotation.evidence_items:
            if evidence.tier.startswith('I-'):
                tier_i_drugs.extend(evidence.drug_names)
            elif evidence.tier.startswith('II-'):
                tier_ii_drugs.extend(evidence.drug_names)
            elif evidence.tier.startswith('III-'):
                tier_iii_drugs.extend(evidence.drug_names)

        report = {
            'variant': f"{annotation.gene} {annotation.alteration}",
            'tumor_type': annotation.tumor_type,
            'escat_classification': {
                'tier': annotation.highest_tier,
                'score': annotation.escat_score,
                'is_actionable': annotation.is_actionable,
                'description': self._get_tier_description(annotation.highest_tier)
            },
            'therapeutic_options': {
                'tier_I': list(set(tier_i_drugs)),
                'tier_II': list(set(tier_ii_drugs)),
                'tier_III': list(set(tier_iii_drugs))
            },
            'evidence_items': [
                {
                    'tier': e.tier,
                    'drugs': e.drug_names,
                    'approval': e.approval_agency,
                    'guidelines': e.guideline_source,
                    'esmo_mcbs': e.esmo_mcbs_score,
                    'description': e.evidence_description
                }
                for e in annotation.evidence_items
            ],
            'alternative_indications': annotation.alternative_indications,
            'clinical_recommendation': annotation.clinical_recommendation
        }

        return report

    def _get_tier_description(self, tier: Optional[str]) -> str:
        """Get tier description in Italian"""
        descriptions = {
            'I-A': 'Target pronto per uso routinario - Approvazione regolatoria',
            'I-B': 'Target pronto per uso routinario - Linee guida cliniche',
            'I-C': 'Target pronto per uso routinario - Diversa indicazione',
            'II-A': 'Target investigazionale - Evidenza clinica',
            'II-B': 'Target investigazionale - Evidenza preclinica',
            'III-A': 'Beneficio in altro tipo tumorale',
            'IV': 'Evidenza preclinica di actionability',
            'V': 'Evidenza da eventi genomici co-occorrenti',
            'X': 'Assenza di evidenza o marker di resistenza'
        }
        return descriptions.get(tier, 'Tier non classificato')


# Example usage
if __name__ == "__main__":
    annotator = ESCATAnnotator()

    test_cases = [
        ("EGFR", "L858R", "NSCLC"),
        ("ALK", "Fusion", "NSCLC"),
        ("BRAF", "V600E", "Melanoma"),
        ("BRAF", "V600E", "NSCLC"),
        ("KRAS", "G12C", "NSCLC"),
        ("ERBB2", "Amplification", "Breast Cancer"),
        ("ERBB2", "Amplification", "Colorectal Cancer"),
        ("KRAS", "G12D", "Colorectal Cancer"),
    ]

    print("="*80)
    print("ESCAT ANNOTATION REPORT (ESMO Scale for Clinical Actionability)")
    print("="*80)

    for gene, alteration, tumor in test_cases:
        print(f"\n{'='*80}")
        print(f"Variante: {gene} {alteration}")
        print(f"Tumore: {tumor}")
        print('='*80)

        annotation = annotator.annotate_variant(gene, alteration, tumor)
        report = annotator.get_escat_report(annotation)

        # Print ESCAT classification
        escat = report['escat_classification']
        print(f"\nESCAT Tier: {escat['tier'] or 'N/A'}")
        print(f"Score: {escat['score']}/100")
        print(f"Actionable: {'✓ SI' if escat['is_actionable'] else '✗ NO'}")
        print(f"Descrizione: {escat['description']}")

        # Print therapeutic options
        therapies = report['therapeutic_options']
        if therapies['tier_I']:
            print(f"\nTier I - Farmaci Approvati:")
            for drug in therapies['tier_I']:
                print(f"  ✓ {drug}")

        if therapies['tier_II']:
            print(f"\nTier II - Investigazionali:")
            for drug in therapies['tier_II']:
                print(f"  • {drug}")

        if therapies['tier_III']:
            print(f"\nTier III - Off-label:")
            for drug in therapies['tier_III']:
                print(f"  ○ {drug}")

        # Print alternative indications
        if report['alternative_indications']:
            print(f"\nIndicazioni Alternative:")
            for alt in report['alternative_indications'][:3]:
                print(f"  - {alt['tumor_type']}: {alt['tier']} ({', '.join(alt['drugs'][:2])})")

        # Print recommendation
        print(f"\n📋 Raccomandazione Clinica:")
        print(f"  {report['clinical_recommendation']}")
