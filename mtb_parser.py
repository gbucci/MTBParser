#!/usr/bin/env python3
"""
Molecular Tumor Board Report Parser e FHIR Mapper
Estrae e standardizza dati clinici molecolari dai report MTB italiani
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd

@dataclass
class Variant:
    """Rappresenta una variante genomica"""
    gene: str
    cdna_change: Optional[str] = None
    protein_change: Optional[str] = None
    classification: Optional[str] = None
    vaf: Optional[float] = None
    raw_text: Optional[str] = None

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

@dataclass
class TherapeuticRecommendation:
    """Raccomandazione terapeutica"""
    drug: Optional[str] = None
    gene_target: Optional[str] = None
    evidence_level: Optional[str] = None
    clinical_trial: Optional[str] = None
    rationale: Optional[str] = None

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

class MTBParser:
    """Parser per report Molecular Tumor Board"""
    
    def __init__(self):
        # Pattern per estrazione varianti genomiche
        self.variant_patterns = [
            # Pattern tabellare (Gene | Variante cDNA | Variante aminoacidica | Classificazione | VAF)
            r'(\w+)\s+c\.([^|]+)\s+p\.([^|]+)\s+(Pathogenic|VUS|Benign|Risultati discordanti)\s+(\d+)%',
            # Pattern inline con percentuale
            r'(\w+)\s+([cp]\.[^\s,]+).*?(\d+)%',
            # Pattern semplice gene + alterazione
            r'(\w+)\s+([A-Z]\d+[A-Z*])',
            # Pattern fusioni
            r'fusione\s+(\w+):?:?(\w+)',
            r'riarrangiamento\s+(\w+)/?(\w+)?'
        ]
        
        # Pattern per classificazioni patogenicità
        self.classification_map = {
            'pathogenic': 'Pathogenic',
            'patogenetica': 'Pathogenic',
            'patogenetico': 'Pathogenic',
            'vus': 'VUS',
            'variant of uncertain significance': 'VUS',
            'variante a significato incerto': 'VUS',
            'benign': 'Benign',
            'benigna': 'Benign',
            'likely pathogenic': 'Likely Pathogenic',
            'verosimilmente patogenetica': 'Likely Pathogenic'
        }
        
        # Pattern farmaci
        self.drug_patterns = [
            r'(osimertinib|afatinib|erlotinib|gefitinib)',  # EGFR TKI
            r'(selpercatinib|cabozantinib)',  # RET inhibitors
            r'(olaparib|niraparib|rucaparib)',  # PARP inhibitors
            r'(crizotinib|alectinib|ceritinib|brigatinib)',  # ALK inhibitors
            r'(trametinib|dabrafenib|vemurafenib)',  # BRAF/MEK inhibitors
            r'(capmatinib|tepotinib)',  # MET inhibitors
            r'(amivantamab)',  # EGFR exon 20
            r'(sotorasib|adagrasib)',  # KRAS G12C
            r'(erdafitinib)',  # FGFR inhibitors
        ]

    def extract_patient_info(self, text: str) -> Patient:
        """Estrae informazioni paziente"""
        patient = Patient()
        
        # ID paziente
        id_match = re.search(r'ID Paziente[:\s]+(\d+)', text, re.IGNORECASE)
        if id_match:
            patient.id = id_match.group(1)
        
        # Età
        age_match = re.search(r'Età[:\s]+(\d+)\s+anni', text, re.IGNORECASE)
        if age_match:
            patient.age = int(age_match.group(1))
        
        # Sesso
        sex_match = re.search(r'Sesso[:\s]+([MF])', text, re.IGNORECASE)
        if sex_match:
            patient.sex = sex_match.group(1)
        
        # Data di nascita
        birth_match = re.search(r'Data di nascita[:\s]+(\d{2}/\d{2}/\d{4})', text)
        if birth_match:
            patient.birth_date = birth_match.group(1)
            
        return patient

    def extract_diagnosis(self, text: str) -> Diagnosis:
        """Estrae informazioni diagnostiche"""
        diagnosis = Diagnosis()
        
        # Diagnosi principale
        diag_patterns = [
            r'Diagnosi[:\s]*([^.]+)',
            r'adenocarcinoma|carcinoma|feocromocitoma|paraganglioma|melanoma|colangiocarcinoma',
            r'neoplasia polmonare|tumore polmonare'
        ]
        
        for pattern in diag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                diagnosis.primary_diagnosis = match.group(0 if len(match.groups()) == 0 else 1).strip()
                break
        
        # Stadio
        stage_match = re.search(r'stadio\s+(I{1,3}V?|IV)', text, re.IGNORECASE)
        if stage_match:
            diagnosis.stage = stage_match.group(1)
            
        return diagnosis

    def extract_variants(self, text: str) -> List[Variant]:
        """Estrae varianti genomiche dal testo"""
        variants = []
        
        # Cerca pattern tabulari strutturati
        table_pattern = r'(\w+)\s+c\.([^|]+)\|?\s+p\.([^|]+)\|?\s+(Pathogenic|VUS|Benign|Risultati discordanti)\s+(\d+)%'
        table_matches = re.findall(table_pattern, text, re.IGNORECASE)
        
        for match in table_matches:
            variant = Variant(
                gene=match[0],
                cdna_change=f"c.{match[1].strip()}",
                protein_change=f"p.{match[2].strip()}",
                classification=match[3],
                vaf=float(match[4]) if match[4] else None
            )
            variants.append(variant)
        
        # Cerca pattern più generali per varianti non tabulari
        mutation_patterns = [
            r'(\w+)\s+([A-Z]\d+[A-Z*])',  # Es: EGFR L858R
            r'mutazione\s+di\s+(\w+)[:\s]+([^,.\n]+)',
            r'alterazione\s+di\s+(\w+)[:\s]+([^,.\n]+)',
            r'(\w+)\s+([GV]\d+[A-Z])',  # Es: BRAF V600E
        ]
        
        for pattern in mutation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Evita duplicati
                if not any(v.gene == match[0] and match[1] in (v.protein_change or '') for v in variants):
                    variant = Variant(
                        gene=match[0],
                        protein_change=match[1] if match[1] else None
                    )
                    
                    # Cerca VAF nelle vicinanze
                    vaf_search = re.search(rf'{re.escape(match[0])}.*?(\d+)%', text, re.IGNORECASE)
                    if vaf_search:
                        variant.vaf = float(vaf_search.group(1))
                    
                    variants.append(variant)
        
        # Cerca fusioni geniche
        fusion_patterns = [
            r'fusione\s+(\w+)::(\w+)',
            r'riarrangiamento\s+(\w+)/?(\w+)',
            r'(\w+)-(\w+)\s+fusion'
        ]
        
        for pattern in fusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                variant = Variant(
                    gene=f"{match[0]}::{match[1]}",
                    protein_change="fusion"
                )
                variants.append(variant)
        
        return variants
    
    def extract_tmb(self, text: str) -> Optional[float]:
        """Estrae valore TMB"""
        tmb_match = re.search(r'TMB.*?(\d+\.?\d*)\s*muts?/?Mbp?', text, re.IGNORECASE)
        if tmb_match:
            return float(tmb_match.group(1))
        return None
    
    def extract_therapeutic_recommendations(self, text: str) -> List[TherapeuticRecommendation]:
        """Estrae raccomandazioni terapeutiche"""
        recommendations = []
        
        # Pattern per farmaci con razionale
        drug_pattern = r'(sensibilità|risposta|indicazione).*?(osimertinib|afatinib|selpercatinib|olaparib|trametinib|dabrafenib|amivantamab|sotorasib|erdafitinib|capmatinib|tepotinib|crizotinib|alectinib)'
        
        matches = re.findall(drug_pattern, text, re.IGNORECASE)
        for match in matches:
            recommendation = TherapeuticRecommendation(
                drug=match[1].lower(),
                rationale=match[0]
            )
            recommendations.append(recommendation)
        
        # Cerca trial clinici
        trial_pattern = r'protocollo.*?(INT\s+\d+/\d+|trial|studio)'
        trial_matches = re.findall(trial_pattern, text, re.IGNORECASE)
        for match in trial_matches:
            recommendation = TherapeuticRecommendation(
                clinical_trial=match,
                rationale="Protocol sperimentale"
            )
            recommendations.append(recommendation)
            
        return recommendations
    
    def parse_report(self, text: str) -> MTBReport:
        """Parse completo del report MTB"""
        
        # Estrai data del report
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text)
        report_date = date_match.group(1) if date_match else None
        
        # Estrai metodica NGS
        ngs_pattern = r'(Oncomine|IonTorrent|Illumina|NGS|next.generation.sequencing)'
        ngs_match = re.search(ngs_pattern, text, re.IGNORECASE)
        ngs_method = ngs_match.group(1) if ngs_match else None
        
        return MTBReport(
            patient=self.extract_patient_info(text),
            diagnosis=self.extract_diagnosis(text),
            variants=self.extract_variants(text),
            recommendations=self.extract_therapeutic_recommendations(text),
            tmb=self.extract_tmb(text),
            ngs_method=ngs_method,
            report_date=report_date,
            raw_content=text
        )

class FHIRMapper:
    """Mapper per conversione a FHIR R4"""
    
    def __init__(self):
        self.gene_code_map = {
            'EGFR': {'system': 'http://www.genenames.org', 'code': 'HGNC:3236'},
            'KRAS': {'system': 'http://www.genenames.org', 'code': 'HGNC:6407'},
            'TP53': {'system': 'http://www.genenames.org', 'code': 'HGNC:11998'},
            'BRAF': {'system': 'http://www.genenames.org', 'code': 'HGNC:1097'},
            'ALK': {'system': 'http://www.genenames.org', 'code': 'HGNC:427'},
            'RET': {'system': 'http://www.genenames.org', 'code': 'HGNC:9967'},
            'MET': {'system': 'http://www.genenames.org', 'code': 'HGNC:7029'},
            'BRCA1': {'system': 'http://www.genenames.org', 'code': 'HGNC:1100'},
            'BRCA2': {'system': 'http://www.genenames.org', 'code': 'HGNC:1101'}
        }
    
    def create_patient_resource(self, patient: Patient) -> Dict:
        """Crea risorsa FHIR Patient"""
        resource = {
            'resourceType': 'Patient',
            'id': patient.id or 'unknown',
            'identifier': [
                {
                    'system': 'http://int.it/patient-id',
                    'value': patient.id or 'unknown'
                }
            ],
            'gender': 'male' if patient.sex == 'M' else 'female' if patient.sex == 'F' else 'unknown'
        }
        
        if patient.birth_date:
            # Converti formato italiano in ISO
            try:
                parts = patient.birth_date.split('/')
                iso_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                resource['birthDate'] = iso_date
            except:
                pass
                
        return resource
    
    def create_variant_observation(self, variant: Variant, patient_id: str) -> Dict:
        """Crea risorsa FHIR Observation per variante genomica"""
        
        # Codice base per variante genomica
        observation = {
            'resourceType': 'Observation',
            'id': f"variant-{variant.gene}-{hash(variant.protein_change or variant.cdna_change or '')}",
            'status': 'final',
            'category': [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                            'code': 'laboratory'
                        }
                    ]
                }
            ],
            'code': {
                'coding': [
                    {
                        'system': 'http://loinc.org',
                        'code': '69548-6',
                        'display': 'Genetic variant assessment'
                    }
                ]
            },
            'subject': {
                'reference': f'Patient/{patient_id}'
            },
            'component': []
        }
        
        # Gene
        if variant.gene in self.gene_code_map:
            gene_component = {
                'code': {
                    'coding': [
                        {
                            'system': 'http://loinc.org',
                            'code': '48018-6',
                            'display': 'Gene studied [ID]'
                        }
                    ]
                },
                'valueCodeableConcept': {
                    'coding': [self.gene_code_map[variant.gene]]
                }
            }
            observation['component'].append(gene_component)
        
        # Variante aminoacidica
        if variant.protein_change:
            protein_component = {
                'code': {
                    'coding': [
                        {
                            'system': 'http://loinc.org',
                            'code': '48005-3',
                            'display': 'Amino acid change (pHGVS)'
                        }
                    ]
                },
                'valueString': variant.protein_change
            }
            observation['component'].append(protein_component)
        
        # Variante DNA
        if variant.cdna_change:
            dna_component = {
                'code': {
                    'coding': [
                        {
                            'system': 'http://loinc.org',
                            'code': '48004-6',
                            'display': 'DNA change (cHGVS)'
                        }
                    ]
                },
                'valueString': variant.cdna_change
            }
            observation['component'].append(dna_component)
        
        # VAF (Variant Allele Frequency)
        if variant.vaf:
            vaf_component = {
                'code': {
                    'coding': [
                        {
                            'system': 'http://loinc.org',
                            'code': '81258-6',
                            'display': 'Variant allele frequency'
                        }
                    ]
                },
                'valueQuantity': {
                    'value': variant.vaf,
                    'unit': '%',
                    'system': 'http://unitsofmeasure.org',
                    'code': '%'
                }
            }
            observation['component'].append(vaf_component)
        
        # Classificazione patogenicità
        if variant.classification:
            interpretation = {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': self._map_classification_to_fhir(variant.classification)
                    }
                ]
            }
            observation['interpretation'] = [interpretation]
        
        return observation
    
    def _map_classification_to_fhir(self, classification: str) -> str:
        """Mappa classificazioni a codici FHIR"""
        mapping = {
            'Pathogenic': 'A',  # Abnormal
            'Likely Pathogenic': 'A',
            'VUS': 'I',  # Intermediate
            'Likely Benign': 'N',  # Normal
            'Benign': 'N'
        }
        return mapping.get(classification, 'I')
    
    def create_diagnostic_report(self, mtb_report: MTBReport) -> Dict:
        """Crea risorsa FHIR DiagnosticReport"""
        
        report = {
            'resourceType': 'DiagnosticReport',
            'id': f"mtb-report-{mtb_report.patient.id or 'unknown'}",
            'status': 'final',
            'category': [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                            'code': 'GE',
                            'display': 'Genetics'
                        }
                    ]
                }
            ],
            'code': {
                'coding': [
                    {
                        'system': 'http://loinc.org',
                        'code': '81247-9',
                        'display': 'Master HL7 genetic variant reporting panel'
                    }
                ]
            },
            'subject': {
                'reference': f"Patient/{mtb_report.patient.id or 'unknown'}"
            },
            'result': []
        }
        
        # Aggiungi riferimenti alle osservazioni delle varianti
        for i, variant in enumerate(mtb_report.variants):
            report['result'].append({
                'reference': f"Observation/variant-{variant.gene}-{hash(variant.protein_change or variant.cdna_change or '')}"
            })
        
        # TMB come osservazione separata
        if mtb_report.tmb:
            report['result'].append({
                'reference': f"Observation/tmb-{mtb_report.patient.id or 'unknown'}"
            })
        
        return report
    
    def create_fhir_bundle(self, mtb_report: MTBReport) -> Dict:
        """Crea FHIR Bundle completo"""
        
        bundle = {
            'resourceType': 'Bundle',
            'id': f"mtb-bundle-{mtb_report.patient.id or 'unknown'}",
            'type': 'collection',
            'entry': []
        }
        
        # Patient
        patient_resource = self.create_patient_resource(mtb_report.patient)
        bundle['entry'].append({
            'resource': patient_resource
        })
        
        # Variant Observations
        for variant in mtb_report.variants:
            variant_obs = self.create_variant_observation(variant, mtb_report.patient.id or 'unknown')
            bundle['entry'].append({
                'resource': variant_obs
            })
        
        # TMB Observation
        if mtb_report.tmb:
            tmb_obs = {
                'resourceType': 'Observation',
                'id': f"tmb-{mtb_report.patient.id or 'unknown'}",
                'status': 'final',
                'code': {
                    'coding': [
                        {
                            'system': 'http://loinc.org',
                            'code': '94076-7',
                            'display': 'Mutations/Mb [# Ratio] in Tumor'
                        }
                    ]
                },
                'subject': {
                    'reference': f"Patient/{mtb_report.patient.id or 'unknown'}"
                },
                'valueQuantity': {
                    'value': mtb_report.tmb,
                    'unit': 'mutations per megabase',
                    'system': 'http://unitsofmeasure.org',
                    'code': 'mutations/Mb'
                }
            }
            bundle['entry'].append({
                'resource': tmb_obs
            })
        
        # Diagnostic Report
        diagnostic_report = self.create_diagnostic_report(mtb_report)
        bundle['entry'].append({
            'resource': diagnostic_report
        })
        
        return bundle

# Funzione principale per processing
def process_mtb_reports(file_contents: List[str]) -> List[Dict]:
    """Processa multiple report MTB e restituisce FHIR bundles"""
    parser = MTBParser()
    fhir_mapper = FHIRMapper()
    
    results = []
    
    for content in file_contents:
        # Parse report
        mtb_report = parser.parse_report(content)
        
        # Converti a FHIR
        fhir_bundle = fhir_mapper.create_fhir_bundle(mtb_report)
        
        results.append({
            'parsed_report': asdict(mtb_report),
            'fhir_bundle': fhir_bundle
        })
    
    return results

# Esempio di utilizzo
if __name__ == "__main__":
    # Test con un esempio
    sample_text = """
    ID Paziente: 4158446 Sesso: M Età: 49 anni
    Diagnosi: Feocromocitoma surrenalico con metastasi linfonodale
    
    Gene Variante cDNA Variante aminoacidica Classificazione Frequenza allelica
    DDX4 c.827T>C p.Val276Ala (V276A) VUS 52%
    MAX c.196A>T p.Lys66Ter (K66*) Pathogenic 63%
    RET c.1946C>T p.Ser649Leu (S649L) Risultati discordanti 51%
    
    Il valore del TMB è 2.85 muts/Mbp.
    Si segnala possibile sensibilità a Selpercatinib.
    """
    
    parser = MTBParser()
    report = parser.parse_report(sample_text)
    
    print("=== Report Parsato ===")
    print(f"Paziente ID: {report.patient.id}")
    print(f"Età: {report.patient.age}")
    print(f"Diagnosi: {report.diagnosis.primary_diagnosis}")
    print(f"TMB: {report.tmb}")
    print(f"Varianti trovate: {len(report.variants)}")
    
    for variant in report.variants:
        print(f"  - {variant.gene}: {variant.protein_change} ({variant.classification}, VAF: {variant.vaf}%)")
    
    # Test conversione FHIR
    fhir_mapper = FHIRMapper()
    fhir_bundle = fhir_mapper.create_fhir_bundle(report)
    
    print(f"\n=== FHIR Bundle ===")
    print(f"Risorse create: {len(fhir_bundle['entry'])}")
    print(json.dumps(fhir_bundle, indent=2)[:500] + "...")
