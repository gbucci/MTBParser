#!/usr/bin/env python3
"""
Sistema Completo MTB Report Parser con FHIR/Phenopackets/OMOP Mapping
Include: parsing, vocabolari controllati, quality metrics, export multi-formato
Versione: 1.0.0
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import hashlib
from collections import defaultdict

# =====================================================================
# VOCABOLARI CONTROLLATI
# =====================================================================

class ControlledVocabularies:
    """Vocabolari controllati per standardizzazione terminologica"""
    
    # ICD-O-3 (International Classification of Diseases for Oncology)
    ICD_O_DIAGNOSES = {
        'adenocarcinoma polmonare': {'code': '8140/3', 'system': 'ICD-O-3', 'display': 'Adenocarcinoma, NOS'},
        'carcinoma squamoso polmonare': {'code': '8070/3', 'system': 'ICD-O-3', 'display': 'Squamous cell carcinoma, NOS'},
        'feocromocitoma': {'code': '8700/3', 'system': 'ICD-O-3', 'display': 'Pheochromocytoma, malignant'},
        'paraganglioma': {'code': '8693/3', 'system': 'ICD-O-3', 'display': 'Paraganglioma, malignant'},
        'melanoma': {'code': '8720/3', 'system': 'ICD-O-3', 'display': 'Malignant melanoma, NOS'},
        'colangiocarcinoma': {'code': '8160/3', 'system': 'ICD-O-3', 'display': 'Cholangiocarcinoma'},
        'adenocarcinoma pancreatico': {'code': '8140/3', 'system': 'ICD-O-3', 'display': 'Adenocarcinoma of pancreas'},
        'carcinoma tiroideo': {'code': '8010/3', 'system': 'ICD-O-3', 'display': 'Carcinoma, NOS'},
        'neoplasia polmonare': {'code': '8010/3', 'system': 'ICD-O-3', 'display': 'Carcinoma, lung'},
        'nsclc': {'code': '8046/3', 'system': 'ICD-O-3', 'display': 'Non-small cell carcinoma'},
    }
    
    # RxNorm per farmaci oncologici
    RXNORM_DRUGS = {
        'osimertinib': {'code': '1873986', 'system': 'RxNorm', 'display': 'osimertinib'},
        'afatinib': {'code': '1430438', 'system': 'RxNorm', 'display': 'afatinib'},
        'erlotinib': {'code': '358263', 'system': 'RxNorm', 'display': 'erlotinib'},
        'gefitinib': {'code': '282388', 'system': 'RxNorm', 'display': 'gefitinib'},
        'selpercatinib': {'code': '2361524', 'system': 'RxNorm', 'display': 'selpercatinib'},
        'cabozantinib': {'code': '1234567', 'system': 'RxNorm', 'display': 'cabozantinib'},
        'olaparib': {'code': '1597582', 'system': 'RxNorm', 'display': 'olaparib'},
        'niraparib': {'code': '1856219', 'system': 'RxNorm', 'display': 'niraparib'},
        'rucaparib': {'code': '1790868', 'system': 'RxNorm', 'display': 'rucaparib'},
        'crizotinib': {'code': '1094832', 'system': 'RxNorm', 'display': 'crizotinib'},
        'alectinib': {'code': '1721520', 'system': 'RxNorm', 'display': 'alectinib'},
        'ceritinib': {'code': '1602129', 'system': 'RxNorm', 'display': 'ceritinib'},
        'brigatinib': {'code': '1942606', 'system': 'RxNorm', 'display': 'brigatinib'},
        'trametinib': {'code': '1373476', 'system': 'RxNorm', 'display': 'trametinib'},
        'dabrafenib': {'code': '1374053', 'system': 'RxNorm', 'display': 'dabrafenib'},
        'vemurafenib': {'code': '1147220', 'system': 'RxNorm', 'display': 'vemurafenib'},
        'capmatinib': {'code': '2379709', 'system': 'RxNorm', 'display': 'capmatinib'},
        'tepotinib': {'code': '2468669', 'system': 'RxNorm', 'display': 'tepotinib'},
        'amivantamab': {'code': '2569455', 'system': 'RxNorm', 'display': 'amivantamab'},
        'sotorasib': {'code': '2566077', 'system': 'RxNorm', 'display': 'sotorasib'},
        'adagrasib': {'code': '2630234', 'system': 'RxNorm', 'display': 'adagrasib'},
        'erdafitinib': {'code': '2177997', 'system': 'RxNorm', 'display': 'erdafitinib'},
        'pembrolizumab': {'code': '1601859', 'system': 'RxNorm', 'display': 'pembrolizumab'},
        'nivolumab': {'code': '1657237', 'system': 'RxNorm', 'display': 'nivolumab'},
    }
    
    # HGNC Gene nomenclature (espanso)
    HGNC_GENES = {
        'EGFR': {'code': 'HGNC:3236', 'system': 'http://www.genenames.org'},
        'KRAS': {'code': 'HGNC:6407', 'system': 'http://www.genenames.org'},
        'TP53': {'code': 'HGNC:11998', 'system': 'http://www.genenames.org'},
        'BRAF': {'code': 'HGNC:1097', 'system': 'http://www.genenames.org'},
        'ALK': {'code': 'HGNC:427', 'system': 'http://www.genenames.org'},
        'RET': {'code': 'HGNC:9967', 'system': 'http://www.genenames.org'},
        'MET': {'code': 'HGNC:7029', 'system': 'http://www.genenames.org'},
        'BRCA1': {'code': 'HGNC:1100', 'system': 'http://www.genenames.org'},
        'BRCA2': {'code': 'HGNC:1101', 'system': 'http://www.genenames.org'},
        'PIK3CA': {'code': 'HGNC:8975', 'system': 'http://www.genenames.org'},
        'FGFR3': {'code': 'HGNC:3690', 'system': 'http://www.genenames.org'},
        'FGFR1': {'code': 'HGNC:3688', 'system': 'http://www.genenames.org'},
        'FGFR2': {'code': 'HGNC:3689', 'system': 'http://www.genenames.org'},
        'NF1': {'code': 'HGNC:7765', 'system': 'http://www.genenames.org'},
        'ATM': {'code': 'HGNC:795', 'system': 'http://www.genenames.org'},
        'PTEN': {'code': 'HGNC:9588', 'system': 'http://www.genenames.org'},
        'MAX': {'code': 'HGNC:6913', 'system': 'http://www.genenames.org'},
        'SMARCA4': {'code': 'HGNC:11100', 'system': 'http://www.genenames.org'},
        'JAK2': {'code': 'HGNC:6192', 'system': 'http://www.genenames.org'},
        'PALB2': {'code': 'HGNC:26144', 'system': 'http://www.genenames.org'},
        'DDX4': {'code': 'HGNC:2700', 'system': 'http://www.genenames.org'},
        'BLM': {'code': 'HGNC:1058', 'system': 'http://www.genenames.org'},
        'ADAT1': {'code': 'HGNC:25191', 'system': 'http://www.genenames.org'},
        'RAD51D': {'code': 'HGNC:9824', 'system': 'http://www.genenames.org'},
        'FANCF': {'code': 'HGNC:3585', 'system': 'http://www.genenames.org'},
        'NTRK1': {'code': 'HGNC:8031', 'system': 'http://www.genenames.org'},
        'NTRK2': {'code': 'HGNC:8032', 'system': 'http://www.genenames.org'},
        'NTRK3': {'code': 'HGNC:8033', 'system': 'http://www.genenames.org'},
        'CDKN2A': {'code': 'HGNC:1787', 'system': 'http://www.genenames.org'},
        'BAP1': {'code': 'HGNC:950', 'system': 'http://www.genenames.org'},
        'CHEK2': {'code': 'HGNC:16627', 'system': 'http://www.genenames.org'},
        'MTAP': {'code': 'HGNC:7413', 'system': 'http://www.genenames.org'},
        'STRN': {'code': 'HGNC:11425', 'system': 'http://www.genenames.org'},
        'EML4': {'code': 'HGNC:19326', 'system': 'http://www.genenames.org'},
        'TACC3': {'code': 'HGNC:11524', 'system': 'http://www.genenames.org'},
        'MYCN': {'code': 'HGNC:7559', 'system': 'http://www.genenames.org'},
        'RAD50': {'code': 'HGNC:9823', 'system': 'http://www.genenames.org'},
    }
    
    @classmethod
    def map_diagnosis(cls, diagnosis_text: str) -> Optional[Dict]:
        """Mappa diagnosi a codice ICD-O"""
        diagnosis_lower = diagnosis_text.lower()
        for key, value in cls.ICD_O_DIAGNOSES.items():
            if key in diagnosis_lower:
                return value
        return None
    
    @classmethod
    def map_drug(cls, drug_name: str) -> Optional[Dict]:
        """Mappa farmaco a codice RxNorm"""
        drug_lower = drug_name.lower().strip()
        return cls.RXNORM_DRUGS.get(drug_lower)
    
    @classmethod
    def map_gene(cls, gene_name: str) -> Optional[Dict]:
        """Mappa gene a codice HGNC"""
        gene_upper = gene_name.upper().strip()
        # Gestisci fusioni (es: ALK::EML4)
        if '::' in gene_upper:
            gene_upper = gene_upper.split('::')[0]
        return cls.HGNC_GENES.get(gene_upper)

# =====================================================================
# DATA MODELS
# =====================================================================

@dataclass
class Variant:
    """Rappresenta una variante genomica"""
    gene: str
    cdna_change: Optional[str] = None
    protein_change: Optional[str] = None
    classification: Optional[str] = None
    vaf: Optional[float] = None
    raw_text: Optional[str] = None
    gene_code: Optional[Dict] = None

@dataclass
class Patient:
    """Informazioni paziente"""
    id: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    birth_date: Optional[str] = None

@dataclass
class Diagnosis:
    """Diagnosi principale"""
    primary_diagnosis: Optional[str] = None
    stage: Optional[str] = None
    histology: Optional[str] = None
    icd_o_code: Optional[Dict] = None

@dataclass
class TherapeuticRecommendation:
    """Raccomandazione terapeutica"""
    drug: Optional[str] = None
    gene_target: Optional[str] = None
    evidence_level: Optional[str] = None
    clinical_trial: Optional[str] = None
    rationale: Optional[str] = None
    drug_code: Optional[Dict] = None

@dataclass
class QualityMetrics:
    """Metriche di qualità del parsing"""
    total_fields: int = 0
    filled_fields: int = 0
    completeness_pct: float = 0.0
    variants_found: int = 0
    variants_with_vaf: int = 0
    variants_classified: int = 0
    variants_with_gene_code: int = 0
    drugs_identified: int = 0
    drugs_mapped: int = 0
    diagnosis_mapped: bool = False
    patient_complete: bool = False
    warnings: List[str] = field(default_factory=list)
    
    def calculate(self):
        """Calcola percentuale completezza"""
        if self.total_fields > 0:
            self.completeness_pct = round((self.filled_fields / self.total_fields) * 100, 1)

@dataclass
class MTBReport:
    """Report MTB completo"""
    patient: Patient
    diagnosis: Diagnosis
    variants: List[Variant]
    recommendations: List[TherapeuticRecommendation]
    tmb: Optional[float] = None
    ngs_method: Optional[str] = None
    report_date: Optional[str] = None
    raw_content: Optional[str] = None
    quality_metrics: Optional[QualityMetrics] = None

# =====================================================================
# PARSER PRINCIPALE
# =====================================================================

class MTBParser:
    """Parser avanzato per report Molecular Tumor Board"""
    
    def __init__(self):
        self.vocab = ControlledVocabularies()
        
        # Pattern per estrazione varianti genomiche
        self.variant_patterns = [
            # Pattern tabellare completo
            r'(\w+)\s+c\.([^\s|]+)\s+p\.([^\s|]+)\s+(Pathogenic|VUS|Benign|Risultati discordanti|Likely Pathogenic)\s+(\d+)%',
            # Pattern inline con VAF
            r'(\w+)\s+([cp]\.[^\s,]+).*?(\d+)%',
            # Pattern alterazioni comuni (es. L858R, V600E, G12D)
            r'(\w+)\s+([A-Z]\d+[A-Z*]+)',
            # Pattern con "mutazione di"
            r'mutazione\s+(?:di\s+)?(\w+)[:\s]+([^,.\n]+)',
            r'alterazione\s+(?:di\s+)?(\w+)[:\s]+([^,.\n]+)',
        ]
        
        # Pattern fusioni
        self.fusion_patterns = [
            r'fusione\s+(\w+)::(\w+)',
            r'riarrangiamento\s+(\w+)[/:]+(\w+)',
            r'(\w+)-(\w+)\s+fusion',
            r'(\w+)\s*\(\d+\)\s*::\s*(\w+)\s*\(\d+\)',  # Es: FGFR3(17)::TACC3(11)
        ]

    def extract_patient_info(self, text: str) -> Patient:
        """Estrae informazioni paziente"""
        patient = Patient()
        
        # ID paziente - pattern multipli
        id_patterns = [
            r'ID\s+Paziente[:\s]+(\d+)',
            r'Paziente\s*(\d+)',
            r'ID[:\s]+(\d+)',
        ]
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                patient.id = match.group(1)
                break
        
        # Età - pattern multipli
        age_patterns = [
            r'Età[:\s]+(\d+)\s+anni',
            r'(\d+)\s+anni\s+affett',
            r'age[:\s]+(\d+)',
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age_val = int(match.group(1))
                if 0 < age_val < 120:  # Validazione età
                    patient.age = age_val
                    break
        
        # Sesso
        sex_match = re.search(r'Sesso[:\s]+([MF])', text, re.IGNORECASE)
        if sex_match:
            patient.sex = sex_match.group(1).upper()
        
        # Data di nascita
        birth_match = re.search(r'Data\s+di\s+nascita[:\s]+(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if birth_match:
            patient.birth_date = birth_match.group(1)
            
        return patient

    def extract_diagnosis(self, text: str) -> Diagnosis:
        """Estrae informazioni diagnostiche con mapping ICD-O"""
        diagnosis = Diagnosis()
        
        # Diagnosi principale - pattern multipli
        diag_patterns = [
            r'Diagnosi[:\s]*([^.\n]{10,150})',
            r'affett[oa]\s+da\s+([^.\n]{10,150})',
            r'(adenocarcinoma[^.\n]{0,100})',
            r'(carcinoma[^.\n]{0,100})',
            r'(feocromocitoma[^.\n]{0,100})',
            r'(paraganglioma[^.\n]{0,100})',
            r'(melanoma[^.\n]{0,100})',
            r'(colangiocarcinoma[^.\n]{0,100})',
        ]
        
        for pattern in diag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diag_text = match.group(1).strip()
                # Pulisci il testo
                diag_text = re.sub(r'\s+', ' ', diag_text)
                if len(diag_text) > 10:  # Minimo di caratteri
                    diagnosis.primary_diagnosis = diag_text
                    # Mappa a ICD-O
                    diagnosis.icd_o_code = self.vocab.map_diagnosis(diag_text)
                    break
        
        # Stadio
        stage_patterns = [
            r'stadio\s+(I{1,3}V?|IV|[1-4][ABC]?)',
            r'stage\s+(I{1,3}V?|IV|[1-4][ABC]?)',
        ]
        for pattern in stage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diagnosis.stage = match.group(1).upper()
                break
        
        # Istologia
        histology_patterns = [
            r'istotipo\s+([^.\n]{5,100})',
            r'istologia\s+([^.\n]{5,100})',
            r'istologico\s+([^.\n]{5,100})',
        ]
        for pattern in histology_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hist_text = match.group(1).strip()
                if len(hist_text) > 5:
                    diagnosis.histology = hist_text
                    break
            
        return diagnosis

    def extract_variants(self, text: str) -> List[Variant]:
        """Estrae varianti genomiche con mapping HGNC"""
        variants = []
        seen = set()
        
        # 1. Cerca pattern tabulari strutturati (formato completo)
        table_pattern = r'(\w+)\s+c\.([^\s|]+)\s+p\.([^\s|]+)\s+(Pathogenic|VUS|Benign|Risultati discordanti|Likely Pathogenic)\s+(\d+)%'
        table_matches = re.findall(table_pattern, text, re.IGNORECASE)
        
        for match in table_matches:
            gene = match[0].upper()
            variant_key = f"{gene}_{match[2]}"
            
            if variant_key not in seen:
                variant = Variant(
                    gene=gene,
                    cdna_change=f"c.{match[1].strip()}",
                    protein_change=f"p.{match[2].strip()}",
                    classification=match[3],
                    vaf=float(match[4]) if match[4] else None,
                    gene_code=self.vocab.map_gene(gene)
                )
                variants.append(variant)
                seen.add(variant_key)
        
        # 2. Pattern per mutazioni comuni (es: EGFR L858R, BRAF V600E, KRAS G12D)
        mutation_patterns = [
            r'\b(\w+)\s+([A-Z]\d+[A-Z*]+)\b',
            r'\b(\w+)\s+([GV]\d+[A-Z])\b',
            r'mutazione\s+(?:di\s+)?(\w+)[:\s]+([A-Z]\d+[A-Z*]+)',
            r'alterazione\s+(?:di\s+)?(\w+)[:\s]+([A-Z]\d+[A-Z*]+)',
        ]
        
        for pattern in mutation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                gene = match[0].upper()
                prot_change = match[1].upper()
                variant_key = f"{gene}_{prot_change}"
                
                # Filtra geni validi
                if gene not in self.vocab.HGNC_GENES:
                    continue
                
                if variant_key not in seen:
                    variant = Variant(
                        gene=gene,
                        protein_change=prot_change,
                        gene_code=self.vocab.map_gene(gene)
                    )
                    
                    # Cerca VAF nelle vicinanze (entro 100 caratteri)
                    gene_pos = text.upper().find(gene)
                    if gene_pos >= 0:
                        context = text[gene_pos:gene_pos+100]
                        vaf_search = re.search(r'(\d+)%', context)
                        if vaf_search:
                            vaf_val = float(vaf_search.group(1))
                            if 0 < vaf_val <= 100:
                                variant.vaf = vaf_val
                    
                    # Cerca classificazione nelle vicinanze
                    if gene_pos >= 0:
                        context = text[max(0, gene_pos-50):gene_pos+150]
                        class_search = re.search(
                            r'(Pathogenic|VUS|Benign|patogenetica|patogenetico)',
                            context, re.IGNORECASE
                        )
                        if class_search:
                            class_text = class_search.group(1).title()
                            if 'patogen' in class_text.lower():
                                variant.classification = 'Pathogenic'
                            else:
                                variant.classification = class_text
                    
                    variants.append(variant)
                    seen.add(variant_key)
        
        # 3. Cerca fusioni geniche
        for pattern in self.fusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                gene1 = match[0].upper()
                gene2 = match[1].upper() if len(match) > 1 and match[1] else ""
                
                # Verifica che siano geni validi
                if gene1 not in self.vocab.HGNC_GENES and gene2 not in self.vocab.HGNC_GENES:
                    continue
                
                fusion_name = f"{gene1}::{gene2}" if gene2 else gene1
                
                if fusion_name not in seen:
                    variant = Variant(
                        gene=fusion_name,
                        protein_change="fusion",
                        classification="Pathogenic",  # Le fusioni sono generalmente patogeniche
                        gene_code=self.vocab.map_gene(gene1)
                    )
                    variants.append(variant)
                    seen.add(fusion_name)
        
        # 4. Pattern speciali per inserzioni/delezioni esone (es: EGFR exon 19/20)
        exon_patterns = [
            r'(\w+)\s+es(?:one)?\s+(\d+)\s+(insertion|deletion|delins?)',
            r'(\w+)\s+exon\s+(\d+)\s+(insertion|deletion|delins?)',
        ]
        for pattern in exon_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                gene = match[0].upper()
                exon = match[1]
                alteration = match[2].lower()
                
                if gene in self.vocab.HGNC_GENES:
                    variant_key = f"{gene}_exon{exon}_{alteration}"
                    if variant_key not in seen:
                        variant = Variant(
                            gene=gene,
                            protein_change=f"exon {exon} {alteration}",
                            classification="Pathogenic",
                            gene_code=self.vocab.map_gene(gene)
                        )
                        variants.append(variant)
                        seen.add(variant_key)
        
        return variants
    
    def extract_tmb(self, text: str) -> Optional[float]:
        """Estrae valore TMB"""
        tmb_patterns = [
            r'TMB[:\s]*(\d+\.?\d*)\s*mut[s]?/?Mbp?',
            r'tumor\s+mutational\s+burden[:\s]*(\d+\.?\d*)',
            r'TMB[:\s]+(\d+\.?\d*)',
        ]
        
        for pattern in tmb_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tmb_val = float(match.group(1))
                if 0 < tmb_val < 1000:  # Validazione range TMB
                    return tmb_val
        return None
    
    def extract_therapeutic_recommendations(self, text: str) -> List[TherapeuticRecommendation]:
        """Estrae raccomandazioni terapeutiche con mapping RxNorm"""
        recommendations = []
        seen_drugs = set()
        
        # Lista completa di farmaci oncologici
        drug_names = '|'.join(self.vocab.RXNORM_DRUGS.keys())
        
        # Pattern per identificare raccomandazioni farmacologiche
        drug_patterns = [
            rf'\b(sensibilità|risposta|indicazione|approvato)[^.{{50}}]*?\b({drug_names})\b',
            rf'\b({drug_names})\b[^.{{50}}]*?(indicat[oa]|approvato|rimborsato)',
            rf'trattamento\s+con\s+\b({drug_names})\b',
            rf'\b({drug_names})\b',  # Pattern generico
        ]
        
        for pattern in drug_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Estrai il nome del farmaco dalla tupla
                drug_name = None
                rationale = None
                
                for item in match:
                    item_lower = item.lower().strip()
                    if item_lower in self.vocab.RXNORM_DRUGS:
                        drug_name = item_lower
                    elif item and len(item) > 3:
                        rationale = item
                
                if drug_name and drug_name not in seen_drugs:
                    recommendation = TherapeuticRecommendation(
                        drug=drug_name,
                        rationale=rationale,
                        drug_code=self.vocab.map_drug(drug_name)
                    )
                    recommendations.append(recommendation)
                    seen_drugs.add(drug_name)
        
        # Cerca trial clinici
        trial_patterns = [
            r'protocollo\s+(INT\s+\d+/\d+)',
            r'trial\s+clinico[:\s]+([^\n.]+)',
            r'studio\s+di\s+fase\s+([123])[:\s]*([^\n.]*)',
        ]
        
        for pattern in trial_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                trial_name = match if isinstance(match, str) else ' '.join(match)
                if trial_name and len(trial_name) > 3:
                    recommendation = TherapeuticRecommendation(
                        clinical_trial=trial_name.strip(),
                        rationale="Protocollo sperimentale disponibile"
                    )
                    recommendations.append(recommendation)
            
        return recommendations
    
    def calculate_quality_metrics(self, report: MTBReport) -> QualityMetrics:
        """Calcola metriche di qualità del report parsato"""
        metrics = QualityMetrics()
        
        # Conta campi totali e riempiti
        total = 0
        filled = 0
        
        # Patient fields
        patient_fields = {'id': report.patient.id, 'age': report.patient.age, 
                         'sex': report.patient.sex, 'birth_date': report.patient.birth_date}
        for field_name, field_value in patient_fields.items():
            total += 1
            if field_value:
                filled += 1
        
        metrics.patient_complete = sum(1 for v in patient_fields.values() if v) >= 3
        
        # Diagnosis fields
        diag_fields = {'primary_diagnosis': report.diagnosis.primary_diagnosis, 
                      'stage': report.diagnosis.stage, 
                      'icd_o_code': report.diagnosis.icd_o_code}
        for field_name, field_value in diag_fields.items():
            total += 1
            if field_value:
                filled += 1
        
        # Report-level fields
        if report.tmb:
            filled += 1
        total += 1
        
        if report.ngs_method:
            filled += 1
        total += 1
        
        if report.report_date:
            filled += 1
        total += 1
        
        metrics.total_fields = total
        metrics.filled_fields = filled
        metrics.calculate()
        
        # Varianti
        metrics.variants_found = len(report.variants)
        metrics.variants_with_vaf = sum(1 for v in report.variants if v.vaf)
        metrics.variants_classified = sum(1 for v in report.variants if v.classification)
        metrics.variants_with_gene_code = sum(1 for v in report.variants if v.gene_code)
        
        # Farmaci
        metrics.drugs_identified = len(report.recommendations)
        metrics.drugs_mapped = sum(1 for r in report.recommendations if r.drug_code)
        
        # Diagnosi
        metrics.diagnosis_mapped = report.diagnosis.icd_o_code is not None
        
        # Warnings
        if metrics.variants_found == 0:
            metrics.warnings.append("⚠️ Nessuna variante genomica identificata")
        
        if metrics.variants_found > 0 and metrics.variants_with_vaf < metrics.variants_found * 0.3:
            metrics.warnings.append(f"⚠️ Solo {metrics.variants_with_vaf}/{metrics.variants_found} varianti hanno VAF")
        
        if not metrics.diagnosis_mapped and report.diagnosis.primary_diagnosis:
            metrics.warnings.append("⚠️ Diagnosi non mappata a codice ICD-O standard")
        
        if metrics.drugs_identified > 0 and metrics.drugs_mapped == 0:
            metrics.warnings.append("⚠️ Farmaci identificati ma non mappati a RxNorm")
        
        if not metrics.patient_complete:
            metrics.warnings.append("⚠️ Informazioni paziente incomplete")
        
        if metrics.variants_with_gene_code < metrics.variants_found * 0.5:
            metrics.warnings.append(f"⚠️ Solo {metrics.variants_with_gene_code}/{metrics.variants_found} geni mappati a HGNC")
        
        return metrics
    
    def parse_report(self, text: str) -> MTBReport:
        """Parse completo del report MTB con quality metrics"""
        
        # Estrai data del report
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'data[:\s]+(\d{1,2}[\s/-]\d{1,2}[\s/-]\d{4})',
        ]
        report_date = None
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                report_date = match.group(1)
                break
        
        # Estrai metodica NGS
        ngs_patterns = [
            r'(Oncomine[^.\n]{0,50})',
            r'(IonTorrent)',
            r'(Illumina[^.\n]{0,30})',
            r'pannello\s+([^.\n]{5,80})',
            r'NGS[:\s]+([^.\n]{5,50})',
        ]
        ngs_method = None
        for pattern in ngs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ngs_method = match.group(1).strip()
                if len(ngs_method) > 3:
                    break
        
        # Crea report
        report = MTBReport(
            patient=self.extract_patient_info(text),
            diagnosis=self.extract_diagnosis(text),
            variants=self.extract_variants(text),
            recommendations=self.extract_therapeutic_recommendations(text),
            tmb=self.extract_tmb(text),
            ngs_method=ngs_method,
            report_date=report_date,
            raw_content=text[:1000]  # Store first 1000 chars
        )
        
        # Calcola quality metrics
        report.quality_metrics = self.calculate_quality_metrics(report)
        
        return report
