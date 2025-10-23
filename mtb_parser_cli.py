#!/usr/bin/env python3
"""
MTB Parser CLI - Command-line interface for MTB report parsing
Supports interactive editing mode and multi-format export
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List

# Handle imports
try:
    from core.mtb_parser import MTBParser
    from core.report_validator import ReportValidator
    from interactive.interactive_editor import SimpleInteractiveEditor
    from exporters.unified_exporter import UnifiedExporter, ExportFormat
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    from core.mtb_parser import MTBParser
    from core.report_validator import ReportValidator
    from interactive.interactive_editor import SimpleInteractiveEditor
    from exporters.unified_exporter import UnifiedExporter, ExportFormat


class MTBParserCLI:
    """
    Command-line interface for MTB Parser

    Features:
    - Parse MTB reports from text files
    - Automatic validation with interactive editing mode
    - Export to multiple interoperable formats (FHIR, Phenopackets, OMOP)
    - Batch processing support
    """

    def __init__(self):
        self.parser = MTBParser()
        self.validator = ReportValidator()

    def parse_file(
        self,
        input_file: Path,
        interactive: bool = False,
        auto_interactive: bool = True,
        export_formats: Optional[List[ExportFormat]] = None,
        output_dir: Optional[Path] = None
    ) -> bool:
        """
        Parse a single MTB report file

        Args:
            input_file: Path to input text file
            interactive: Force interactive mode
            auto_interactive: Automatically trigger interactive mode for invalid reports
            export_formats: List of export formats
            output_dir: Output directory for exports

        Returns:
            Success status
        """
        try:
            # Read file
            print(f"\n📄 Reading: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                text_content = f.read()

            # Parse report
            print("🔍 Parsing report...")
            report = self.parser.parse_report(text_content)

            # Show parsing summary
            print(f"\n✓ Parsing complete!")
            print(f"  - Patient ID: {report.patient.id or 'N/A'}")
            print(f"  - Diagnosis: {report.diagnosis.primary_diagnosis or 'N/A'}")
            print(f"  - Variants found: {len(report.variants)}")
            print(f"  - Recommendations: {len(report.recommendations)}")

            # Validate report
            print("\n🔎 Validating report...")
            is_valid, issues = self.validator.validate(report)

            if not is_valid or issues:
                print("\n" + self.validator.format_validation_report())

                # Trigger interactive mode if needed
                if (auto_interactive and self.validator.needs_interactive_mode()) or interactive:
                    print("\n" + "="*70)
                    print("⚡ Interactive editing mode activated")
                    print("="*70)

                    editor = SimpleInteractiveEditor(report, issues)
                    report = editor.start()

                    # Re-validate
                    print("\n🔎 Re-validating after edits...")
                    is_valid, issues = self.validator.validate(report)
                    print(self.validator.format_validation_report())
            else:
                print("✓ Validation passed - no issues found")

            # Show quality metrics
            if report.quality_metrics:
                qm = report.quality_metrics
                print(f"\n📊 Quality Metrics:")
                print(f"  - Completeness: {qm.completeness_pct}%")
                print(f"  - Variants with VAF: {qm.variants_with_vaf}/{qm.variants_found}")
                print(f"  - Variants classified: {qm.variants_classified}/{qm.variants_found}")
                print(f"  - Drugs mapped: {qm.drugs_mapped}/{qm.drugs_identified}")

            # Export if requested
            if export_formats:
                print(f"\n📤 Exporting to {len(export_formats)} format(s)...")
                exporter = UnifiedExporter(
                    output_dir=output_dir or Path.cwd() / "mtb_exports",
                    pretty=True
                )
                exporter.export(report, formats=export_formats, save_to_file=True)

            return True

        except FileNotFoundError:
            print(f"❌ Error: File not found: {input_file}")
            return False
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            import traceback
            traceback.print_exc()
            return False

    def parse_batch(
        self,
        input_dir: Path,
        pattern: str = "*.txt",
        interactive: bool = False,
        export_formats: Optional[List[ExportFormat]] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Parse multiple MTB reports in batch

        Args:
            input_dir: Directory containing input files
            pattern: File pattern (e.g., "*.txt")
            interactive: Enable interactive mode for all files
            export_formats: Export formats
            output_dir: Output directory
        """
        print(f"\n{'='*70}")
        print(f"  BATCH PROCESSING")
        print(f"{'='*70}")
        print(f"Input directory: {input_dir}")
        print(f"Pattern: {pattern}\n")

        # Find all matching files
        files = list(input_dir.glob(pattern))

        if not files:
            print(f"⚠️  No files found matching pattern: {pattern}")
            return

        print(f"Found {len(files)} file(s) to process\n")

        # Process each file
        success_count = 0
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] " + "="*60)
            success = self.parse_file(
                file_path,
                interactive=interactive,
                auto_interactive=True,
                export_formats=export_formats,
                output_dir=output_dir
            )
            if success:
                success_count += 1

        # Summary
        print(f"\n{'='*70}")
        print(f"BATCH SUMMARY")
        print(f"{'='*70}")
        print(f"Total files: {len(files)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(files) - success_count}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="MTB Report Parser - Parse and export molecular tumor board reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse single file with interactive mode
  python mtb_parser_cli.py input.txt -i

  # Parse and export to all formats
  python mtb_parser_cli.py input.txt -e all -o ./exports

  # Parse and export to specific formats
  python mtb_parser_cli.py input.txt -e fhir phenopackets

  # Batch process directory
  python mtb_parser_cli.py --batch ./reports/ -e all

  # Force interactive mode for batch
  python mtb_parser_cli.py --batch ./reports/ -i

Supported export formats:
  - fhir          : FHIR R4 Bundle
  - phenopackets  : GA4GH Phenopackets v2
  - omop          : OMOP CDM v5.4
  - json          : Native JSON format
  - csv           : CSV exports
  - all           : All formats
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'input_file',
        nargs='?',
        type=Path,
        help='Input MTB report file (text format)'
    )
    input_group.add_argument(
        '--batch',
        type=Path,
        metavar='DIR',
        help='Batch process all files in directory'
    )

    # Interactive mode
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Force interactive editing mode for all reports'
    )

    parser.add_argument(
        '--no-auto-interactive',
        action='store_true',
        help='Disable automatic interactive mode for invalid reports'
    )

    # Export options
    parser.add_argument(
        '-e', '--export',
        nargs='+',
        choices=['fhir', 'phenopackets', 'omop', 'json', 'csv', 'all'],
        metavar='FORMAT',
        help='Export formats (space-separated)'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        metavar='DIR',
        help='Output directory for exports (default: ./mtb_exports)'
    )

    # Batch options
    parser.add_argument(
        '--pattern',
        default='*.txt',
        help='File pattern for batch processing (default: *.txt)'
    )

    # Other options
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )

    args = parser.parse_args()

    # Parse export formats
    export_formats = None
    if args.export:
        format_map = {
            'fhir': ExportFormat.FHIR_R4,
            'phenopackets': ExportFormat.PHENOPACKETS_V2,
            'omop': ExportFormat.OMOP_CDM_V5_4,
            'json': ExportFormat.JSON,
            'csv': ExportFormat.CSV,
            'all': ExportFormat.ALL
        }
        export_formats = [format_map[f] for f in args.export]

    # Create CLI instance
    cli = MTBParserCLI()

    # Execute
    if args.batch:
        # Batch mode
        if not args.batch.is_dir():
            print(f"❌ Error: Not a directory: {args.batch}")
            sys.exit(1)

        cli.parse_batch(
            input_dir=args.batch,
            pattern=args.pattern,
            interactive=args.interactive,
            export_formats=export_formats,
            output_dir=args.output
        )
    else:
        # Single file mode
        if not args.input_file.exists():
            print(f"❌ Error: File not found: {args.input_file}")
            sys.exit(1)

        success = cli.parse_file(
            input_file=args.input_file,
            interactive=args.interactive,
            auto_interactive=not args.no_auto_interactive,
            export_formats=export_formats,
            output_dir=args.output
        )

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
