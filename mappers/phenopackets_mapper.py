#!/usr/bin/env python3
"""
GA4GH Phenopackets v2 Mapper - Converts MTB Report to Phenopackets format
Follows GA4GH Phenopacket Schema v2.0 specification
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

# Handle imports for both module and script execution
try:
    from core.data_models import MTBReport, Variant, Patient, Diagnosis
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Variant, Patient, Diagnosis


class PhenopacketsMapper:
    """
    Maps MTB Report to GA4GH Phenopackets v2 format

    Phenopackets is a standard for sharing disease and phenotype information
    that characterizes an individual person or biosample.

    Specification: https://phenopacket-schema.readthedocs.io/
    """

    def __init__(self):
        """Initialize Phenopackets Mapper"""
        pass

    def create_phenopacket(self, report: MTBReport) -> Dict:
        """
        Create GA4GH Phenopacket from MTB Report

        Args:
            report: Parsed MTB Report

        Returns:
            Phenopacket v2 as dictionary
        """
        phenopacket = {
            'id': f"phenopacket-{report.patient.id or 'unknown'}",
            'subject': self._create_subject(report.patient),
            'phenotypicFeatures': [],
            'measurements': [],
            'diseases': [],
            'medicalActions': [],
            'interpretations': [],
            'metaData': self._create_metadata(report)
        }

        # Add disease (diagnosis)
        if report.diagnosis.primary_diagnosis:
            phenopacket['diseases'].append(
                self._create_disease(report.diagnosis)
            )

        # Add genomic interpretations (variants)
        if report.variants:
            phenopacket['interpretations'].append(
                self._create_interpretation(report.variants, report.patient.id)
            )

        # Add TMB as measurement
        if report.tmb is not None:
            phenopacket['measurements'].append(
                self._create_tmb_measurement(report.tmb)
            )

        # Add therapeutic recommendations as medical actions
        for recommendation in report.recommendations:
            phenopacket['medicalActions'].append(
                self._create_medical_action(recommendation)
            )

        return phenopacket

    def _create_subject(self, patient: Patient) -> Dict:
        """
        Create Individual (subject) element

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/individual.html
        """
        subject = {
            'id': patient.id or 'unknown'
        }

        # Add sex
        if patient.sex:
            # Map to GA4GH sex ontology
            sex_map = {
                'M': 'MALE',
                'F': 'FEMALE'
            }
            subject['sex'] = sex_map.get(patient.sex, 'UNKNOWN_SEX')

        # Add date of birth as ISO8601Duration from birth to now (age)
        if patient.age:
            subject['timeAtLastEncounter'] = {
                'age': {
                    'iso8601duration': f"P{patient.age}Y"
                }
            }

        return subject

    def _create_disease(self, diagnosis: Diagnosis) -> Dict:
        """
        Create Disease element

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/disease.html
        """
        disease = {}

        # Use ICD-O code if available
        if diagnosis.icd_o_code:
            disease['term'] = {
                'id': f"ICD-O:{diagnosis.icd_o_code['code']}",
                'label': diagnosis.icd_o_code['display']
            }
        else:
            disease['term'] = {
                'id': 'NCIT:C3262',  # Generic 'Neoplasm' NCIT code
                'label': diagnosis.primary_diagnosis or 'Unknown neoplasm'
            }

        # Add stage if available
        if diagnosis.stage:
            disease['clinicalTnmFinding'] = [{
                'id': f"NCIT:C{diagnosis.stage}",  # Simplified - should use proper TNM codes
                'label': f"Stage {diagnosis.stage}"
            }]

        return disease

    def _create_interpretation(self, variants: List[Variant], patient_id: str) -> Dict:
        """
        Create Interpretation element with genomic interpretations

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/interpretation.html
        """
        interpretation = {
            'id': f"interpretation-{patient_id or 'unknown'}",
            'progressStatus': 'SOLVED',  # Assuming report is complete
            'diagnosis': {
                'genomicInterpretations': []
            }
        }

        # Add each variant as genomic interpretation
        for variant in variants:
            genomic_interp = self._create_genomic_interpretation(variant)
            interpretation['diagnosis']['genomicInterpretations'].append(genomic_interp)

        return interpretation

    def _create_genomic_interpretation(self, variant: Variant) -> Dict:
        """
        Create GenomicInterpretation for a variant

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/genomic-interpretation.html
        """
        genomic_interp = {
            'subjectOrBiosampleId': 'tumor-sample',
            'interpretationStatus': self._map_classification_to_interpretation_status(
                variant.classification
            )
        }

        # Create VariantInterpretation
        variant_interpretation = {
            'acmgPathogenicityClassification': self._map_classification_to_acmg(
                variant.classification
            ),
            'therapeuticActionability': 'ACTIONABLE' if variant.is_actionable() else 'NOT_ACTIONABLE',
            'variationDescriptor': self._create_variation_descriptor(variant)
        }

        genomic_interp['variantInterpretation'] = variant_interpretation

        return genomic_interp

    def _create_variation_descriptor(self, variant: Variant) -> Dict:
        """
        Create VariationDescriptor (VRS-based variant representation)

        Schema: https://vrs.ga4gh.org/en/stable/
        """
        descriptor = {
            'id': f"variant-{variant.gene}-{variant.protein_change or variant.cdna_change}",
            'geneContext': {},
            'expressions': [],
            'variationType': {}
        }

        # Add gene context with HGNC
        if variant.gene_code:
            descriptor['geneContext'] = {
                'valueId': variant.gene_code['code'],
                'symbol': variant.gene
            }
        else:
            descriptor['geneContext'] = {
                'symbol': variant.gene
            }

        # Add HGVS expressions
        if variant.protein_change:
            descriptor['expressions'].append({
                'syntax': 'hgvs.p',
                'value': variant.protein_change if variant.protein_change.startswith('p.')
                         else f"p.{variant.protein_change}"
            })

        if variant.cdna_change:
            descriptor['expressions'].append({
                'syntax': 'hgvs.c',
                'value': variant.cdna_change if variant.cdna_change.startswith('c.')
                         else f"c.{variant.cdna_change}"
            })

        # Add VAF if available
        if variant.vaf is not None:
            descriptor['allelicState'] = {
                'id': 'GENO:0000135',  # heterozygous
                'label': 'heterozygous'
            }
            # Store VAF in extension (non-standard but useful)
            descriptor['vaf'] = variant.vaf

        # Variation type
        if variant.is_fusion():
            descriptor['variationType'] = {
                'id': 'SO:0001565',
                'label': 'gene_fusion'
            }
        else:
            descriptor['variationType'] = {
                'id': 'SO:0001583',
                'label': 'missense_variant'
            }

        return descriptor

    def _create_tmb_measurement(self, tmb: float) -> Dict:
        """
        Create Measurement for TMB

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/measurement.html
        """
        return {
            'assay': {
                'id': 'LOINC:94076-7',
                'label': 'Mutations/Megabase [# Ratio] in Tumor'
            },
            'value': {
                'quantity': {
                    'unit': {
                        'id': 'UCUM:1/Mb',
                        'label': 'mutations per megabase'
                    },
                    'value': tmb
                }
            }
        }

    def _create_medical_action(self, recommendation) -> Dict:
        """
        Create MedicalAction for therapeutic recommendation

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/medical-action.html
        """
        medical_action = {
            'treatment': {
                'agent': {}
            },
            'treatmentTarget': {},
            'treatmentIntent': {
                'id': 'NCIT:C62220',
                'label': 'Therapeutic Intent'
            }
        }

        # Add drug with RxNorm code
        if recommendation.drug_code:
            medical_action['treatment']['agent'] = {
                'id': f"RxNorm:{recommendation.drug_code['code']}",
                'label': recommendation.drug_code['display']
            }
        else:
            medical_action['treatment']['agent'] = {
                'label': recommendation.drug
            }

        # Add gene target
        if recommendation.gene_target:
            medical_action['treatmentTarget'] = {
                'id': f"HGNC:{recommendation.gene_target}",
                'label': recommendation.gene_target
            }

        # Add response to treatment (evidence level)
        if recommendation.evidence_level:
            medical_action['responseToTreatment'] = {
                'id': 'NCIT:C41184',  # Evidence-based
                'label': recommendation.evidence_level
            }

        return medical_action

    def _create_metadata(self, report: MTBReport) -> Dict:
        """
        Create MetaData element

        Schema: https://phenopacket-schema.readthedocs.io/en/latest/metadata.html
        """
        metadata = {
            'created': datetime.utcnow().isoformat() + 'Z',
            'createdBy': 'MTBParser',
            'submittedBy': 'MTB Parser System v1.0',
            'resources': [
                {
                    'id': 'hgnc',
                    'name': 'HUGO Gene Nomenclature Committee',
                    'url': 'https://www.genenames.org',
                    'version': '2024',
                    'namespacePrefix': 'HGNC',
                    'iriPrefix': 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/'
                },
                {
                    'id': 'icdo3',
                    'name': 'International Classification of Diseases for Oncology, 3rd Edition',
                    'url': 'https://www.who.int/classifications/icd/adaptations/oncology/en/',
                    'version': '3.2',
                    'namespacePrefix': 'ICD-O',
                    'iriPrefix': 'http://terminology.hl7.org/CodeSystem/icd-o-3/'
                },
                {
                    'id': 'rxnorm',
                    'name': 'RxNorm',
                    'url': 'https://www.nlm.nih.gov/research/umls/rxnorm',
                    'version': '2024',
                    'namespacePrefix': 'RxNorm',
                    'iriPrefix': 'http://purl.bioontology.org/ontology/RXNORM/'
                },
                {
                    'id': 'loinc',
                    'name': 'Logical Observation Identifiers Names and Codes',
                    'url': 'https://loinc.org/',
                    'version': '2.76',
                    'namespacePrefix': 'LOINC',
                    'iriPrefix': 'http://loinc.org/rdf/'
                }
            ],
            'phenopacketSchemaVersion': '2.0'
        }

        # Add NGS method as external reference
        if report.ngs_method:
            metadata['externalReferences'] = [{
                'id': 'ngs-panel',
                'description': report.ngs_method
            }]

        return metadata

    @staticmethod
    def _map_classification_to_interpretation_status(classification: Optional[str]) -> str:
        """Map variant classification to InterpretationStatus"""
        if not classification:
            return 'UNKNOWN'

        mapping = {
            'Pathogenic': 'CAUSATIVE',
            'Likely Pathogenic': 'CONTRIBUTORY',
            'VUS': 'UNKNOWN',
            'Likely Benign': 'UNKNOWN',
            'Benign': 'UNKNOWN'
        }
        return mapping.get(classification, 'UNKNOWN')

    @staticmethod
    def _map_classification_to_acmg(classification: Optional[str]) -> str:
        """Map variant classification to ACMG category"""
        if not classification:
            return 'UNCERTAIN_SIGNIFICANCE'

        mapping = {
            'Pathogenic': 'PATHOGENIC',
            'Likely Pathogenic': 'LIKELY_PATHOGENIC',
            'VUS': 'UNCERTAIN_SIGNIFICANCE',
            'Likely Benign': 'LIKELY_BENIGN',
            'Benign': 'BENIGN'
        }
        return mapping.get(classification, 'UNCERTAIN_SIGNIFICANCE')


# Example usage
if __name__ == "__main__":
    print("=== GA4GH Phenopackets v2 Mapper Test ===\n")

    # Create sample report
    from core.data_models import Patient, Diagnosis, Variant, TherapeuticRecommendation, MTBReport

    patient = Patient(id="12345", age=65, sex="M", birth_date="1958-03-15")

    diagnosis = Diagnosis(
        primary_diagnosis="Adenocarcinoma polmonare",
        stage="IV",
        icd_o_code={'code': '8140/3', 'system': 'ICD-O-3', 'display': 'Adenocarcinoma, NOS'}
    )

    variant1 = Variant(
        gene="EGFR",
        cdna_change="c.2573T>G",
        protein_change="p.Leu858Arg",
        classification="Pathogenic",
        vaf=45.0,
        gene_code={'code': 'HGNC:3236', 'system': 'http://www.genenames.org'}
    )

    variant2 = Variant(
        gene="ALK::EML4",
        protein_change="fusion",
        classification="Pathogenic",
        gene_code={'code': 'HGNC:427', 'system': 'http://www.genenames.org'}
    )

    recommendation = TherapeuticRecommendation(
        drug="osimertinib",
        gene_target="EGFR",
        evidence_level="FDA Approved",
        drug_code={'code': '1873986', 'system': 'RxNorm', 'display': 'osimertinib'}
    )

    report = MTBReport(
        patient=patient,
        diagnosis=diagnosis,
        variants=[variant1, variant2],
        recommendations=[recommendation],
        tmb=8.5,
        ngs_method="FoundationOne CDx"
    )

    # Create Phenopacket
    mapper = PhenopacketsMapper()
    phenopacket = mapper.create_phenopacket(report)

    # Display
    print(f"Phenopacket ID: {phenopacket['id']}")
    print(f"Subject: {phenopacket['subject']['id']}, Sex: {phenopacket['subject']['sex']}")
    print(f"Diseases: {len(phenopacket['diseases'])}")
    print(f"Genomic Interpretations: {len(phenopacket['interpretations'][0]['diagnosis']['genomicInterpretations']) if phenopacket['interpretations'] else 0}")
    print(f"Medical Actions: {len(phenopacket['medicalActions'])}")
    print(f"Measurements: {len(phenopacket['measurements'])}")

    # Pretty print full phenopacket
    print("\n=== Complete Phenopacket (JSON) ===")
    print(json.dumps(phenopacket, indent=2))
