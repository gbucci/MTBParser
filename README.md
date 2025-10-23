# MTBParser

**Version 1.0.0** - Parser completo per report di Molecular Tumor Board (MTB) italiani con **export multi-formato** e **modalità interattiva**.

## 🚀 NOVITÀ - Version 1.0.0

### Nuove Features Principali

✅ **Export Multi-Formato Unificato** - Supporto completo per 5 formati interoperabili:
- **FHIR R4** - HL7 FHIR Bundle per integrazione EHR
- **GA4GH Phenopackets v2** - Standard per ricerca genomica internazionale
- **OMOP CDM v5.4** - Common Data Model per studi osservazionali
- **JSON** - Formato nativo MTBParser
- **CSV** - Export tabulari per analisi

✅ **Modalità Interattiva** - Sistema intelligente di validazione e correzione:
- Validazione automatica con 3 livelli di severità (CRITICAL, WARNING, INFO)
- Attivazione automatica per report incompleti
- Editor guidato campo per campo
- Navigazione intuitiva con tastiera

✅ **CLI Completo** - Interfaccia command-line production-ready:
- Parse singolo o batch processing
- Export selettivo o completo
- Configurazione flessibile

**📖 Documentazione Nuove Features:**
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Guida rapida comandi
- **[README_INTERACTIVE.md](README_INTERACTIVE.md)** - Guida completa modalità interattiva ed export
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Dettagli tecnici

---

## Descrizione

MTBParser è uno strumento Python che estrae automaticamente dati clinici molecolari strutturati da report MTB in formato testuale e li converte in **5 formati standard interoperabili** per l'integrazione in sistemi sanitari ed ambiti di ricerca.

Il parser è ottimizzato per gestire report MTB italiani, riconoscendo terminologia medica italiana e formati tipici dei centri oncologici italiani.

## Caratteristiche

- **Estrazione automatica** di dati clinici da testo non strutturato
- **Supporto multi-formato** per varianti genomiche (tabulari, inline, fusioni geniche)
- **Conversione FHIR R4** completa seguendo le linee guida per genomica
- **Terminologia italiana** e inglese per classificazioni patogenicità
- **Mappatura farmaci** per terapie target oncologiche
- **Codifiche standard**: LOINC, HGNC, FHIR Observation

## Dati Estratti

### Informazioni Paziente
- ID paziente
- Età e sesso
- Data di nascita

### Diagnosi
- Diagnosi principale
- Stadio tumorale
- Istologia

### Varianti Genomiche
- Gene
- Variante cDNA (notazione HGVS)
- Variante proteica (notazione HGVS)
- Classificazione patogenicità (Pathogenic, VUS, Benign, ecc.)
- VAF (Variant Allele Frequency)
- Fusioni geniche

### Parametri Molecolari
- TMB (Tumor Mutational Burden)
- Metodica NGS utilizzata

### Raccomandazioni Terapeutiche
- Farmaci target
- Gene bersaglio
- Livello di evidenza
- Trial clinici
- Razionale della raccomandazione

## 🚀 Quick Start (Nuova CLI)

### Installazione

```bash
# Clone del repository
git clone https://github.com/gbucci/MTBParser.git
cd MTBParser

# Installazione dipendenze base
pip install pandas

# Installazione dipendenze per generazione PDF (opzionale)
pip install reportlab
```

### Uso CLI (NUOVO)

```bash
# Parse report di esempio con export completo
python mtb_parser_cli.py examples/sample_report.txt -e all -o ./exports

# Parse con modalità interattiva
python mtb_parser_cli.py my_report.txt -i

# Batch processing di una directory
python mtb_parser_cli.py --batch ./reports/ -e all

# Export solo FHIR per integrazione EHR
python mtb_parser_cli.py report.txt -e fhir -o ./ehr_integration

# Help completo
python mtb_parser_cli.py --help
```

**Output organizzato per paziente:**
```
exports/
└── patient_12345/
    ├── fhir_r4_bundle.json
    ├── ga4gh_phenopacket_v2.json
    ├── omop_cdm_v5_4.json
    ├── mtb_report.json
    └── csv/
        ├── patient_summary.csv
        ├── variants.csv
        └── recommendations.csv
```

### Requisiti
- Python 3.7+
- pandas

## Utilizzo

### Esempio Base

```python
from mtb_parser import MTBParser, FHIRMapper

# Inizializza il parser
parser = MTBParser()

# Testo del report MTB
report_text = """
ID Paziente: 4158446 Sesso: M Età: 49 anni
Diagnosi: Adenocarcinoma polmonare

Gene Variante cDNA Variante aminoacidica Classificazione Frequenza allelica
EGFR c.2573T>G p.Leu858Arg (L858R) Pathogenic 45%
KRAS c.35G>A p.Gly12Asp (G12D) Pathogenic 38%

Il valore del TMB è 8.5 muts/Mbp.
Si segnala sensibilità a Osimertinib.
"""

# Parse del report
mtb_report = parser.parse_report(report_text)

# Visualizza risultati
print(f"Paziente: {mtb_report.patient.id}")
print(f"Varianti trovate: {len(mtb_report.variants)}")
for variant in mtb_report.variants:
    print(f"  - {variant.gene}: {variant.protein_change} (VAF: {variant.vaf}%)")
```

### Conversione FHIR

```python
from mtb_parser import MTBParser, FHIRMapper
import json

# Parse del report
parser = MTBParser()
mtb_report = parser.parse_report(report_text)

# Converti in FHIR Bundle
fhir_mapper = FHIRMapper()
fhir_bundle = fhir_mapper.create_fhir_bundle(mtb_report)

# Salva in JSON
with open('fhir_bundle.json', 'w') as f:
    json.dump(fhir_bundle, f, indent=2)

print(f"FHIR Bundle creato con {len(fhir_bundle['entry'])} risorse")
```

### Processing Multiplo

```python
from mtb_parser import process_mtb_reports

# Lista di report testuali
reports = [report1_text, report2_text, report3_text]

# Processa tutti i report
results = process_mtb_reports(reports)

for result in results:
    parsed = result['parsed_report']
    fhir = result['fhir_bundle']
    print(f"Paziente {parsed['patient']['id']}: {len(parsed['variants'])} varianti")
```

### Generazione Report PDF

MTBParser può generare report PDF professionali dai dati estratti:

```bash
# Genera PDF da file JSON completo
python3 generate_pdf_report.py output/report_001/complete_package.json

# Specifica percorso di output personalizzato
python3 generate_pdf_report.py output/report_001/complete_package.json custom_report.pdf
```

Il report PDF include:
- Anagrafica paziente
- Diagnosi con codici ICD-O
- Informazioni sul panel NGS utilizzato (FoundationOne CDx, OncoPanel Plus, etc.)
- Tabella delle varianti genomiche con classificazione
- Tumor Mutational Burden (TMB)
- Raccomandazioni terapeutiche con livelli di evidenza

Il generatore rileva automaticamente il panel NGS utilizzato confrontando i geni identificati con i panel standard oncologici.

### Test Rapido

Esegui il file principale per vedere un esempio funzionante:

```bash
python3 mtb_parser.py
```

## Clinical Annotation (NEW in v1.1.0)

MTBParser integra tre sorgenti di evidenza clinica per l'annotazione delle varianti genomiche:

### Annotatori Disponibili

| Annotatore | Licenza | Costo | Focus | Evidenze |
|-----------|---------|-------|-------|----------|
| **CIViC** | FREE | CC0 Public Domain | Global, community | ~3000+ variants |
| **ESCAT** | FREE | Citation required | European/ESMO | ~50+ tier-classified |
| **OncoKB** | COMMERCIAL | Free tier/Paid | US/FDA | ~5000+ variants |

### Quick Start - Free Sources (Default)

```python
from annotators.combined_annotator import CombinedAnnotator

# Default: CIViC + ESCAT (both free)
annotator = CombinedAnnotator()

# Annotate variant
result = annotator.annotate_variant('EGFR', 'L858R', 'NSCLC')
report = annotator.get_clinical_report(result)

print(f"Actionability: {report['actionability']['score']}/100")
print(f"ESCAT Tier: {report['escat_classification']['tier']}")
print(f"FDA Drugs: {report['therapeutic_options']['fda_approved']}")
```

### Configuration Presets

```python
from annotators.annotator_config import AnnotatorConfig

# European hospitals (ESCAT + CIViC)
config = AnnotatorConfig.european_clinical()
annotator = CombinedAnnotator(config=config)

# US hospitals (OncoKB + CIViC)
config = AnnotatorConfig.us_clinical(oncokb_api_key="your_key")

# Maximum validation (all three sources)
config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")

# ESCAT only (European standard)
config = AnnotatorConfig.escat_only()
```

### Integration with MTB Reports

```python
from core.mtb_parser import MTBParser
from annotators.combined_annotator import CombinedAnnotator

# Parse MTB report
parser = MTBParser()
mtb_report = parser.parse_report(report_text)

# Annotate variants with free sources
annotator = CombinedAnnotator()

for variant in mtb_report.variants:
    result = annotator.annotate_variant(
        gene=variant.gene,
        variant=variant.protein_change,
        tumor_type=mtb_report.diagnosis.primary_diagnosis
    )

    report = annotator.get_clinical_report(result)
    print(f"{variant.gene}: ESCAT {report['escat_classification']['tier']}")
    print(f"  Drugs: {report['therapeutic_options']['fda_approved']}")
```

**Documentazione completa:**
- [ANNOTATOR_CONFIGURATION.md](ANNOTATOR_CONFIGURATION.md) - Configuration guide
- [ESCAT_INTEGRATION.md](ESCAT_INTEGRATION.md) - ESCAT tier system details
- [examples/annotator_configuration_examples.py](examples/annotator_configuration_examples.py) - Examples

## Formati Report Supportati

### Formato Tabellare
```
Gene  Variante cDNA    Variante aminoacidica  Classificazione  Frequenza allelica
EGFR  c.2573T>G        p.Leu858Arg (L858R)    Pathogenic       45%
TP53  c.524G>A         p.Arg175His (R175H)    Pathogenic       62%
```

### Formato Inline
```
Mutazione di EGFR: L858R (45%)
Alterazione di KRAS G12C con frequenza del 38%
```

### Fusioni Geniche
```
fusione ALK::EML4
riarrangiamento RET/PTC
```

## Struttura FHIR

Il mapper FHIR genera un Bundle contenente:

1. **Patient**: Dati demografici del paziente
2. **Observation** (per ogni variante):
   - Gene (LOINC 48018-6, codificato HGNC)
   - Variante DNA cDNA (LOINC 48004-6)
   - Variante proteica (LOINC 48005-3)
   - VAF (LOINC 81258-6)
   - Classificazione patogenicità
3. **Observation** (TMB): LOINC 94076-7
4. **DiagnosticReport**: Master genetic panel (LOINC 81247-9)

### Codifiche Utilizzate
- **LOINC**: Codici per osservazioni genetiche
- **HGNC**: Gene symbols standardizzati
- **FHIR Observation Interpretation**: Classificazioni patogenicità

## Estensioni

### Aggiungere Nuovi Geni

Modifica `FHIRMapper.gene_code_map`:

```python
self.gene_code_map = {
    'NUOVO_GENE': {'system': 'http://www.genenames.org', 'code': 'HGNC:XXXX'},
    # ... altri geni
}
```

### Aggiungere Pattern Varianti

Aggiungi pattern regex in `MTBParser.variant_patterns`:

```python
self.variant_patterns = [
    r'nuovo_pattern_regex',
    # ... altri pattern
]
```

### Aggiungere Farmaci

Estendi `MTBParser.drug_patterns`:

```python
self.drug_patterns = [
    r'(nuovo_farmaco|altro_farmaco)',  # Nuova classe
    # ... altri farmaci
]
```

## Limitazioni

- Il parser usa regex e può non catturare tutti i formati possibili
- Supporto ottimizzato per report italiani; report in altre lingue potrebbero richiedere adattamenti
- La qualità dell'estrazione dipende dalla struttura del report originale
- L'input deve essere in formato testo (non gestisce direttamente immagini o PDF scansionati)

## Contribuire

Contributi benvenuti! Per aggiungere funzionalità:

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/nuova-feature`)
3. Commit delle modifiche (`git commit -m 'Aggiunge nuova feature'`)
4. Push al branch (`git push origin feature/nuova-feature`)
5. Apri una Pull Request

## Sviluppo

Consulta il file [CLAUDE.md](CLAUDE.md) per dettagli sull'architettura e linee guida per lo sviluppo.

## Licenza

Questo progetto è distribuito sotto licenza open source.

## Autori

- Gabriele Bucci (bucci.g@gmail.com)

## Riferimenti

- [HL7 FHIR Genomics](https://www.hl7.org/fhir/genomics.html)
- [FHIR Observation](https://www.hl7.org/fhir/observation.html)
- [LOINC Genetic Testing](https://loinc.org/)
- [HGNC Gene Nomenclature](https://www.genenames.org/)
