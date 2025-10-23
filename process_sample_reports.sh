#!/bin/bash
###############################################################################
# MTBParser - Process Sample Reports Script
#
# This script processes all DOCX files in tests/sample_reports/ and generates:
# 1. Parsed JSON data for each patient
# 2. Individual PDF reports with ESCAT pyramids
# 3. Batch CSV summary
# 4. Batch PDF summary with statistics
#
# Usage: ./process_sample_reports.sh
###############################################################################

set -e  # Exit on error

# Configuration
INPUT_DIR="tests/sample_reports"
PARSED_DIR="batch_test_output"
STRUCTURED_DIR="batch_reports_final"
INDIVIDUAL_PDFS_DIR="sample_reports_individual_pdfs"
BATCH_OUTPUT_DIR="sample_reports_batch_output"

echo "================================================================================"
echo "MTBParser - Sample Reports Processing Pipeline"
echo "================================================================================"
echo ""

# Step 1: Parse all DOCX files
echo "📋 STEP 1: Parsing DOCX files from $INPUT_DIR"
echo "--------------------------------------------------------------------------------"

mkdir -p "$PARSED_DIR"
count=0

for docx_file in "$INPUT_DIR"/*.docx; do
    if [ -f "$docx_file" ]; then
        count=$((count + 1))
        filename=$(basename "$docx_file" .docx)

        echo "  [$count] Parsing: $filename"

        # Create patient directory
        patient_dir="$PARSED_DIR/patient_$(printf '%03d' $count)"
        mkdir -p "$patient_dir"

        # Parse with MTBParser CLI (suppress interactive mode)
        ./mtb_parser_cli.py "$docx_file" -e json -o "$patient_dir" --no-auto-interactive 2>&1 | \
            grep -E "(Patient ID|Diagnosis|Variants found|✓ MTB Report)" || true
    fi
done

echo ""
echo "✅ Parsed $count reports"
echo ""

# Step 2: Restructure for batch processing
echo "📋 STEP 2: Restructuring data for batch processing"
echo "--------------------------------------------------------------------------------"

rm -rf "$STRUCTURED_DIR"
mkdir -p "$STRUCTURED_DIR"

for outer_dir in "$PARSED_DIR"/patient_*; do
    # Find JSON files recursively
    json_file=$(find "$outer_dir" -name "mtb_report.json" -o -name "complete_package.json" | head -1)

    if [ -n "$json_file" ]; then
        # Get directory containing the JSON
        json_dir=$(dirname "$json_file")
        patient_id=$(basename "$json_dir" | sed 's/patient_//')

        # Create target directory
        target_dir="$STRUCTURED_DIR/patient_$patient_id"
        mkdir -p "$target_dir"

        # Check if it's mtb_report.json or complete_package.json
        if [[ "$json_file" == *"mtb_report.json" ]]; then
            # Wrap in complete_package format
            echo '{"mtb_report":' > "$target_dir/complete_package.json"
            cat "$json_file" >> "$target_dir/complete_package.json"
            echo '}' >> "$target_dir/complete_package.json"
            echo "  ✅ Patient $patient_id"
        else
            cp "$json_file" "$target_dir/complete_package.json"
            echo "  ✅ Patient $patient_id"
        fi
    fi
done

num_patients=$(ls -1 "$STRUCTURED_DIR" | wc -l | tr -d ' ')
echo ""
echo "✅ Structured $num_patients patient directories"
echo ""

# Step 3: Generate individual PDF reports
echo "📋 STEP 3: Generating individual PDF reports"
echo "--------------------------------------------------------------------------------"

mkdir -p "$INDIVIDUAL_PDFS_DIR"
pdf_count=0

for patient_dir in "$STRUCTURED_DIR"/patient_*; do
    if [ -d "$patient_dir" ]; then
        patient_id=$(basename "$patient_dir" | sed 's/patient_//')
        json_file="$patient_dir/complete_package.json"

        if [ -f "$json_file" ]; then
            pdf_count=$((pdf_count + 1))
            pdf_file="$INDIVIDUAL_PDFS_DIR/MTB_Report_Patient_${patient_id}.pdf"

            echo "  [$pdf_count] Patient $patient_id"
            ./generate_pdf_report.py "$json_file" "$pdf_file" 2>&1 | \
                grep -E "✅ PDF report generated" || true
        fi
    fi
done

echo ""
echo "✅ Generated $pdf_count individual PDF reports"
echo ""

# Step 4: Generate batch CSV and PDF summary
echo "📋 STEP 4: Generating batch summary (CSV + PDF)"
echo "--------------------------------------------------------------------------------"

mkdir -p "$BATCH_OUTPUT_DIR"
./batch_report_generator.py "$STRUCTURED_DIR" "$BATCH_OUTPUT_DIR"

echo ""
echo "================================================================================"
echo "✅ PROCESSING COMPLETE"
echo "================================================================================"
echo ""
echo "📁 Output Directories:"
echo "   • Parsed JSON:        $STRUCTURED_DIR/"
echo "   • Individual PDFs:    $INDIVIDUAL_PDFS_DIR/"
echo "   • Batch Reports:      $BATCH_OUTPUT_DIR/"
echo ""
echo "📊 Summary:"
echo "   • Patients processed: $num_patients"
echo "   • Individual PDFs:    $pdf_count"
echo "   • Batch CSV:          $(ls -1 $BATCH_OUTPUT_DIR/*.csv 2>/dev/null | wc -l | tr -d ' ')"
echo "   • Batch PDF:          $(ls -1 $BATCH_OUTPUT_DIR/*.pdf 2>/dev/null | wc -l | tr -d ' ')"
echo ""
echo "📄 Files Generated:"
ls -lh "$BATCH_OUTPUT_DIR"/*.{csv,pdf} 2>/dev/null || echo "   (No batch files found)"
echo ""
echo "To view batch PDF:"
echo "   open $BATCH_OUTPUT_DIR/*.pdf"
echo ""
echo "To view CSV:"
echo "   open $BATCH_OUTPUT_DIR/*.csv"
echo ""
