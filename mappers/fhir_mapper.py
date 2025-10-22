#!/usr/bin/env python3
"""
FHIR R4 Mapper - Converts MTB Report to FHIR R4 Bundle
Supports FHIR Genomics Reporting Implementation Guide
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# Handle imports for both module and script execution
try:
    from core.data_models import MTBReport, Variant, Patient, Diagnosis, TherapeuticRecommendation
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Variant, Patient, Diagnosis, TherapeuticRecommendation


class FHIRMapper:
    """
    Maps MTB Report to FHIR R4 Resources

    Creates:
    - Patient resource
    - Condition resource (diagnosis)
    - Observation resources (genomic variants)
    - MedicationStatement resources (recommendations)
    - DiagnosticReport resource (master report)
    - Bundle (transaction bundle containing all resources)
    """

    # LOINC codes for genomic observations
    LOINC_CODES = {
        'genetic_variant_assessment': '69548-6',
        'gene_studied': '48018-6',
        'amino_acid_change': '48005-3',
        'dna_change': '48004-6',
        'variant_allele_frequency': '81258-6',
        'tmb': '94076-7',
        'genomic_report': '81247-9',
        'genomic_region_studied': '53041-0'
    }

    def __init__(self):
        """Initialize FHIR Mapper"""
        self.base_url = "urn:uuid:"

    def create_fhir_bundle(self, report: MTBReport) -> Dict:
        """
        Create complete FHIR Bundle from MTB Report

        Args:
            report: Parsed MTB Report

        Returns:
            FHIR Bundle (transaction type) as dictionary
        """
        entries = []

        # Generate consistent UUIDs for referencing
        patient_id = str(uuid.uuid4())
        condition_id = str(uuid.uuid4())
        diagnostic_report_id = str(uuid.uuid4())

        # 1. Patient resource
        patient_resource = self.create_patient_resource(report.patient, patient_id)
        entries.append({
            'fullUrl': f'{self.base_url}{patient_id}',
            'resource': patient_resource,
            'request': {
                'method': 'POST',
                'url': 'Patient'
            }
        })

        # 2. Condition resource (diagnosis)
        if report.diagnosis.primary_diagnosis:
            condition_resource = self.create_condition_resource(
                report.diagnosis, patient_id, condition_id
            )
            entries.append({
                'fullUrl': f'{self.base_url}{condition_id}',
                'resource': condition_resource,
                'request': {
                    'method': 'POST',
                    'url': 'Condition'
                }
            })

        # 3. Variant Observations
        observation_ids = []
        for variant in report.variants:
            obs_id = str(uuid.uuid4())
            observation_ids.append(obs_id)

            variant_obs = self.create_variant_observation(variant, patient_id, obs_id)
            entries.append({
                'fullUrl': f'{self.base_url}{obs_id}',
                'resource': variant_obs,
                'request': {
                    'method': 'POST',
                    'url': 'Observation'
                }
            })

        # 4. TMB Observation
        if report.tmb is not None:
            tmb_id = str(uuid.uuid4())
            observation_ids.append(tmb_id)

            tmb_obs = self.create_tmb_observation(report.tmb, patient_id, tmb_id)
            entries.append({
                'fullUrl': f'{self.base_url}{tmb_id}',
                'resource': tmb_obs,
                'request': {
                    'method': 'POST',
                    'url': 'Observation'
                }
            })

        # 5. MedicationStatement resources
        for recommendation in report.recommendations:
            med_id = str(uuid.uuid4())
            med_statement = self.create_medication_statement(
                recommendation, patient_id, med_id
            )
            entries.append({
                'fullUrl': f'{self.base_url}{med_id}',
                'resource': med_statement,
                'request': {
                    'method': 'POST',
                    'url': 'MedicationStatement'
                }
            })

        # 6. DiagnosticReport (master report)
        diagnostic_report = self.create_diagnostic_report(
            report, patient_id, diagnostic_report_id, observation_ids
        )
        entries.append({
            'fullUrl': f'{self.base_url}{diagnostic_report_id}',
            'resource': diagnostic_report,
            'request': {
                'method': 'POST',
                'url': 'DiagnosticReport'
            }
        })

        # Create Bundle
        bundle = {
            'resourceType': 'Bundle',
            'type': 'transaction',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'entry': entries
        }

        return bundle

    def create_patient_resource(self, patient: Patient, patient_id: str) -> Dict:
        """Create FHIR Patient resource"""
        resource = {
            'resourceType': 'Patient',
            'id': patient_id
        }

        if patient.id:
            resource['identifier'] = [{
                'system': 'urn:hospital:patient-id',
                'value': patient.id
            }]

        if patient.birth_date:
            resource['birthDate'] = patient.birth_date

        if patient.sex:
            # Map to FHIR administrative gender
            gender_map = {'M': 'male', 'F': 'female'}
            resource['gender'] = gender_map.get(patient.sex, 'unknown')

        return resource

    def create_condition_resource(
        self,
        diagnosis: Diagnosis,
        patient_id: str,
        condition_id: str
    ) -> Dict:
        """Create FHIR Condition resource for diagnosis"""
        resource = {
            'resourceType': 'Condition',
            'id': condition_id,
            'subject': {
                'reference': f'{self.base_url}{patient_id}'
            },
            'clinicalStatus': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                    'code': 'active'
                }]
            }
        }

        # Add diagnosis code if mapped to ICD-O
        if diagnosis.icd_o_code:
            resource['code'] = {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/icd-o-3',
                    'code': diagnosis.icd_o_code['code'],
                    'display': diagnosis.icd_o_code['display']
                }],
                'text': diagnosis.primary_diagnosis
            }
        else:
            resource['code'] = {
                'text': diagnosis.primary_diagnosis
            }

        # Add stage if available
        if diagnosis.stage:
            resource['stage'] = [{
                'summary': {
                    'text': diagnosis.stage
                }
            }]

        return resource

    def create_variant_observation(
        self,
        variant: Variant,
        patient_id: str,
        observation_id: str
    ) -> Dict:
        """
        Create FHIR Observation resource for genomic variant
        Following FHIR Genomics Reporting IG
        """
        resource = {
            'resourceType': 'Observation',
            'id': observation_id,
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'laboratory'
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': self.LOINC_CODES['genetic_variant_assessment'],
                    'display': 'Genetic variant assessment'
                }]
            },
            'subject': {
                'reference': f'{self.base_url}{patient_id}'
            },
            'component': []
        }

        # Component: Gene studied
        if variant.gene:
            gene_component = {
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': self.LOINC_CODES['gene_studied'],
                        'display': 'Gene studied [ID]'
                    }]
                },
                'valueCodeableConcept': {
                    'text': variant.gene
                }
            }

            # Add HGNC code if available
            if variant.gene_code:
                gene_component['valueCodeableConcept']['coding'] = [{
                    'system': variant.gene_code['system'],
                    'code': variant.gene_code['code'],
                    'display': variant.gene
                }]

            resource['component'].append(gene_component)

        # Component: Protein change (pHGVS)
        if variant.protein_change:
            resource['component'].append({
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': self.LOINC_CODES['amino_acid_change'],
                        'display': 'Amino acid change (pHGVS)'
                    }]
                },
                'valueCodeableConcept': {
                    'text': variant.protein_change
                }
            })

        # Component: DNA change (cHGVS)
        if variant.cdna_change:
            resource['component'].append({
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': self.LOINC_CODES['dna_change'],
                        'display': 'DNA change (cHGVS)'
                    }]
                },
                'valueCodeableConcept': {
                    'text': variant.cdna_change
                }
            })

        # Component: Variant Allele Frequency
        if variant.vaf is not None:
            resource['component'].append({
                'code': {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': self.LOINC_CODES['variant_allele_frequency'],
                        'display': 'Variant allele frequency'
                    }]
                },
                'valueQuantity': {
                    'value': variant.vaf,
                    'unit': '%',
                    'system': 'http://unitsofmeasure.org',
                    'code': '%'
                }
            })

        # Interpretation: Clinical significance
        if variant.classification:
            resource['interpretation'] = [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                    'code': self._map_classification_to_fhir(variant.classification),
                    'display': variant.classification
                }]
            }]

        return resource

    def create_tmb_observation(
        self,
        tmb: float,
        patient_id: str,
        observation_id: str
    ) -> Dict:
        """Create FHIR Observation for Tumor Mutational Burden"""
        return {
            'resourceType': 'Observation',
            'id': observation_id,
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'laboratory'
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': self.LOINC_CODES['tmb'],
                    'display': 'Mutations/Megabase [# Ratio] in Tumor'
                }]
            },
            'subject': {
                'reference': f'{self.base_url}{patient_id}'
            },
            'valueQuantity': {
                'value': tmb,
                'unit': 'mut/Mb',
                'system': 'http://unitsofmeasure.org',
                'code': '1/Mb'
            }
        }

    def create_medication_statement(
        self,
        recommendation: TherapeuticRecommendation,
        patient_id: str,
        medication_id: str
    ) -> Dict:
        """Create FHIR MedicationStatement for therapeutic recommendation"""
        resource = {
            'resourceType': 'MedicationStatement',
            'id': medication_id,
            'status': 'intended',  # Recommendation, not yet active
            'subject': {
                'reference': f'{self.base_url}{patient_id}'
            }
        }

        # Medication coding
        medication_coding = {
            'text': recommendation.drug
        }

        if recommendation.drug_code:
            medication_coding['coding'] = [{
                'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                'code': recommendation.drug_code['code'],
                'display': recommendation.drug_code['display']
            }]

        resource['medicationCodeableConcept'] = medication_coding

        # Add note with rationale
        if recommendation.rationale or recommendation.gene_target:
            notes = []
            if recommendation.gene_target:
                notes.append(f"Target: {recommendation.gene_target}")
            if recommendation.rationale:
                notes.append(recommendation.rationale)
            if recommendation.evidence_level:
                notes.append(f"Evidence: {recommendation.evidence_level}")

            resource['note'] = [{
                'text': ' | '.join(notes)
            }]

        return resource

    def create_diagnostic_report(
        self,
        report: MTBReport,
        patient_id: str,
        report_id: str,
        observation_ids: List[str]
    ) -> Dict:
        """Create FHIR DiagnosticReport (master genomic report)"""
        resource = {
            'resourceType': 'DiagnosticReport',
            'id': report_id,
            'status': 'final',
            'category': [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'GE',
                    'display': 'Genetics'
                }]
            }],
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': self.LOINC_CODES['genomic_report'],
                    'display': 'Master HL7 genetic variant reporting panel'
                }]
            },
            'subject': {
                'reference': f'{self.base_url}{patient_id}'
            },
            'result': [
                {'reference': f'{self.base_url}{obs_id}'}
                for obs_id in observation_ids
            ]
        }

        # Add effective date if available
        if report.report_date:
            resource['effectiveDateTime'] = report.report_date

        # Add NGS method in specimen
        if report.ngs_method:
            resource['specimen'] = [{
                'display': report.ngs_method
            }]

        # Add conclusion with quality metrics
        if report.quality_metrics:
            conclusion_parts = [
                f"Completeness: {report.quality_metrics.completeness_pct}%",
                f"Variants: {report.quality_metrics.variants_found}",
                f"Actionable variants: {len(report.get_actionable_variants())}"
            ]
            resource['conclusion'] = ' | '.join(conclusion_parts)

        return resource

    @staticmethod
    def _map_classification_to_fhir(classification: str) -> str:
        """Map variant classification to FHIR interpretation codes"""
        mapping = {
            'Pathogenic': 'POS',
            'Likely Pathogenic': 'POS',
            'VUS': 'IND',
            'Likely Benign': 'NEG',
            'Benign': 'NEG'
        }
        return mapping.get(classification, 'IND')


# Example usage
if __name__ == "__main__":
    print("=== FHIR R4 Mapper Test ===\n")

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
        ngs_method="FoundationOne CDx",
        report_date="2025-10-22"
    )

    # Create FHIR Bundle
    mapper = FHIRMapper()
    fhir_bundle = mapper.create_fhir_bundle(report)

    # Display
    print(f"FHIR Bundle Type: {fhir_bundle['type']}")
    print(f"Total Resources: {len(fhir_bundle['entry'])}")
    print("\nResources:")
    for entry in fhir_bundle['entry']:
        resource_type = entry['resource']['resourceType']
        print(f"  - {resource_type}")

    # Pretty print full bundle
    print("\n=== Complete FHIR Bundle (JSON) ===")
    print(json.dumps(fhir_bundle, indent=2))
