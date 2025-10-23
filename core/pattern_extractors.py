#!/usr/bin/env python3
"""
Pattern Extractors - NLP patterns for extracting clinical entities from MTB reports
Contains all regex patterns and extraction logic for Italian clinical text
"""

import re
from typing import List, Optional, Tuple, Set, Dict

# Handle imports for both module and script execution
try:
    from core.data_models import Variant, Patient, Diagnosis, TherapeuticRecommendation
    from vocabularies.vocabulary_loader import VocabularyLoader
except ModuleNotFoundError:
    # When run as script, adjust path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import Variant, Patient, Diagnosis, TherapeuticRecommendation
    from vocabularies.vocabulary_loader import VocabularyLoader


class PatternExtractors:
    """
    Collection of pattern-based extractors for clinical entities
    """

    def __init__(self, vocab_loader: VocabularyLoader):
        """
        Initialize pattern extractors

        Args:
            vocab_loader: VocabularyLoader instance for mapping to controlled vocabularies
        """
        self.vocab = vocab_loader

        # ===== VARIANT PATTERNS =====
        self.variant_patterns = [
            # Detailed exon format: "variante nell'esone X del gene EGFR (NM_005228.4): c.2241A>C, p.(Leu747Phe), frequenza allelica 11%"
            r"variante\s+nell['\']esone\s+\d+\s+del\s+gene\s+(\w+)\s*\([^\)]+\):\s*c\.([^,\s]+)(?:,\s*p\.\(([^)]+)\))?(?:,?\s*frequenza\s+allelica\s+(\d+(?:\.\d+)?)%)?",

            # Pattern tabellare completo: EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
            r'(\w+)\s+c\.([^\s|]+)\s+p\.([^\s|]+)\s+(Pathogenic|VUS|Benign|Risultati discordanti|Likely Pathogenic|Likely Benign)\s+(\d+)%',

            # Pattern inline con VAF: EGFR c.2573T>G 45%
            r'(\w+)\s+([cp]\.[^\s,]+).*?(\d+)%',

            # Pattern alterazioni comuni: EGFR L858R, BRAF V600E, KRAS G12D, TP53 R273H
            r'\b(\w+)\s+([A-Z]\d+[A-Z*_]+)\b',

            # Pattern con parentesi: EGFR (L858R), KRAS (G12D)
            r'\b(\w+)\s*\(([A-Z]\d+[A-Z*]+)\)',

            # Pattern "mutazione di GENE": mutazione di BRAF V600E
            r'mutazione\s+(?:di\s+)?(\w+)[:\s]+([^,.\n]+)',

            # Pattern "alterazione di GENE"
            r'alterazione\s+(?:di\s+)?(\w+)[:\s]+([^,.\n]+)',

            # Pattern frameshift: TP53 p.Arg273fs, BRCA1 p.Gln1756fs
            r'\b(\w+)\s+p\.([A-Z][a-z]{2}\d+fs[*X]?\d*)\b',

            # Pattern stop-gained/nonsense: TP53 p.Arg213*, BRCA1 p.Gln1395*
            r'\b(\w+)\s+p\.([A-Z][a-z]{2}\d+\*)\b',

            # Pattern splice variant: BRCA2 c.8488-1G>A
            r'\b(\w+)\s+c\.(\d+[-+]\d+[ACGT]>[ACGT])\b',

            # Pattern duplicazione: EGFR c.2235_2249dup
            r'\b(\w+)\s+c\.(\d+_\d+dup)',
        ]

        # ===== FUSION PATTERNS =====
        self.fusion_patterns = [
            # fusione ALK::EML4
            r'fusione\s+(\w+)::(\w+)',

            # riarrangiamento GENE1/GENE2 or GENE1:GENE2
            r'riarrangiamento\s+(\w+)[/:]+(\w+)',

            # GENE1-GENE2 fusion (English format)
            r'(\w+)-(\w+)\s+fusion',

            # FGFR3(17)::TACC3(11) - with exon numbers
            r'(\w+)\s*\(\d+\)\s*::\s*(\w+)\s*\(\d+\)',

            # Fusion detected format: ALK fusion detected
            r'\b(\w+)\s+fusion\s+(?:detected|identified|positiv[oa])',

            # GENE rearrangement
            r'\b(\w+)\s+rearrangement',
        ]

        # ===== CNV/AMPLIFICATION PATTERNS =====
        self.cnv_patterns = [
            # ERBB2 amplification, MET amplificazione
            r'\b(\w+)\s+amplif(?:ication|icazione)',

            # MYC amplified
            r'\b(\w+)\s+amplified',

            # ERBB2 copy number: 8.5
            r'\b(\w+)\s+copy\s+number[:\s]+(\d+\.?\d*)',

            # EGFR CN = 12
            r'\b(\w+)\s+CN[:\s=]+(\d+\.?\d*)',

            # Loss of heterozygosity: TP53 LOH
            r'\b(\w+)\s+LOH\b',

            # Deletion: CDKN2A deletion, PTEN delezione
            r'\b(\w+)\s+del(?:etion|ezione)',

            # Homozygous deletion
            r'\b(\w+)\s+(?:homozygous|omozigotica)\s+del(?:etion|ezione)',
        ]

        # ===== EXON PATTERNS =====
        self.exon_patterns = [
            # EGFR esone 19 deletion
            r'(\w+)\s+es(?:one)?\s+(\d+)\s+(insertion|deletion|delins?)',

            # EGFR exon 20 insertion (English)
            r'(\w+)\s+exon\s+(\d+)\s+(insertion|deletion|delins?)',
        ]

        # ===== PATIENT PATTERNS =====
        self.patient_id_patterns = [
            r'ID\s+Paziente[:\s]+([A-Z0-9]+)',
            r'Paziente\s+([A-Z]\d+)\s+',  # "Paziente N1 maschio" format
            r'Paziente\s*[:\s]*([A-Z0-9]+)',
            r'ID[:\s]+([A-Z0-9]+)',
        ]

        self.age_patterns = [
            # Explicit age field - limit to reasonable ages (1-120)
            r'\bEtà[:\s]+(\d{1,3})\b',
            r'\bAge[:\s]+(\d{1,3})\b',
            # More restrictive: age should be reasonable (1-3 digits) and followed by age indicator
            r'\b([1-9]\d{0,2})\s+anni\b',
            r'\b([1-9]\d{0,2})\s+years\b',
        ]

        self.sex_patterns = [
            r'Sesso[:\s]+(M|F|Maschio|Femmina|Male|Female)',
            r'Sex[:\s]+(M|F|Male|Female)',
            r'Gender[:\s]+(M|F|Male|Female)',
            # Inline format: "Paziente N1 maschio" - allow optional ID between Paziente and sex
            r'[Pp]aziente\s+(?:[A-Z0-9]+\s+)?(maschio|femmina)',
        ]

        self.birth_date_patterns = [
            # Support multiple separators: /, -, .
            r'Data\s+di\s+nascita[:\s]+(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})',
            r'Date\s+of\s+birth[:\s]+(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})',
            # "nato/a il" format - colon optional
            r'[Nn]ato[/a]?\s+il[:\s]+(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})',
        ]

        # ===== DIAGNOSIS PATTERNS =====
        # Order matters: more specific patterns first
        self.diagnosis_patterns = [
            # Inline format: "affetto/a da [diagnosis]"
            # Example: "Paziente17 60 anni affetta da adenocarcinoma polmonare stadio IV"
            # Stops at: stadio, stage, con, in, e comutazione
            r'affett[oa]\s+da\s+([^.\n]+?)(?:\s+(?:stadio|stage|con|in\s+terapia|in\s+trattamento|e(?:\s+comutazione)?)\s+)',

            # More flexible variant: stops at period, newline, or "in"
            r'affett[oa]\s+da\s+([^.\n,]+?)(?:\s+in\s+)',

            # Variant: "con diagnosi di [diagnosis]"
            r'con\s+diagnosi\s+di\s+([^.\n]+?)(?:\s+(?:stadio|stage|con)\s+)',

            # Standard format with label (at beginning of line or after newline)
            r'(?:^|\n)Diagnosi[:\s]+([^\n.(]+)',
            r'(?:^|\n)Diagnosis[:\s]+([^\n.(]+)',

            # Tumore/Neoplasia only if at beginning or after specific context
            r'(?:^|\n)Tumore[:\s]+([^\n.(]+)',
            r'(?:^|\n)Neoplasia[:\s]+([^\n.(]+)',

            # Starting with diagnosis type (as fallback)
            # Example: "adenocarcinoma polmonare stadio IV"
            r'\b((?:adeno)?carcinoma\s+\w+(?:\s+\w+)?)\s+stadio',
        ]

        self.stage_patterns = [
            # Note: IV must come before I{1,3} to match correctly
            r'[Ss]tadio[:\s]+(IV|I{1,3}[AB]?)',
            r'[Ss]tage[:\s]+(IV|I{1,3}[AB]?)',
            r'TNM[:\s]+T(\d)N(\d)M(\d)',
        ]

        # ===== TMB PATTERNS =====
        self.tmb_patterns = [
            r'TMB[:\s]*(\d+\.?\d*)\s*mut[s]?/?Mbp?',
            r'tumor\s+mutational\s+burden[:\s]*(\d+\.?\d*)',
            r'TMB[:\s]+(\d+\.?\d*)',
        ]

        # ===== DRUG PATTERNS (will be generated from vocabulary) =====
        self._init_drug_patterns()

    def _init_drug_patterns(self):
        """Initialize drug patterns from vocabulary"""
        drug_names = '|'.join(self.vocab.rxnorm_drugs.keys())

        self.drug_patterns = [
            # "sensibilità a osimertinib"
            rf'\b(sensibilità|risposta|indicazione|approvato)[^.{{50}}]*?\b({drug_names})\b',

            # "trattamento con osimertinib"
            rf'trattamento\s+con\s+\b({drug_names})\b',

            # "indicazione a osimertinib"
            rf'\b({drug_names})\b[^.{{50}}]*?(indicat[oa]|approvato|rimborsato)',

            # Generic drug mention
            rf'\b({drug_names})\b',
        ]

    # ========== PATIENT EXTRACTION ==========

    def extract_patient_info(self, text: str) -> Patient:
        """
        Extract patient demographic information

        Args:
            text: Clinical report text

        Returns:
            Patient dataclass with extracted information
        """
        patient = Patient()

        # Extract ID
        for pattern in self.patient_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient.id = match.group(1)
                break

        # Extract age
        for pattern in self.age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient.age = int(match.group(1))
                break

        # Extract sex
        for pattern in self.sex_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sex_value = match.group(1)
                # Normalize to M/F
                if sex_value.lower() in ['maschio', 'male']:
                    patient.sex = 'M'
                elif sex_value.lower() in ['femmina', 'female']:
                    patient.sex = 'F'
                else:
                    patient.sex = sex_value.upper()
                break

        # Extract birth date
        for pattern in self.birth_date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Convert Italian date format (DD/MM/YYYY) to ISO (YYYY-MM-DD)
                patient.birth_date = self._convert_date_to_iso(date_str)
                break

        # Calculate age from birth date if age not found
        if patient.birth_date and not patient.age:
            patient.age = self._calculate_age_from_birth_date(patient.birth_date)

        return patient

    @staticmethod
    def _convert_date_to_iso(date_str: str) -> str:
        """Convert DD/MM/YYYY or DD.MM.YYYY to YYYY-MM-DD"""
        parts = re.split(r'[/.\-]', date_str)
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

    @staticmethod
    def _calculate_age_from_birth_date(birth_date_iso: str) -> Optional[int]:
        """
        Calculate age from birth date in ISO format (YYYY-MM-DD)

        Args:
            birth_date_iso: Birth date in ISO format (YYYY-MM-DD)

        Returns:
            Age in years, or None if calculation fails
        """
        try:
            from datetime import datetime
            birth = datetime.strptime(birth_date_iso, '%Y-%m-%d')
            today = datetime.now()
            # Calculate age accounting for birthday not yet occurred this year
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return age
        except (ValueError, AttributeError):
            return None

    # ========== DIAGNOSIS EXTRACTION ==========

    def extract_diagnosis(self, text: str) -> Diagnosis:
        """
        Extract diagnosis information

        Args:
            text: Clinical report text

        Returns:
            Diagnosis dataclass with ICD-O mapping
        """
        diagnosis = Diagnosis()

        # Extract primary diagnosis
        for pattern in self.diagnosis_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diagnosis.primary_diagnosis = match.group(1).strip()
                break

        # Extract stage
        for pattern in self.stage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diagnosis.stage = match.group(1)
                break

        # Map to ICD-O
        if diagnosis.primary_diagnosis:
            diagnosis.icd_o_code = self.vocab.map_diagnosis(diagnosis.primary_diagnosis)

        return diagnosis

    # ========== VARIANT EXTRACTION ==========

    def extract_variants(self, text: str) -> List[Variant]:
        """
        Extract genomic variants using multiple pattern strategies

        Args:
            text: Clinical report text

        Returns:
            List of Variant dataclasses with HGNC mapping
        """
        variants = []
        seen = set()  # Deduplicate variants

        # 1. Extract standard variants
        for pattern in self.variant_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                variant = self._parse_variant_match(match, pattern)
                if variant:
                    variant_key = f"{variant.gene}_{variant.protein_change}_{variant.cdna_change}"
                    if variant_key not in seen:
                        # Map to HGNC
                        variant.gene_code = self.vocab.map_gene(variant.gene)
                        # Validate it's a known gene before adding
                        if variant.gene.upper() in self.vocab.hgnc_genes or variant.gene_code:
                            variants.append(variant)
                            seen.add(variant_key)

        # 2. Extract fusions
        fusion_variants = self._extract_fusions(text, seen)
        variants.extend(fusion_variants)
        seen.update([f"{v.gene}_{v.protein_change}" for v in fusion_variants])

        # 3. Extract exon-level alterations
        exon_variants = self._extract_exon_alterations(text, seen)
        variants.extend(exon_variants)
        seen.update([f"{v.gene}_{v.protein_change}" for v in exon_variants])

        # 4. Extract CNV/amplifications
        cnv_variants = self._extract_cnv(text, seen)
        variants.extend(cnv_variants)

        # 5. Post-process: Enrich variants with VAF information
        variants = self._enrich_variants_with_vaf(variants, text)

        return variants

    def _parse_variant_match(self, match: Tuple, pattern: str) -> Optional[Variant]:
        """Parse regex match into Variant object"""
        if not match:
            return None

        # Pattern 1: Full tabular format (gene, cDNA, protein, class, VAF)
        if len(match) == 5:
            gene, cdna, protein, classification, vaf = match
            return Variant(
                gene=gene.upper(),
                cdna_change=f"c.{cdna}" if not cdna.startswith('c.') else cdna,
                protein_change=f"p.{protein}" if not protein.startswith('p.') else protein,
                classification=classification,
                vaf=float(vaf)
            )

        # Pattern for detailed exon format (gene, cDNA, protein, VAF)
        elif len(match) == 4:
            gene, cdna, protein, vaf = match
            return Variant(
                gene=gene.upper(),
                cdna_change=f"c.{cdna}" if cdna and not cdna.startswith('c.') else cdna if cdna else None,
                protein_change=f"p.{protein}" if protein and not protein.startswith('p.') else protein if protein else None,
                vaf=float(vaf) if vaf else None
            )

        # Pattern 2: Gene + change + VAF
        elif len(match) == 3:
            gene, change, vaf = match
            if change.startswith('c.'):
                return Variant(gene=gene.upper(), cdna_change=change, vaf=float(vaf))
            elif change.startswith('p.'):
                return Variant(gene=gene.upper(), protein_change=change, vaf=float(vaf))
            else:
                # Protein short form (e.g., L858R)
                return Variant(gene=gene.upper(), protein_change=change, vaf=float(vaf))

        # Pattern 3: Gene + protein change (no VAF)
        elif len(match) == 2:
            gene, change = match
            return Variant(gene=gene.upper(), protein_change=change.strip())

        return None

    def _extract_fusions(self, text: str, seen: Set[str]) -> List[Variant]:
        """Extract gene fusions"""
        fusions = []

        for pattern in self.fusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                gene1 = match[0].upper()
                gene2 = match[1].upper() if len(match) > 1 else ""

                # Verify at least one is a known gene
                if gene1 not in self.vocab.hgnc_genes and gene2 not in self.vocab.hgnc_genes:
                    continue

                fusion_name = f"{gene1}::{gene2}" if gene2 else gene1
                variant_key = f"{fusion_name}_fusion"

                if variant_key not in seen:
                    variant = Variant(
                        gene=fusion_name,
                        protein_change="fusion",
                        classification="Pathogenic",
                        gene_code=self.vocab.map_gene(gene1)
                    )
                    fusions.append(variant)

        return fusions

    def _extract_exon_alterations(self, text: str, seen: Set[str]) -> List[Variant]:
        """Extract exon-level alterations (insertions/deletions)"""
        exon_variants = []

        for pattern in self.exon_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                gene, exon, alteration = match
                gene = gene.upper()

                if gene not in self.vocab.hgnc_genes:
                    continue

                variant_key = f"{gene}_exon{exon}_{alteration}"
                if variant_key not in seen:
                    variant = Variant(
                        gene=gene,
                        protein_change=f"exon {exon} {alteration}",
                        classification="Pathogenic",
                        gene_code=self.vocab.map_gene(gene)
                    )
                    exon_variants.append(variant)

        return exon_variants

    def _extract_cnv(self, text: str, seen: Set[str]) -> List[Variant]:
        """Extract copy number variations (amplifications/deletions)"""
        cnv_variants = []

        for pattern in self.cnv_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle different match formats
                if isinstance(match, tuple):
                    gene = match[0].upper()
                    copy_number = match[1] if len(match) > 1 else None
                else:
                    gene = match.upper()
                    copy_number = None

                # Validate gene
                if gene not in self.vocab.hgnc_genes:
                    continue

                # Determine alteration type
                alteration_type = self._classify_cnv_alteration(pattern, copy_number)
                variant_key = f"{gene}_{alteration_type}"

                if variant_key not in seen:
                    variant = Variant(
                        gene=gene,
                        protein_change=alteration_type,
                        classification="Pathogenic" if alteration_type in ["amplification", "deletion", "LOH"] else "VUS",
                        gene_code=self.vocab.map_gene(gene),
                        raw_text=f"{gene} {alteration_type}" + (f" (CN={copy_number})" if copy_number else "")
                    )
                    cnv_variants.append(variant)

        return cnv_variants

    @staticmethod
    def _classify_cnv_alteration(pattern: str, copy_number: Optional[str]) -> str:
        """Classify CNV alteration type based on pattern"""
        pattern_lower = pattern.lower()

        if 'amplif' in pattern_lower:
            return "amplification"
        elif 'copy' in pattern_lower or 'cn' in pattern_lower:
            if copy_number:
                cn_val = float(copy_number)
                if cn_val >= 4:
                    return "amplification"
                elif cn_val <= 1:
                    return "deletion"
                else:
                    return f"copy_number_variation (CN={copy_number})"
            return "copy_number_variation"
        elif 'loh' in pattern_lower:
            return "LOH"
        elif 'delet' in pattern_lower or 'delez' in pattern_lower:
            if 'homozygous' in pattern_lower or 'omozigotica' in pattern_lower:
                return "homozygous_deletion"
            return "deletion"
        else:
            return "CNV"

    def _enrich_variants_with_vaf(self, variants: List[Variant], text: str) -> List[Variant]:
        """
        Post-process variants to add VAF (Variant Allele Frequency) information

        Searches for VAF patterns in the text and matches them to variants by gene name.
        Handles multiple Italian formats:
        - "EGFR 16%" (gene + percentage)
        - "frequenza allelica 76%" (spelled out)
        - "f.a. 68%" or "f.a.61%" (abbreviated)

        Args:
            variants: List of extracted variants
            text: Original report text

        Returns:
            Variants enriched with VAF where found
        """
        # VAF extraction patterns (in order of priority)
        vaf_patterns = [
            # Pattern 1: Gene name followed by percentage
            # Example: "EGFR 16%" or "PTEN 20%"
            (r'\b({gene})\s+(\d+(?:\.\d+)?)%', 'gene_percent'),

            # Pattern 2: Gene + mutation + f.a. + percentage
            # Example: "Gly719Arg f.a.61%" or "f.a. 68%"
            (r'({mutation})\s+f\.a\.?\s*(\d+(?:\.\d+)?)%', 'mutation_fa'),

            # Pattern 3: "frequenza allelica" spelled out
            # Example: "frequenza allelica 76%"
            (r'({mutation}).*?frequenza\s+allelica\s+(\d+(?:\.\d+)?)%', 'mutation_freq'),

            # Pattern 4: Protein change followed by percentage
            # Example: "L858R 45%" or "(L858R) 45%"
            (r'({mutation})\s*\)?\s*(\d+(?:\.\d+)?)%', 'mutation_percent'),
        ]

        # Create a mapping of gene -> variants for quick lookup
        gene_variants = {}
        for variant in variants:
            if variant.gene not in gene_variants:
                gene_variants[variant.gene] = []
            gene_variants[variant.gene].append(variant)

        # For each variant without VAF, try to find it
        for variant in variants:
            if variant.vaf is not None:
                continue  # Already has VAF

            gene = variant.gene
            mutation = variant.protein_change or variant.cdna_change

            # Try gene-based patterns first
            for pattern_template, pattern_type in vaf_patterns:
                if '{gene}' in pattern_template:
                    # Gene-based pattern
                    pattern = pattern_template.replace('{gene}', re.escape(gene))
                    matches = re.findall(pattern, text, re.IGNORECASE)

                    if matches:
                        # Take the first match
                        vaf_value = float(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                        variant.vaf = vaf_value
                        break

                elif mutation and '{mutation}' in pattern_template:
                    # Mutation-based pattern
                    # Clean mutation string for regex
                    mutation_clean = mutation.strip('p.').strip('c.')
                    pattern = pattern_template.replace('{mutation}', re.escape(mutation_clean))
                    matches = re.findall(pattern, text, re.IGNORECASE)

                    if matches:
                        vaf_value = float(matches[0][1] if isinstance(matches[0], tuple) else matches[0])
                        variant.vaf = vaf_value
                        break

            # Special case: Look for VAF in nearby context (within 200 chars)
            if variant.vaf is None and mutation:
                # Find mutation mention in text
                mutation_clean = mutation.strip('p.').strip('c.')
                mutation_pattern = re.escape(mutation_clean)

                for match in re.finditer(mutation_pattern, text, re.IGNORECASE):
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end]

                    # Look for percentage in context
                    vaf_match = re.search(r'(\d+(?:\.\d+)?)%', context)
                    if vaf_match:
                        variant.vaf = float(vaf_match.group(1))
                        break

        return variants

    # ========== TMB EXTRACTION ==========

    def extract_tmb(self, text: str) -> Optional[float]:
        """
        Extract Tumor Mutational Burden value

        Args:
            text: Clinical report text

        Returns:
            TMB value in mutations/Mb, or None
        """
        for pattern in self.tmb_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tmb_val = float(match.group(1))
                # Validation: TMB typically 0-1000 mut/Mb
                if 0 < tmb_val < 1000:
                    return tmb_val
        return None

    # ========== THERAPEUTIC RECOMMENDATIONS EXTRACTION ==========

    def extract_therapeutic_recommendations(self, text: str) -> List[TherapeuticRecommendation]:
        """
        Extract therapeutic recommendations with drug-gene mapping

        Args:
            text: Clinical report text

        Returns:
            List of TherapeuticRecommendation dataclasses
        """
        recommendations = []
        seen_drugs = set()

        for pattern in self.drug_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                drug_name = self._extract_drug_from_match(match)
                if not drug_name or drug_name in seen_drugs:
                    continue

                # Map drug to RxNorm
                drug_info = self.vocab.map_drug(drug_name)
                if not drug_info:
                    continue

                # Create recommendation
                recommendation = TherapeuticRecommendation(
                    drug=drug_name,
                    drug_code=drug_info,
                    gene_target=", ".join(drug_info.get('target', [])),
                    evidence_level=drug_info.get('evidence_level', 'Unknown')
                )

                recommendations.append(recommendation)
                seen_drugs.add(drug_name)

        return recommendations

    @staticmethod
    def _extract_drug_from_match(match: Tuple) -> Optional[str]:
        """Extract drug name from regex match tuple"""
        if isinstance(match, str):
            return match.lower().strip()

        for item in match:
            # Look for the drug name (typically longer, contains drug-like terms)
            if len(item) > 3 and any(c.isalpha() for c in item):
                if item.lower() not in ['sensibilità', 'risposta', 'indicazione', 'approvato', 'trattamento']:
                    return item.lower().strip()

        return None


# Example usage
if __name__ == "__main__":
    # Initialize (use relative imports when run as script)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from vocabularies.vocabulary_loader import VocabularyLoader
    from core.data_models import Variant, Patient, Diagnosis

    vocab = VocabularyLoader()
    extractors = PatternExtractors(vocab)

    # Test text
    test_text = """
    Paziente: 12345
    Età: 65 anni
    Sesso: M
    Data di nascita: 15/03/1958

    Diagnosi: Adenocarcinoma polmonare stadio IV

    Varianti identificate:
    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    KRAS G12D 32%
    fusione ALK::EML4

    TMB: 8.5 mut/Mb

    Raccomandazioni: sensibilità a osimertinib
    """

    # Extract entities
    patient = extractors.extract_patient_info(test_text)
    print(f"Patient: ID={patient.id}, Age={patient.age}, Sex={patient.sex}, Birth={patient.birth_date}")

    diagnosis = extractors.extract_diagnosis(test_text)
    print(f"\nDiagnosis: {diagnosis.primary_diagnosis} (Stage: {diagnosis.stage})")
    print(f"ICD-O: {diagnosis.icd_o_code}")

    variants = extractors.extract_variants(test_text)
    print(f"\nVariants found: {len(variants)}")
    for v in variants:
        print(f"  - {v.gene} {v.protein_change or v.cdna_change} (VAF: {v.vaf}%)")

    tmb = extractors.extract_tmb(test_text)
    print(f"\nTMB: {tmb} mut/Mb")

    recommendations = extractors.extract_therapeutic_recommendations(test_text)
    print(f"\nRecommendations: {len(recommendations)}")
    for r in recommendations:
        print(f"  - {r.drug} (Target: {r.gene_target})")
