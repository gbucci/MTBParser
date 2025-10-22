# MTBParser

Parser e convertitore FHIR per report di Molecular Tumor Board (MTB) italiani.

## Descrizione

MTBParser è uno strumento Python che estrae automaticamente dati clinici molecolari strutturati da report MTB in formato testuale e li converte in risorse FHIR R4 standard per l'interoperabilità sanitaria.

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

## Installazione

### Requisiti
- Python 3.7+
- pandas

### Setup

```bash
# Clone del repository
git clone https://github.com/gbucci/MTBParser.git
cd MTBParser

# Installazione dipendenze
pip install pandas
```

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

### Test Rapido

Esegui il file principale per vedere un esempio funzionante:

```bash
python3 mtb_parser.py
```

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
- Non gestisce immagini o PDF (richiede pre-conversione in testo)

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
