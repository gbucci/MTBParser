#!/usr/bin/env python3
"""
OMOP CDM v5.4 Mapper - Converts MTB Report to OMOP Common Data Model
For observational research and real-world evidence generation
"""

import json
from datetime import datetime, date
from typing import Dict, List, Optional
import hashlib

# Handle imports for both module and script execution
try:
    from core.data_models import MTBReport, Variant, Patient, Diagnosis, TherapeuticRecommendation
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.data_models import MTBReport, Variant, Patient, Diagnosis, TherapeuticRecommendation


class OMOPMapper:
    """
    Maps MTB Report to OMOP CDM v5.4 tables

    OMOP CDM: Observational Medical Outcomes Partnership Common Data Model
    Specification: https://ohdsi.github.io/CommonDataModel/cdm54.html

    Key tables:
    - person: Patient demographics
    - condition_occurrence: Diagnosis
    - measurement: Genomic variants, TMB
    - drug_exposure: Therapeutic recommendations
    - observation: Other clinical data
    - specimen: Tumor sample information
    """

    # OMOP Concept IDs (these should ideally come from OMOP vocabulary)
    # Using placeholder IDs - in production, map to actual OMOP concepts
    CONCEPT_IDS = {
        'gender_male': 8507,
        'gender_female': 8532,
        'race_unknown': 0,
        'ethnicity_unknown': 0,
        'measurement_type': 44818702,  # Lab test
        'drug_exposure_type': 38000177,  # Prescription written
        'condition_type': 32020,  # EHR diagnosis
        'specimen_type': 581378,  # Specimen
        'genomic_variant': 4000000,  # Custom concept
        'tmb': 4000001,  # Custom concept
        'vaf': 4000002,  # Custom concept
    }

    def __init__(self):
        """Initialize OMOP Mapper"""
        self.visit_occurrence_id = 1  # Simplified - should be from actual visit
        self.provider_id = 1  # Simplified - should be from actual provider

    def create_omop_tables(self, report: MTBReport) -> Dict[str, List[Dict]]:
        """
        Create OMOP CDM tables from MTB Report

        Args:
            report: Parsed MTB Report

        Returns:
            Dictionary with table names as keys and list of records as values
        """
        omop_data = {
            'person': [],
            'condition_occurrence': [],
            'measurement': [],
            'drug_exposure': [],
            'observation': [],
            'specimen': []
        }

        # Generate person_id from patient ID
        person_id = self._generate_person_id(report.patient.id)

        # 1. Person table
        if report.patient:
            omop_data['person'].append(
                self._create_person_record(report.patient, person_id)
            )

        # 2. Condition occurrence (diagnosis)
        if report.diagnosis.primary_diagnosis:
            omop_data['condition_occurrence'].append(
                self._create_condition_record(report.diagnosis, person_id)
            )

        # 3. Specimen (tumor sample)
        specimen_id = self._generate_specimen_id(person_id)
        omop_data['specimen'].append(
            self._create_specimen_record(person_id, specimen_id, report.ngs_method)
        )

        # 4. Measurement records for variants
        measurement_id = 1
        for variant in report.variants:
            # Variant as measurement
            omop_data['measurement'].append(
                self._create_variant_measurement(
                    variant, person_id, specimen_id, measurement_id
                )
            )
            measurement_id += 1

            # VAF as separate measurement if available
            if variant.vaf is not None:
                omop_data['measurement'].append(
                    self._create_vaf_measurement(
                        variant, person_id, specimen_id, measurement_id
                    )
                )
                measurement_id += 1

        # 5. TMB measurement
        if report.tmb is not None:
            omop_data['measurement'].append(
                self._create_tmb_measurement(
                    report.tmb, person_id, specimen_id, measurement_id
                )
            )

        # 6. Drug exposure (recommendations)
        drug_exposure_id = 1
        for recommendation in report.recommendations:
            omop_data['drug_exposure'].append(
                self._create_drug_exposure(
                    recommendation, person_id, drug_exposure_id
                )
            )
            drug_exposure_id += 1

        return omop_data

    def _create_person_record(self, patient: Patient, person_id: int) -> Dict:
        """
        Create PERSON table record

        Schema: https://ohdsi.github.io/CommonDataModel/cdm54.html#PERSON
        """
        record = {
            'person_id': person_id,
            'gender_concept_id': self._map_gender(patient.sex),
            'year_of_birth': self._extract_year_from_date(patient.birth_date) if patient.birth_date else None,
            'month_of_birth': self._extract_month_from_date(patient.birth_date) if patient.birth_date else None,
            'day_of_birth': self._extract_day_from_date(patient.birth_date) if patient.birth_date else None,
            'race_concept_id': self.CONCEPT_IDS['race_unknown'],
            'ethnicity_concept_id': self.CONCEPT_IDS['ethnicity_unknown'],
            'person_source_value': patient.id
        }

        return {k: v for k, v in record.items() if v is not None}

    def _create_condition_record(self, diagnosis: Diagnosis, person_id: int) -> Dict:
        """
        Create CONDITION_OCCURRENCE table record

        Schema: https://ohdsi.github.io/CommonDataModel/cdm54.html#CONDITION_OCCURRENCE
        """
        record = {
            'condition_occurrence_id': 1,
            'person_id': person_id,
            'condition_concept_id': 0,  # Would map ICD-O to OMOP concept
            'condition_start_date': date.today().isoformat(),
            'condition_type_concept_id': self.CONCEPT_IDS['condition_type'],
            'condition_source_value': diagnosis.primary_diagnosis,
            'visit_occurrence_id': self.visit_occurrence_id
        }

        # Add ICD-O code if available
        if diagnosis.icd_o_code:
            record['condition_source_concept_id'] = diagnosis.icd_o_code['code']

        # Add stage as modifier
        if diagnosis.stage:
            record['condition_status_source_value'] = f"Stage {diagnosis.stage}"

        return record

    def _create_specimen_record(
        self,
        person_id: int,
        specimen_id: int,
        ngs_method: Optional[str]
    ) -> Dict:
        """
        Create SPECIMEN table record

        Schema: https://ohdsi.github.io/CommonDataModel/cdm54.html#SPECIMEN
        """
        return {
            'specimen_id': specimen_id,
            'person_id': person_id,
            'specimen_concept_id': self.CONCEPT_IDS['specimen_type'],
            'specimen_type_concept_id': self.CONCEPT_IDS['specimen_type'],
            'specimen_date': date.today().isoformat(),
            'specimen_source_value': ngs_method or 'NGS Panel'
        }

    def _create_variant_measurement(
        self,
        variant: Variant,
        person_id: int,
        specimen_id: int,
        measurement_id: int
    ) -> Dict:
        """
        Create MEASUREMENT record for genomic variant

        Schema: https://ohdsi.github.io/CommonDataModel/cdm54.html#MEASUREMENT
        """
        # Create measurement value from variant info
        value_string = f"{variant.gene}"
        if variant.protein_change:
            value_string += f" {variant.protein_change}"
        if variant.cdna_change:
            value_string += f" ({variant.cdna_change})"

        record = {
            'measurement_id': measurement_id,
            'person_id': person_id,
            'measurement_concept_id': self.CONCEPT_IDS['genomic_variant'],
            'measurement_date': date.today().isoformat(),
            'measurement_type_concept_id': self.CONCEPT_IDS['measurement_type'],
            'value_as_concept_id': self._map_classification(variant.classification),
            'value_source_value': variant.classification,
            'measurement_source_value': value_string,
            'specimen_source_id': specimen_id,
            'visit_occurrence_id': self.visit_occurrence_id
        }

        # Add gene as modifier
        if variant.gene_code:
            record['modifier_source_value'] = f"HGNC:{variant.gene_code['code']}"

        return record

    def _create_vaf_measurement(
        self,
        variant: Variant,
        person_id: int,
        specimen_id: int,
        measurement_id: int
    ) -> Dict:
        """Create MEASUREMENT record for Variant Allele Frequency"""
        return {
            'measurement_id': measurement_id,
            'person_id': person_id,
            'measurement_concept_id': self.CONCEPT_IDS['vaf'],
            'measurement_date': date.today().isoformat(),
            'measurement_type_concept_id': self.CONCEPT_IDS['measurement_type'],
            'value_as_number': variant.vaf,
            'unit_source_value': 'percent',
            'measurement_source_value': f"{variant.gene} VAF",
            'specimen_source_id': specimen_id,
            'visit_occurrence_id': self.visit_occurrence_id
        }

    def _create_tmb_measurement(
        self,
        tmb: float,
        person_id: int,
        specimen_id: int,
        measurement_id: int
    ) -> Dict:
        """Create MEASUREMENT record for Tumor Mutational Burden"""
        return {
            'measurement_id': measurement_id,
            'person_id': person_id,
            'measurement_concept_id': self.CONCEPT_IDS['tmb'],
            'measurement_date': date.today().isoformat(),
            'measurement_type_concept_id': self.CONCEPT_IDS['measurement_type'],
            'value_as_number': tmb,
            'unit_source_value': 'mut/Mb',
            'measurement_source_value': 'Tumor Mutational Burden',
            'specimen_source_id': specimen_id,
            'visit_occurrence_id': self.visit_occurrence_id
        }

    def _create_drug_exposure(
        self,
        recommendation: TherapeuticRecommendation,
        person_id: int,
        drug_exposure_id: int
    ) -> Dict:
        """
        Create DRUG_EXPOSURE record for therapeutic recommendation

        Schema: https://ohdsi.github.io/CommonDataModel/cdm54.html#DRUG_EXPOSURE
        """
        record = {
            'drug_exposure_id': drug_exposure_id,
            'person_id': person_id,
            'drug_concept_id': 0,  # Would map RxNorm to OMOP concept
            'drug_exposure_start_date': date.today().isoformat(),
            'drug_type_concept_id': self.CONCEPT_IDS['drug_exposure_type'],
            'drug_source_value': recommendation.drug,
            'visit_occurrence_id': self.visit_occurrence_id
        }

        # Add RxNorm code if available
        if recommendation.drug_code:
            record['drug_source_concept_id'] = recommendation.drug_code['code']

        # Add gene target as route (non-standard but useful)
        if recommendation.gene_target:
            record['route_source_value'] = f"Target: {recommendation.gene_target}"

        # Add evidence level
        if recommendation.evidence_level:
            record['sig_source_value'] = recommendation.evidence_level

        return record

    # Helper methods

    @staticmethod
    def _generate_person_id(patient_id: Optional[str]) -> int:
        """Generate numeric person_id from string patient_id"""
        if patient_id and patient_id.isdigit():
            return int(patient_id)
        # Hash string to get consistent numeric ID
        return int(hashlib.md5((patient_id or 'unknown').encode()).hexdigest()[:8], 16)

    @staticmethod
    def _generate_specimen_id(person_id: int) -> int:
        """Generate specimen_id"""
        return person_id * 1000 + 1  # Simple scheme

    def _map_gender(self, sex: Optional[str]) -> int:
        """Map sex to OMOP gender concept"""
        if not sex:
            return 0
        mapping = {
            'M': self.CONCEPT_IDS['gender_male'],
            'F': self.CONCEPT_IDS['gender_female']
        }
        return mapping.get(sex, 0)

    @staticmethod
    def _map_classification(classification: Optional[str]) -> int:
        """Map variant classification to concept (simplified)"""
        if not classification:
            return 0
        # These would be actual OMOP concept IDs in production
        mapping = {
            'Pathogenic': 4000010,
            'Likely Pathogenic': 4000011,
            'VUS': 4000012,
            'Likely Benign': 4000013,
            'Benign': 4000014
        }
        return mapping.get(classification, 0)

    @staticmethod
    def _extract_year_from_date(date_str: str) -> Optional[int]:
        """Extract year from ISO date string"""
        if not date_str:
            return None
        try:
            return int(date_str.split('-')[0])
        except:
            return None

    @staticmethod
    def _extract_month_from_date(date_str: str) -> Optional[int]:
        """Extract month from ISO date string"""
        if not date_str:
            return None
        try:
            return int(date_str.split('-')[1])
        except:
            return None

    @staticmethod
    def _extract_day_from_date(date_str: str) -> Optional[int]:
        """Extract day from ISO date string"""
        if not date_str:
            return None
        try:
            return int(date_str.split('-')[2])
        except:
            return None


# Example usage
if __name__ == "__main__":
    print("=== OMOP CDM v5.4 Mapper Test ===\n")

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

    # Create OMOP tables
    mapper = OMOPMapper()
    omop_tables = mapper.create_omop_tables(report)

    # Display statistics
    print("OMOP CDM Tables Generated:")
    for table_name, records in omop_tables.items():
        print(f"  {table_name}: {len(records)} records")

    # Display sample records
    print("\n=== Sample Records ===\n")

    print("PERSON table:")
    print(json.dumps(omop_tables['person'], indent=2))

    print("\nCONDITION_OCCURRENCE table:")
    print(json.dumps(omop_tables['condition_occurrence'], indent=2))

    print("\nMEASUREMENT table (first 2):")
    print(json.dumps(omop_tables['measurement'][:2], indent=2))

    print("\nDRUG_EXPOSURE table:")
    print(json.dumps(omop_tables['drug_exposure'], indent=2))

    print("\nSPECIMEN table:")
    print(json.dumps(omop_tables['specimen'], indent=2))
