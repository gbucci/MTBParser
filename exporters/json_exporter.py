#!/usr/bin/env python3
"""
JSON Exporter - Export MTB reports and mappings to JSON format
"""

import json
from pathlib import Path
from typing import Dict, Optional, Union

# Handle imports
try:
    from core.data_models import MTBReport
except ModuleNotFoundError:
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent))
    from core.data_models import MTBReport


class JSONExporter:
    """
    Export MTB Report and standard mappings to JSON
    """

    def __init__(self, pretty: bool = True, include_raw: bool = False):
        """
        Initialize JSON Exporter

        Args:
            pretty: Pretty-print JSON with indentation
            include_raw: Include raw report text in export
        """
        self.pretty = pretty
        self.include_raw = include_raw

    def export_report(self, report: MTBReport) -> str:
        """
        Export MTB Report to JSON string

        Args:
            report: Parsed MTB Report

        Returns:
            JSON string
        """
        report_dict = report.to_dict()

        if not self.include_raw:
            report_dict.pop('raw_content', None)

        indent = 2 if self.pretty else None
        return json.dumps(report_dict, indent=indent, ensure_ascii=False)

    def export_fhir(self, fhir_bundle: Dict) -> str:
        """
        Export FHIR Bundle to JSON string

        Args:
            fhir_bundle: FHIR Bundle dictionary

        Returns:
            JSON string
        """
        indent = 2 if self.pretty else None
        return json.dumps(fhir_bundle, indent=indent, ensure_ascii=False)

    def export_phenopacket(self, phenopacket: Dict) -> str:
        """
        Export Phenopacket to JSON string

        Args:
            phenopacket: Phenopacket dictionary

        Returns:
            JSON string
        """
        indent = 2 if self.pretty else None
        return json.dumps(phenopacket, indent=indent, ensure_ascii=False)

    def export_omop(self, omop_tables: Dict) -> str:
        """
        Export OMOP tables to JSON string

        Args:
            omop_tables: OMOP tables dictionary

        Returns:
            JSON string
        """
        indent = 2 if self.pretty else None
        return json.dumps(omop_tables, indent=indent, ensure_ascii=False)

    def save_to_file(self, data: Union[str, Dict], filepath: Union[str, Path]):
        """
        Save JSON to file

        Args:
            data: JSON string or dictionary
            filepath: Output file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, dict):
            indent = 2 if self.pretty else None
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data)

    def export_complete_package(
        self,
        report: MTBReport,
        fhir_bundle: Optional[Dict] = None,
        phenopacket: Optional[Dict] = None,
        omop_tables: Optional[Dict] = None
    ) -> Dict:
        """
        Export complete package with all formats

        Args:
            report: MTB Report
            fhir_bundle: FHIR Bundle (optional)
            phenopacket: Phenopacket (optional)
            omop_tables: OMOP tables (optional)

        Returns:
            Complete package dictionary
        """
        package = {
            'mtb_report': report.to_dict(),
            'metadata': {
                'patient_id': report.patient.id,
                'report_date': report.report_date,
                'parser_version': '1.0.0'
            }
        }

        if not self.include_raw:
            package['mtb_report'].pop('raw_content', None)

        if fhir_bundle:
            package['fhir_r4'] = fhir_bundle

        if phenopacket:
            package['ga4gh_phenopacket_v2'] = phenopacket

        if omop_tables:
            package['omop_cdm_v5_4'] = omop_tables

        return package


# Example usage
if __name__ == "__main__":
    print("=== JSON Exporter Test ===\n")

    from core.mtb_parser import MTBParser
    from mappers.fhir_mapper import FHIRMapper
    from mappers.phenopackets_mapper import PhenopacketsMapper
    from mappers.omop_mapper import OMOPMapper

    # Sample report
    sample_text = """
    Paziente: 12345
    Età: 65 anni
    Sesso: M

    Diagnosi: Adenocarcinoma polmonare stadio IV
    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    TMB: 8.5 mut/Mb
    """

    # Parse
    parser = MTBParser()
    report = parser.parse_report(sample_text)

    # Create mappers
    fhir_mapper = FHIRMapper()
    pheno_mapper = PhenopacketsMapper()
    omop_mapper = OMOPMapper()

    # Generate mappings
    fhir_bundle = fhir_mapper.create_fhir_bundle(report)
    phenopacket = pheno_mapper.create_phenopacket(report)
    omop_tables = omop_mapper.create_omop_tables(report)

    # Export
    exporter = JSONExporter(pretty=True, include_raw=False)

    # 1. Export individual formats
    print("1. MTB Report JSON (first 500 chars):")
    report_json = exporter.export_report(report)
    print(report_json[:500] + "...\n")

    # 2. Export complete package
    print("2. Creating complete package...")
    package = exporter.export_complete_package(
        report=report,
        fhir_bundle=fhir_bundle,
        phenopacket=phenopacket,
        omop_tables=omop_tables
    )

    print(f"Package contains:")
    for key in package.keys():
        print(f"  - {key}")

    # 3. Save to file
    output_file = Path("/tmp/mtb_report_package.json")
    exporter.save_to_file(package, output_file)
    print(f"\n3. Saved complete package to: {output_file}")
    print(f"   File size: {output_file.stat().st_size} bytes")
