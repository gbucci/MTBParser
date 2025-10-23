# MTBParser - Quick Reference Guide

## 🚀 Quick Start (5 minuti)

### 1. Installazione

```bash
cd MTBParser
pip install -r requirements.txt  # Se necessario
```

### 2. Parse il tuo primo report

```bash
# Parse e visualizza risultati
python mtb_parser_cli.py examples/sample_report.txt

# Parse ed export in tutti i formati
python mtb_parser_cli.py examples/sample_report.txt -e all -o ./my_exports
```

### 3. Check gli export

```bash
ls ./my_exports/patient_12345/
# Output:
#   fhir_r4_bundle.json
#   ga4gh_phenopacket_v2.json
#   omop_cdm_v5_4.json
#   mtb_report.json
#   csv/
```

---

## 📋 Comandi Essenziali

### Parse Singolo File

```bash
# Solo parse e validazione
python mtb_parser_cli.py report.txt

# Con export FHIR
python mtb_parser_cli.py report.txt -e fhir

# Con export completo
python mtb_parser_cli.py report.txt -e all
```

### Modalità Interattiva

```bash
# Auto-attivazione (se ci sono errori critici)
python mtb_parser_cli.py report.txt -e all

# Forza modalità interattiva
python mtb_parser_cli.py report.txt -i -e all
```

### Batch Processing

```bash
# Processa tutti i .txt in una directory
python mtb_parser_cli.py --batch ./reports/ -e all

# Con pattern personalizzato
python mtb_parser_cli.py --batch ./data/ --pattern "*.mtb" -e all
```

---

## 🎯 Use Cases Comuni

### UC1: Integrazione EHR (Solo FHIR)

```bash
python mtb_parser_cli.py report.txt -e fhir -o ./ehr_integration
```

Output: `./ehr_integration/patient_XXX/fhir_r4_bundle.json`

### UC2: Ricerca Genomica (Phenopackets)

```bash
python mtb_parser_cli.py report.txt -e phenopackets -o ./research
```

Output: `./research/patient_XXX/ga4gh_phenopacket_v2.json`

### UC3: Analisi Dati (CSV)

```bash
python mtb_parser_cli.py report.txt -e csv -o ./analysis
```

Output: `./analysis/patient_XXX/csv/` con 3 file CSV

### UC4: Package Completo

```python
from exporters.unified_exporter import UnifiedExporter

exporter = UnifiedExporter()
package_dir = exporter.export_complete_package(report)
# Crea package con tutti i formati + README
```

---

## 🔍 Validazione - Quick Guide

### Campi Critici (Trigger Interactive Mode)

Se mancano questi campi, la modalità interattiva si attiva automaticamente:

- ⚠️ **Patient ID** - ID paziente mancante
- ⚠️ **Diagnosi** - Nessuna diagnosi trovata
- ⚠️ **Varianti** - Nessuna variante genomica trovata

### Come Gestire gli Errori

**Scenario 1: Report incompleto**
```bash
python mtb_parser_cli.py incomplete_report.txt
# Output: Validation errors → Interactive mode auto-attivato
```

**Scenario 2: Ignora errori (batch)**
```bash
python mtb_parser_cli.py --batch ./reports/ --no-auto-interactive -e json
# Parse tutti i report, salta interactive mode
```

**Scenario 3: Fix manuale**
```bash
# 1. Parse e vedi errori
python mtb_parser_cli.py report.txt

# 2. Correggi il file sorgente
vim report.txt

# 3. Re-parse
python mtb_parser_cli.py report.txt -e all
```

---

## 📊 Formati Export - Quando Usarli?

| Formato | Quando Usarlo | Output |
|---------|---------------|--------|
| **FHIR R4** | Integrazione EHR, interoperabilità clinica | Bundle FHIR transazionale |
| **Phenopackets** | Ricerca genomica, database internazionali | GA4GH Phenopacket v2 JSON |
| **OMOP CDM** | Ricerca osservazionale, real-world evidence | Tabelle OMOP v5.4 |
| **JSON** | Workflow interno, debugging | MTBParser native JSON |
| **CSV** | Analisi Excel/R/Python, reporting | 3 file CSV (patient, variants, drugs) |

### Export Multipli

```bash
# Solo formati standard
python mtb_parser_cli.py report.txt -e fhir phenopackets omop

# Standard + analisi
python mtb_parser_cli.py report.txt -e fhir csv

# Tutto
python mtb_parser_cli.py report.txt -e all
```

---

## 🐍 Python API - Quick Reference

### Workflow Base

```python
from core.mtb_parser import MTBParser
from exporters.unified_exporter import UnifiedExporter, ExportFormat

# Parse
parser = MTBParser()
with open('report.txt') as f:
    report = parser.parse_report(f.read())

# Export
exporter = UnifiedExporter(output_dir="./exports")
exporter.export(report, formats=[ExportFormat.FHIR_R4], save_to_file=True)
```

### Con Validazione

```python
from core.report_validator import ReportValidator

validator = ReportValidator()
is_valid, issues = validator.validate(report)

if not is_valid:
    print(validator.format_validation_report())
```

### Con Interactive Mode

```python
from interactive.interactive_editor import SimpleInteractiveEditor

if validator.needs_interactive_mode():
    editor = SimpleInteractiveEditor(report, issues)
    report = editor.start()
```

### Export Programmatico

```python
from exporters.unified_exporter import UnifiedExporter, ExportFormat

exporter = UnifiedExporter(output_dir="./output", pretty=True)

# Solo FHIR
results = exporter.export(report, formats=[ExportFormat.FHIR_R4])
fhir_bundle = results['fhir_r4']

# Tutti i formati
results = exporter.export(report, formats=[ExportFormat.ALL])

# Package completo
package_dir = exporter.export_complete_package(report)
```

---

## 🔧 Troubleshooting Quick Fixes

### Problema: "No variants found"

**Causa**: Il parser non ha trovato varianti genomiche

**Fix**:
1. Controlla formato varianti nel testo
2. Usa modalità interattiva: `python mtb_parser_cli.py report.txt -i`
3. Aggiungi manualmente quando richiesto: es. `EGFR L858R 45%`

### Problema: "Patient ID missing"

**Causa**: ID paziente non trovato nel testo

**Fix**:
1. Aggiungi nel report: `ID Paziente: 12345`
2. Oppure usa interactive mode per inserirlo

### Problema: "Export failed"

**Causa**: Errore durante export specifico

**Fix**:
```bash
# Test formati uno alla volta
python mtb_parser_cli.py report.txt -e fhir
python mtb_parser_cli.py report.txt -e phenopackets
```

### Problema: Encoding errors (caratteri strani)

**Fix**:
```bash
export LANG=it_IT.UTF-8
python mtb_parser_cli.py report.txt
```

---

## 💡 Tips & Tricks

### Tip 1: Preview Rapido

```bash
# Solo parse e validazione (no export)
python mtb_parser_cli.py report.txt
# Vedi quality metrics e validation warnings
```

### Tip 2: Export Selettivo per Performance

```bash
# Se serve solo FHIR, non generare tutto
python mtb_parser_cli.py report.txt -e fhir  # Fast
python mtb_parser_cli.py report.txt -e all   # Slower
```

### Tip 3: Batch Processing Sicuro

```bash
# Test su singolo file prima
python mtb_parser_cli.py reports/report_001.txt -e all

# Poi batch completo
python mtb_parser_cli.py --batch ./reports/ -e all
```

### Tip 4: Directory Output Organizzata

```bash
# Organizza per progetto
python mtb_parser_cli.py report.txt -e all -o ./project_A/exports

# Organizza per data
python mtb_parser_cli.py report.txt -e all -o ./exports/$(date +%Y%m%d)
```

### Tip 5: Log Processing

```bash
# Salva output per review
python mtb_parser_cli.py --batch ./reports/ -e all 2>&1 | tee processing.log

# Grep errori
grep "Error" processing.log
grep "CRITICAL" processing.log
```

---

## 📖 Risorse Aggiuntive

### Documentazione Completa

- **README_INTERACTIVE.md** - Guida utente dettagliata
- **IMPLEMENTATION_SUMMARY.md** - Dettagli tecnici implementazione
- **CLAUDE.md** - Developer guide

### File di Test

- `examples/sample_report.txt` - Report di esempio
- `examples/test_interactive_mode.py` - Test suite

### Help Online

```bash
# Help comando
python mtb_parser_cli.py --help

# Test rapido
python examples/test_interactive_mode.py
```

---

## 🎓 Tutorial Step-by-Step

### Tutorial 1: Il Tuo Primo Export

```bash
# 1. Copia il file di esempio
cp examples/sample_report.txt my_report.txt

# 2. (Opzionale) Modifica con i tuoi dati
vim my_report.txt

# 3. Parse ed export
python mtb_parser_cli.py my_report.txt -e all -o ./my_first_export

# 4. Check risultati
ls -la my_first_export/patient_*/
```

### Tutorial 2: Batch Processing

```bash
# 1. Crea directory con report
mkdir test_batch
cp examples/sample_report.txt test_batch/report_001.txt
cp examples/sample_report.txt test_batch/report_002.txt

# 2. Modifica report (es: cambia patient ID)
# ...

# 3. Batch process
python mtb_parser_cli.py --batch test_batch/ -e all -o ./batch_results

# 4. Check
ls batch_results/
```

### Tutorial 3: Integrazione in Script Python

```python
#!/usr/bin/env python3
"""
Script di esempio per integrazione MTBParser
"""
import sys
from pathlib import Path
from core.mtb_parser import MTBParser
from exporters.unified_exporter import UnifiedExporter, ExportFormat

def process_mtb_report(input_file, output_dir):
    """Processa report MTB e esporta in FHIR"""

    # Parse
    parser = MTBParser()
    with open(input_file) as f:
        report = parser.parse_report(f.read())

    # Export
    exporter = UnifiedExporter(output_dir=output_dir)
    results = exporter.export(
        report,
        formats=[ExportFormat.FHIR_R4],
        save_to_file=True
    )

    print(f"✓ Processed {input_file}")
    print(f"✓ FHIR exported to {output_dir}")
    return results

if __name__ == "__main__":
    process_mtb_report(
        input_file="examples/sample_report.txt",
        output_dir="./my_exports"
    )
```

---

## 📞 Support

Per problemi o domande:

1. Check documentazione: `README_INTERACTIVE.md`
2. Run test suite: `python examples/test_interactive_mode.py`
3. Check logs: Vedi output dettagliato con validation errors
4. File issue: [Link al repository se applicabile]

---

**Version**: 1.0.0
**Last Updated**: 23 Ottobre 2025
