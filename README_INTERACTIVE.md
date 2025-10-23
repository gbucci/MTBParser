# MTB Parser - Interactive Mode & Multi-Format Export

## Nuove Funzionalità

### 1. Export Multi-Formato Unificato

Il sistema ora supporta l'export automatico in **5 formati interoperabili**:

- **FHIR R4** - HL7 FHIR Bundle per integrazione EHR
- **GA4GH Phenopackets v2** - Standard per ricerca genomica
- **OMOP CDM v5.4** - Common Data Model per ricerca osservazionale
- **JSON** - Formato nativo MTBParser
- **CSV** - Export tabulare per analisi

### 2. Modalità Interattiva

Sistema intelligente di validazione e correzione guidata:

- **Validazione automatica** dei report parsati
- **Attivazione automatica** della modalità interattiva quando mancano campi critici
- **Editor guidato** campo per campo
- **Navigazione con tastiera** (Tab, Backspace, Enter, Esc)

### 3. Validazione Intelligente

Tre livelli di severità:

- 🔴 **CRITICAL**: Campi obbligatori (trigger automatico modalità interattiva)
  - Patient ID
  - Almeno una diagnosi
  - Almeno una variante genomica

- ⚠️ **WARNING**: Campi importanti (opzionali)
  - Età paziente
  - Sesso paziente
  - VAF delle varianti
  - Classificazione varianti

- ℹ️ **INFO**: Informazioni (mapping a standard)

---

## Quick Start

### Installazione

```bash
cd MTBParser
pip install -r requirements.txt
```

### Uso Base - CLI

**Formati supportati**: `.txt` (plain text) e `.docx` (Microsoft Word)

#### 1. Parse singolo file con modalità interattiva

```bash
# File di testo
python mtb_parser_cli.py report.txt -i

# File Word (richiede python-docx)
python mtb_parser_cli.py report.docx -i
```

#### 2. Parse ed export in tutti i formati

```bash
python mtb_parser_cli.py report.txt -e all -o ./exports
python mtb_parser_cli.py report.docx -e all -o ./exports
```

#### 3. Parse ed export solo FHIR e Phenopackets

```bash
python mtb_parser_cli.py report.txt -e fhir phenopackets -o ./exports
```

#### 4. Batch processing di una directory

```bash
# Default pattern (*.txt)
python mtb_parser_cli.py --batch ./reports/ -e all

# Pattern per file .docx
python mtb_parser_cli.py --batch ./reports/ --pattern "*.docx" -e all
```

#### 5. Batch con modalità interattiva forzata

```bash
python mtb_parser_cli.py --batch ./reports/ -i -e all
```

---

## Uso Programmatico

### Esempio 1: Workflow Completo

```python
from core.mtb_parser import MTBParser
from core.report_validator import ReportValidator
from interactive.interactive_editor import SimpleInteractiveEditor
from exporters.unified_exporter import UnifiedExporter, ExportFormat

# Parse
parser = MTBParser()
report = parser.parse_report(text_content)

# Validate
validator = ReportValidator()
is_valid, issues = validator.validate(report)

# Interactive editing se necessario
if validator.needs_interactive_mode():
    editor = SimpleInteractiveEditor(report, issues)
    report = editor.start()

# Export a tutti i formati
exporter = UnifiedExporter(output_dir="./exports")
exporter.export(report, formats=[ExportFormat.ALL], save_to_file=True)
```

### Esempio 2: Export Specifico

```python
from exporters.unified_exporter import UnifiedExporter, ExportFormat

exporter = UnifiedExporter(output_dir="./my_exports", pretty=True)

# Solo FHIR e Phenopackets
results = exporter.export(
    report,
    formats=[ExportFormat.FHIR_R4, ExportFormat.PHENOPACKETS_V2],
    save_to_file=True
)
```

### Esempio 3: Package Completo

```python
from exporters.unified_exporter import UnifiedExporter

exporter = UnifiedExporter(output_dir="./packages")

# Crea package completo con tutti i formati + README + metadata
package_dir = exporter.export_complete_package(report)

# Output:
#   package_dir/
#     ├── fhir_r4_bundle.json
#     ├── ga4gh_phenopacket_v2.json
#     ├── omop_cdm_v5_4.json
#     ├── mtb_report.json
#     ├── csv/
#     │   ├── patient_summary.csv
#     │   ├── variants.csv
#     │   └── recommendations.csv
#     ├── package_metadata.json
#     └── README.md
```

---

## Architettura

```
MTBParser/
├── core/
│   ├── mtb_parser.py          # Parser principale
│   ├── report_validator.py    # Sistema di validazione (NUOVO)
│   └── data_models.py
│
├── interactive/                # Modalità interattiva (NUOVO)
│   ├── __init__.py
│   └── interactive_editor.py  # Editor campo per campo
│
├── mappers/                    # Mapper formati standard
│   ├── fhir_mapper.py         # FHIR R4
│   ├── phenopackets_mapper.py # GA4GH Phenopackets v2
│   └── omop_mapper.py         # OMOP CDM v5.4
│
├── exporters/                  # Sistema export (NUOVO)
│   ├── unified_exporter.py    # Interfaccia unificata (NUOVO)
│   ├── json_exporter.py
│   └── csv_exporter.py
│
└── mtb_parser_cli.py          # CLI principale (NUOVO)
```

---

## Modalità Interattiva - Dettagli

### Come Funziona

1. **Parsing**: Il report viene parsato normalmente
2. **Validazione**: Il sistema controlla campi critici e importanti
3. **Trigger Automatico**: Se mancano campi critici, si attiva automaticamente la modalità interattiva
4. **Editing Guidato**: L'utente viene guidato campo per campo
5. **Re-validazione**: Dopo le modifiche, il report viene ri-validato
6. **Export**: Opzionalmente si può esportare in formati standard

### Campi Critici (Trigger Automatico)

```
🔴 CRITICAL - Modalità interattiva si attiva se mancano:

1. Patient ID
   ├─ Necessario per tracking
   └─ Azione: inserire ID univoco

2. Diagnosi primaria
   ├─ Necessaria per contesto clinico
   └─ Azione: inserire diagnosi (es: "Adenocarcinoma polmonare")

3. Almeno una variante genomica
   ├─ Core del report MTB
   └─ Azione: inserire variante (es: "EGFR L858R")
```

### Esempio di Sessione Interattiva

```
==================================================================
  MTB REPORT INTERACTIVE EDITOR
==================================================================

📝 You will be guided through each field that needs attention.

Keyboard shortcuts:
  Enter       : Save value and move to next field
  Tab         : Skip to next field without changing
  Backspace   : Go to previous field (when input is empty)
  Esc         : Cancel editing current field
  Ctrl+C      : Exit editor

------------------------------------------------------------------

[Field 1/3] 🔴 Patient ID
------------------------------------------------------------------
Current value: (empty)
Help: Unique patient identifier

Enter new value: 12345
✓ Updated: Patient ID = 12345

[Field 2/3] 🔴 Primary Diagnosis
------------------------------------------------------------------
Current value: (empty)
Help: Primary cancer diagnosis (e.g., Adenocarcinoma polmonare)

Enter new value: Adenocarcinoma polmonare stadio IV
✓ Updated: Primary Diagnosis = Adenocarcinoma polmonare stadio IV

[Field 3/3] 🔴 Add Genomic Variant
------------------------------------------------------------------
Current value: (empty)
Help: Enter variant (e.g., EGFR L858R, KRAS G12D)

Enter new value: EGFR L858R 45%
✓ Updated: Add Genomic Variant = EGFR L858R 45%

==================================================================
✓ Interactive editing completed!
==================================================================

✓ Report has been modified.
```

---

## Formati Export

### FHIR R4

**Standard**: HL7 FHIR R4
**Use Case**: Integrazione EHR, scambio dati clinici
**Output**: Bundle transazionale con Patient, Condition, Observation, DiagnosticReport

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "...",
        "gender": "male"
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "code": {
          "coding": [{
            "system": "http://loinc.org",
            "code": "69548-6"
          }]
        }
      }
    }
  ]
}
```

### GA4GH Phenopackets v2

**Standard**: GA4GH Phenopacket Schema v2.0
**Use Case**: Ricerca genomica, database federati
**Output**: Phenopacket completo con interpretazioni genomiche

```json
{
  "id": "phenopacket-12345",
  "subject": {
    "id": "12345",
    "sex": "MALE"
  },
  "interpretations": [{
    "diagnosis": {
      "genomicInterpretations": [...]
    }
  }]
}
```

### OMOP CDM v5.4

**Standard**: OMOP Common Data Model v5.4
**Use Case**: Ricerca osservazionale, real-world evidence
**Output**: Tabelle OMOP (person, condition_occurrence, measurement, drug_exposure)

```json
{
  "person": [{
    "person_id": 12345,
    "gender_concept_id": 8507,
    "year_of_birth": 1958
  }],
  "measurement": [{
    "measurement_id": 1,
    "person_id": 12345,
    "measurement_concept_id": 4000000,
    "value_as_number": 45.0
  }]
}
```

---

## Testing

### Test Automatici

```bash
# Test completo del workflow
python examples/test_interactive_mode.py
```

Output:
- Test del workflow completo (parse → validate → interactive → export)
- Test di tutti gli scenari di validazione
- Test di tutti i formati di export

### Test Manuali

```bash
# 1. Crea un report di test incompleto
cat > test_report.txt << EOF
Paziente: TEST001
Età: 65 anni

EGFR L858R 45%
TMB: 8.5 mut/Mb
EOF

# 2. Parse con modalità interattiva
python mtb_parser_cli.py test_report.txt -i -e all

# 3. Controlla gli export generati
ls -la mtb_exports/patient_TEST001/
```

---

## CLI Reference

```bash
python mtb_parser_cli.py --help
```

### Opzioni Principali

| Opzione | Descrizione |
|---------|-------------|
| `input_file` | File report MTB da parsare |
| `--batch DIR` | Batch processing directory |
| `-i, --interactive` | Forza modalità interattiva |
| `--no-auto-interactive` | Disabilita auto-trigger interattivo |
| `-e, --export FORMAT [FORMAT ...]` | Formati export (fhir, phenopackets, omop, json, csv, all) |
| `-o, --output DIR` | Directory output |
| `--pattern PATTERN` | Pattern file per batch (default: *.txt) |
| `-q, --quiet` | Modalità silenziosa |

### Esempi Avanzati

```bash
# Export solo CSV per analisi rapida
python mtb_parser_cli.py report.txt -e csv -o ./analysis

# Batch con pattern custom
python mtb_parser_cli.py --batch ./data/ --pattern "*.mtb" -e all

# Disable auto-interactive per batch processing automatico
python mtb_parser_cli.py --batch ./reports/ --no-auto-interactive -e json
```

---

## Validazione - Regole

### Patient

| Campo | Severità | Requisito |
|-------|----------|-----------|
| ID | CRITICAL | Obbligatorio per tracking |
| Age | WARNING | Utile per decisioni terapeutiche |
| Sex | WARNING | Importante per analisi genomica |
| Birth Date | INFO | Opzionale |

### Diagnosis

| Campo | Severità | Requisito |
|-------|----------|-----------|
| Primary Diagnosis | CRITICAL | Almeno una diagnosi richiesta |
| Stage | WARNING | Guida strategia terapeutica |
| ICD-O Code | INFO | Mapping a standard |

### Variants

| Campo | Severità | Requisito |
|-------|----------|-----------|
| At least one variant | CRITICAL | Core del report MTB |
| Gene name | WARNING | Richiesto per ogni variante |
| VAF | WARNING | Indica clonalità |
| Classification | WARNING | Indica patogenicità |
| HGNC mapping | INFO | Standard nomenclature |

---

## Troubleshooting

### La modalità interattiva non si attiva

**Problema**: Il report ha issues ma l'editor non parte

**Soluzione**:
- Forza con `-i`: `python mtb_parser_cli.py report.txt -i`
- Controlla che ci siano CRITICAL issues (non solo WARNING)

### Export fallisce

**Problema**: Errore durante export in formato specifico

**Soluzione**:
```bash
# Test formato singolarmente
python mtb_parser_cli.py report.txt -e fhir
python mtb_parser_cli.py report.txt -e phenopackets
```

### Encoding errors

**Problema**: Caratteri italiani non visualizzati

**Soluzione**: I file sono salvati in UTF-8. Assicurati che il terminale supporti UTF-8:
```bash
export LANG=it_IT.UTF-8
```

---

## Best Practices

### 1. Workflow Consigliato

```bash
# Step 1: Parse con validazione
python mtb_parser_cli.py report.txt

# Step 2: Se necessario, attiva interactive mode
python mtb_parser_cli.py report.txt -i

# Step 3: Export finale
python mtb_parser_cli.py report.txt -e all -o ./final_exports
```

### 2. Batch Processing

Per grandi volumi:
```bash
# Senza interactive mode (auto-fix solo se implementato)
python mtb_parser_cli.py --batch ./reports/ --no-auto-interactive -e json

# Con review manuale issues
python mtb_parser_cli.py --batch ./reports/ -e all > batch_log.txt 2>&1
```

### 3. Quality Control

```python
from core.report_validator import ReportValidator

validator = ReportValidator()
is_valid, issues = validator.validate(report)

# Check quality
if report.quality_metrics.completeness_pct < 70:
    print("⚠️ Low quality report - consider manual review")
```

---

## Roadmap

### Prossime Feature

- [ ] **Advanced interactive mode** con interfaccia curses completa
- [ ] **Auto-fix suggestions** basati su ML/LLM
- [ ] **Bulk editing** per batch processing
- [ ] **Web interface** per editing remoto
- [ ] **Export to REDCap** format
- [ ] **Integration con CIViC/OncoKB APIs** per annotation automatica
- [ ] **Support HGVS validation** con Mutalyzer API

---

## Contribuire

Per contribuire nuovi formati di export o miglioramenti alla modalità interattiva, vedi `CONTRIBUTING.md`.

---

## Licenza

[Specificare licenza]

---

## Contatti

Per domande o bug report: [specificare contatti]
