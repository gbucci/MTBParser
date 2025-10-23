#!/usr/bin/env python3
"""
Unified Exporter - Single interface for all export formats
Supports: FHIR R4, GA4GH Phenopackets v2, OMOP CDM v5.4, JSON, CSV
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from enum import Enum

# Handle imports
try:
    from core.data_models import MTBReport
    from mappers.fhir_mapper import FHIRMapper
    from mappers.phenopackets_mapper import PhenopacketsMapper
    from mappers.omop_mapper import OMOPMapper
    from exporters.json_exporter import JSONExporter
    from exporters.csv_exporter import CSVExporter
except ModuleNotFoundError:
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent))
    from core.data_models import MTBReport
    from mappers.fhir_mapper import FHIRMapper
    from mappers.phenopackets_mapper import PhenopacketsMapper
    from mappers.omop_mapper import OMOPMapper
    from exporters.json_exporter import JSONExporter
    from exporters.csv_exporter import CSVExporter


class ExportFormat(Enum):
    """Supported export formats"""
    FHIR_R4 = "fhir_r4"
    PHENOPACKETS_V2 = "phenopackets_v2"
    OMOP_CDM_V5_4 = "omop_cdm_v5_4"
    JSON = "json"
    CSV = "csv"
    ALL = "all"


class UnifiedExporter:
    """
    Unified interface for exporting MTB reports to multiple interoperable formats

    Usage:
        exporter = UnifiedExporter()
        exporter.export(report, formats=[ExportFormat.FHIR_R4, ExportFormat.PHENOPACKETS_V2])
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None, pretty: bool = True):
        """
        Initialize Unified Exporter

        Args:
            output_dir: Base output directory for file exports
            pretty: Pretty-print JSON outputs
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "mtb_exports"
        self.pretty = pretty

        # Initialize mappers
        self.fhir_mapper = FHIRMapper()
        self.phenopackets_mapper = PhenopacketsMapper()
        self.omop_mapper = OMOPMapper()
        self.json_exporter = JSONExporter(pretty=pretty, include_raw=False)
        self.csv_exporter = CSVExporter(delimiter=',')

    def export(
        self,
        report: MTBReport,
        formats: Optional[List[ExportFormat]] = None,
        save_to_file: bool = True
    ) -> Dict[str, Union[Dict, str]]:
        """
        Export MTB report to specified formats

        Args:
            report: Parsed MTB Report
            formats: List of export formats (default: all formats)
            save_to_file: Save outputs to files

        Returns:
            Dictionary with format names as keys and exported data as values
        """
        if formats is None or ExportFormat.ALL in formats:
            formats = [
                ExportFormat.FHIR_R4,
                ExportFormat.PHENOPACKETS_V2,
                ExportFormat.OMOP_CDM_V5_4,
                ExportFormat.JSON,
                ExportFormat.CSV
            ]

        results = {}

        # Create patient-specific output directory
        patient_id = report.patient.id or "unknown"
        patient_dir = self.output_dir / f"patient_{patient_id}"

        if save_to_file:
            patient_dir.mkdir(parents=True, exist_ok=True)

        # Export FHIR R4
        if ExportFormat.FHIR_R4 in formats:
            fhir_bundle = self.fhir_mapper.create_fhir_bundle(report)
            results['fhir_r4'] = fhir_bundle

            if save_to_file:
                fhir_path = patient_dir / "fhir_r4_bundle.json"
                self.json_exporter.save_to_file(fhir_bundle, fhir_path)
                print(f"✓ FHIR R4 Bundle saved to: {fhir_path}")

        # Export Phenopackets v2
        if ExportFormat.PHENOPACKETS_V2 in formats:
            phenopacket = self.phenopackets_mapper.create_phenopacket(report)
            results['phenopackets_v2'] = phenopacket

            if save_to_file:
                pheno_path = patient_dir / "ga4gh_phenopacket_v2.json"
                self.json_exporter.save_to_file(phenopacket, pheno_path)
                print(f"✓ GA4GH Phenopacket v2 saved to: {pheno_path}")

        # Export OMOP CDM v5.4
        if ExportFormat.OMOP_CDM_V5_4 in formats:
            omop_tables = self.omop_mapper.create_omop_tables(report)
            results['omop_cdm_v5_4'] = omop_tables

            if save_to_file:
                omop_path = patient_dir / "omop_cdm_v5_4.json"
                self.json_exporter.save_to_file(omop_tables, omop_path)
                print(f"✓ OMOP CDM v5.4 tables saved to: {omop_path}")

        # Export JSON (native format)
        if ExportFormat.JSON in formats:
            json_str = self.json_exporter.export_report(report)
            results['json'] = json_str

            if save_to_file:
                json_path = patient_dir / "mtb_report.json"
                self.json_exporter.save_to_file(json_str, json_path)
                print(f"✓ MTB Report JSON saved to: {json_path}")

        # Export CSV
        if ExportFormat.CSV in formats:
            if save_to_file:
                csv_dir = patient_dir / "csv"
                self.csv_exporter.save_complete_export(report, csv_dir)
                print(f"✓ CSV exports saved to: {csv_dir}/")

            # Return CSV data as structured format
            results['csv'] = {
                'patient_summary': self.csv_exporter.export_patient_summary(report),
                'variants': self.csv_exporter.export_variants_to_rows(report),
                'recommendations': self.csv_exporter.export_recommendations_to_rows(report)
            }

        return results

    def export_batch(
        self,
        reports: List[MTBReport],
        formats: Optional[List[ExportFormat]] = None
    ) -> List[Dict]:
        """
        Export multiple reports in batch

        Args:
            reports: List of MTB Reports
            formats: Export formats

        Returns:
            List of export results
        """
        results = []

        print(f"\n=== Batch Export: {len(reports)} reports ===\n")

        for i, report in enumerate(reports, 1):
            patient_id = report.patient.id or f"unknown_{i}"
            print(f"[{i}/{len(reports)}] Exporting patient {patient_id}...")

            result = self.export(report, formats=formats, save_to_file=True)
            results.append(result)
            print()

        print(f"✓ Batch export complete: {len(reports)} reports processed")
        return results

    def export_complete_package(
        self,
        report: MTBReport,
        package_name: Optional[str] = None
    ) -> Path:
        """
        Export complete interoperable package with all formats

        Args:
            report: MTB Report
            package_name: Custom package name

        Returns:
            Path to package directory
        """
        patient_id = report.patient.id or "unknown"
        package_name = package_name or f"mtb_package_{patient_id}"
        package_dir = self.output_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=== Creating Complete Interoperable Package ===")
        print(f"Package: {package_name}\n")

        # Export all formats
        self.export(report, formats=[ExportFormat.ALL], save_to_file=True)

        # Create package metadata
        metadata = {
            'package_name': package_name,
            'patient_id': patient_id,
            'formats_included': [
                'FHIR R4',
                'GA4GH Phenopackets v2',
                'OMOP CDM v5.4',
                'JSON',
                'CSV'
            ],
            'quality_metrics': report.quality_metrics.to_dict() if report.quality_metrics else None,
            'parser_version': '1.0.0'
        }

        metadata_path = package_dir / "package_metadata.json"
        self.json_exporter.save_to_file(metadata, metadata_path)
        print(f"✓ Package metadata saved to: {metadata_path}")

        # Create README
        readme_content = self._create_package_readme(report, metadata)
        readme_path = package_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✓ README created: {readme_path}")

        print(f"\n✓ Complete package created at: {package_dir}")
        return package_dir

    def _create_package_readme(self, report: MTBReport, metadata: Dict) -> str:
        """Generate README for export package"""
        patient_id = report.patient.id or "unknown"

        readme = f"""# MTB Report Interoperable Export Package

## Patient Information
- **Patient ID**: {patient_id}
- **Report Date**: {report.report_date or 'N/A'}
- **Parser Version**: {metadata['parser_version']}

## Contents

This package contains the MTB report exported to multiple interoperable formats:

### 1. FHIR R4 (`fhir_r4_bundle.json`)
HL7 FHIR R4 Bundle following the Genomics Reporting Implementation Guide.
- Standard: HL7 FHIR R4
- Use case: Clinical data exchange, EHR integration
- Specification: https://hl7.org/fhir/R4/

### 2. GA4GH Phenopackets v2 (`ga4gh_phenopacket_v2.json`)
GA4GH Phenopacket following v2.0 specification.
- Standard: GA4GH Phenopacket Schema v2
- Use case: Research, genomic databases, federated queries
- Specification: https://phenopacket-schema.readthedocs.io/

### 3. OMOP CDM v5.4 (`omop_cdm_v5_4.json`)
OMOP Common Data Model tables for observational research.
- Standard: OMOP CDM v5.4
- Use case: Observational research, real-world evidence
- Specification: https://ohdsi.github.io/CommonDataModel/

### 4. Native JSON (`mtb_report.json`)
MTBParser native JSON format with all extracted data.
- Format: Custom MTBParser JSON schema
- Use case: Parser-specific workflows, debugging

### 5. CSV Exports (`csv/`)
Tabular exports for easy analysis in spreadsheet tools.
- Files: `patient_summary.csv`, `variants.csv`, `recommendations.csv`
- Use case: Data analysis, Excel/R/Python workflows

## Quality Metrics

"""
        if report.quality_metrics:
            qm = report.quality_metrics
            readme += f"""- **Completeness**: {qm.completeness_pct}%
- **Variants Found**: {qm.variants_found}
- **Actionable Variants**: {len(report.get_actionable_variants())}
- **Drugs Identified**: {qm.drugs_identified}
- **Drugs Mapped**: {qm.drugs_mapped}
"""
            if qm.warnings:
                readme += "\n### Warnings\n"
                for warning in qm.warnings:
                    readme += f"- {warning}\n"

        readme += f"""
## Usage

### FHIR R4
```bash
# Validate FHIR bundle
curl -X POST https://hapi.fhir.org/baseR4/$validate \\
  -H "Content-Type: application/json" \\
  -d @fhir_r4_bundle.json
```

### Phenopackets
```python
import json
with open('ga4gh_phenopacket_v2.json') as f:
    phenopacket = json.load(f)
```

### OMOP CDM
```sql
-- Load into OMOP database
COPY person FROM 'omop_cdm_v5_4.json' ...
```

---
Generated by MTBParser v{metadata['parser_version']}
"""
        return readme


# Example usage
if __name__ == "__main__":
    print("=== Unified Exporter Test ===\n")

    from core.mtb_parser import MTBParser

    # Sample report
    sample_text = """
    Paziente: 12345
    Età: 65 anni
    Sesso: M
    Data di nascita: 15/03/1958

    Diagnosi: Adenocarcinoma polmonare stadio IV

    Varianti genomiche:
    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    TP53 c.733G>A p.Gly245Ser Pathogenic 52%

    TMB: 8.5 mut/Mb

    Raccomandazioni:
    Sensibilità a osimertinib per mutazione EGFR L858R
    """

    # Parse
    parser = MTBParser()
    report = parser.parse_report(sample_text)

    # Initialize exporter
    exporter = UnifiedExporter(output_dir="/tmp/mtb_exports", pretty=True)

    # Test 1: Export to specific formats
    print("Test 1: Export to FHIR and Phenopackets")
    results = exporter.export(
        report,
        formats=[ExportFormat.FHIR_R4, ExportFormat.PHENOPACKETS_V2],
        save_to_file=True
    )
    print(f"Exported formats: {list(results.keys())}\n")

    # Test 2: Export complete package
    print("\nTest 2: Export complete interoperable package")
    package_dir = exporter.export_complete_package(report)

    # List files
    print("\nPackage contents:")
    for file in sorted(package_dir.rglob('*')):
        if file.is_file():
            print(f"  {file.relative_to(package_dir)}")
