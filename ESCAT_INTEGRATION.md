# ESCAT Integration - ESMO Scale for Clinical Actionability

**Data:** 2025-10-22
**Versione:** 1.1.0

## Overview

Implementazione completa del sistema **ESCAT (ESMO Scale for Clinical Actionability of molecular Targets)** per la classificazione tier-based dell'actionability clinica delle alterazioni molecolari secondo gli standard ESMO.

ESCAT fornisce un framework standardizzato per guidare le decisioni terapeutiche nella pratica oncologica europea, classificando le alterazioni genomiche in 9 livelli (tier) basati sulla forza dell'evidenza clinica.

## ESCAT Framework

### Tier Classification

**TIER I - Targets ready for routine use:**
- **I-A:** Approvazione regolatoria (EMA/FDA/AIFA) in questa indicazione
- **I-B:** Raccomandato da linee guida cliniche (ESMO-MCBS ≥4)
- **I-C:** Farmaco approvato ma in diversa indicazione tumorale

**TIER II - Investigational targets (likely clinically actionable):**
- **II-A:** Prove cliniche consistenti in tumori resistenti/refrattari
- **II-B:** Evidenza preclinica robusta con rilevanza clinica

**TIER III - Clinical benefit in other tumor types:**
- **III-A:** Beneficio clinico dimostrato in altro tipo tumorale con stesso target

**TIER IV:** Evidenza preclinica di actionability

**TIER V:** Evidenza da eventi genomici co-occorrenti

**TIER X:** Assenza di evidenza o marker di resistenza

### Scoring System

ESCAT Score (0-100):
- Tier I-A: 100 punti
- Tier I-B: 90 punti
- Tier I-C: 80 punti
- Tier II-A: 70 punti
- Tier II-B: 60 punti
- Tier III-A: 50 punti
- Tier IV: 30 punti
- Tier V: 20 punti
- Tier X: 0 punti

Actionability threshold: ≥50 punti (Tier III-A o superiore)

## Implementation

### File Structure

```
annotators/
├── escat_annotator.py        # ESCAT annotator (850+ linee)
├── combined_annotator.py     # Integrazione ESCAT + CIViC + OncoKB
└── __init__.py               # Export ESCATAnnotator
```

### Core Module: `escat_annotator.py`

**Classes:**
- `ESCATTier(Enum)`: Tier enumeration
- `ESCATEvidence`: Evidence item dataclass
- `ESCATAnnotation`: Complete annotation result
- `ESCATAnnotator`: Main annotator class

**Key Features:**
- Curated knowledge base con >20 alterazioni tier-classified
- Normalizzazione automatica tumor types (italiano/inglese)
- Normalizzazione variant notation (HGVS, comuni, fusioni)
- Identificazione indicazioni alternative
- Generazione raccomandazioni cliniche in italiano
- Supporto ESMO-MCBS scoring

### Knowledge Base Coverage

**Tier I-A (EMA/FDA approved):**
- EGFR: L858R, exon 19 deletion, T790M (NSCLC)
- ALK: Fusion (NSCLC)
- ROS1: Fusion (NSCLC)
- BRAF: V600E (Melanoma, Colorectal)
- KRAS: G12C (NSCLC)
- ERBB2: Amplification (Breast, Gastric)
- BRCA1/BRCA2: Loss (Ovarian)
- RET: Fusion (NSCLC)
- NTRK: Fusion (Solid Tumors - tissue agnostic)

**Tier I-B (Guidelines):**
- PIK3CA: H1047R (Breast)
- MET: exon 14 skipping (NSCLC)

**Tier I-C (Off-label):**
- BRAF: V600E (NSCLC - approved in melanoma)

**Tier II-A (Clinical evidence):**
- FGFR2: Fusion (Cholangiocarcinoma)
- FGFR3: Mutations (Bladder)

**Tier III-A (Other tumor types):**
- ERBB2: Amplification (Colorectal - approved in breast/gastric)

**Tier X (Resistance):**
- KRAS: G12D (Colorectal - resistance to anti-EGFR)

## Usage

### Standalone ESCAT Annotation

```python
from annotators.escat_annotator import ESCATAnnotator

annotator = ESCATAnnotator()

# Annotate variant
annotation = annotator.annotate_variant(
    gene="EGFR",
    alteration="L858R",
    tumor_type="NSCLC"
)

# Generate report
report = annotator.get_escat_report(annotation)

print(f"ESCAT Tier: {report['escat_classification']['tier']}")
print(f"Score: {report['escat_classification']['score']}/100")
print(f"Actionable: {report['escat_classification']['is_actionable']}")
print(f"Drugs: {report['therapeutic_options']['tier_I']}")
print(f"Recommendation: {report['clinical_recommendation']}")
```

**Output:**
```
ESCAT Tier: I-A
Score: 100/100
Actionable: True
Drugs: ['Osimertinib', 'Gefitinib', 'Erlotinib', 'Afatinib']
Recommendation: ESCAT Tier I-A: Uso routinario raccomandato.
Osimertinib, Gefitinib, Erlotinib approvato/i da EMA/FDA per questa
indicazione. Terapia standard secondo linee guida ESMO/AIOM.
```

### Integrated Annotation (ESCAT + CIViC + OncoKB)

```python
from annotators.combined_annotator import CombinedAnnotator

annotator = CombinedAnnotator()

# Annotate with all three sources
combined = annotator.annotate_variant(
    gene="EGFR",
    variant="L858R",
    tumor_type="Lung Adenocarcinoma"
)

# Get comprehensive report
report = annotator.get_clinical_report(combined)

print(f"Overall Actionability: {report['actionability']['score']}/100")
print(f"Evidence Level: {report['actionability']['level']}")
print(f"ESCAT Tier: {report['escat_classification']['tier']}")
print(f"Sources: {', '.join(report['evidence_sources'])}")
print(f"FDA Drugs: {report['therapeutic_options']['fda_approved']}")
```

**Output:**
```
Overall Actionability: 100/100
Evidence Level: ESCAT_I-A
ESCAT Tier: I-A
Sources: CIViC, OncoKB, ESCAT
FDA Drugs: ['Osimertinib', 'Gefitinib', 'Erlotinib', 'Afatinib']
```

### Integration with MTB Parser

```python
from core.mtb_parser import MTBParser
from annotators.combined_annotator import CombinedAnnotator

# Parse report
parser = MTBParser()
mtb_report = parser.parse_report(report_text)

# Annotate with ESCAT
annotator = CombinedAnnotator()

for variant in mtb_report.variants:
    annotation = annotator.annotate_variant(
        gene=variant.gene,
        variant=variant.protein_change or variant.cdna_change,
        tumor_type=mtb_report.diagnosis.primary_diagnosis
    )

    report = annotator.get_clinical_report(annotation)

    # Print ESCAT classification
    escat = report['escat_classification']
    print(f"\n{variant.gene} {variant.protein_change}")
    print(f"ESCAT Tier: {escat['tier']}")
    print(f"ESCAT Score: {escat['score']}/100")
    print(f"Description: {escat['description']}")
```

## Clinical Recommendations

ESCAT genera raccomandazioni cliniche automatiche in italiano basate sul tier:

**Tier I-A:**
> "ESCAT Tier I-A: Uso routinario raccomandato. [farmaci] approvato/i da EMA/FDA per questa indicazione. Terapia standard secondo linee guida ESMO/AIOM."

**Tier I-B:**
> "ESCAT Tier I-B: Raccomandato dalle linee guida cliniche (ESMO-MCBS ≥4). Considerare [farmaci] secondo protocolli ESMO."

**Tier I-C:**
> "ESCAT Tier I-C: Farmaco approvato in diversa indicazione tumorale. Considerare uso off-label di [farmaci] previo consenso informato."

**Tier II-A:**
> "ESCAT Tier II-A: Evidenza clinica in tumori resistenti/refrattari. Considerare [farmaci] in contesto di early access program o clinical trial."

**Tier III-A:**
> "ESCAT Tier III-A: Beneficio dimostrato in [altri tumori]. Considerare [farmaci] in contesto off-label o basket trial."

**Tier X:**
> "ESCAT Tier X: Marker di resistenza o nessuna evidenza di actionability. Evitare terapie non efficaci. Considerare alternative terapeutiche."

## Alternative Indications

ESCAT identifica automaticamente indicazioni alternative per lo stesso target in diversi tipi tumorali:

```python
annotation = annotator.annotate_variant("BRAF", "V600E", "NSCLC")
report = annotator.get_escat_report(annotation)

# Alternative indications
for alt in report['alternative_indications']:
    print(f"{alt['tumor_type']}: {alt['tier']} - {', '.join(alt['drugs'])}")
```

**Output:**
```
Melanoma: I-A - Dabrafenib + Trametinib, Vemurafenib + Cobimetinib
Colorectal Cancer: I-A - Encorafenib + Cetuximab
```

## Validation & Quality

### Normalization Features

**Tumor Type Normalization:**
- Italiano → Inglese: "polmonare" → "lung", "mammella" → "breast"
- Acronimi: "NSCLC" → "lung"
- Varianti: "adenocarcinoma polmonare" → "nsclc"

**Alteration Normalization:**
- Rimozione prefissi: "p.L858R" → "L858R"
- Pattern comuni: "fusione ALK" → "FUSION"
- CNV: "amplificazione ERBB2" → "AMPLIFICATION"
- Exon-level: "exon 19 deletion" → standardized

### Evidence Quality

Ogni evidenza ESCAT include:
- **Approval agency:** EMA, FDA, AIFA
- **Guidelines:** ESMO, NCCN, AIOM
- **ESMO-MCBS score:** 1-5 (Magnitude of Clinical Benefit)
- **PMIDs:** Riferimenti PubMed
- **Clinical trial phase:** Per tier investigazionali

## Integration Benefits

### Combined Annotator Enhancements

Con l'integrazione ESCAT, il `CombinedAnnotator` ora:

1. **Priorità ESCAT:** Score ESCAT ha priorità per contesto europeo
2. **Bonus concordanza:** +10% se 2 sources concordano, +15% se tutte e 3
3. **Threshold actionability:** 50 punti (ESCAT Tier III-A)
4. **Triple validation:** Evidenze concordanti da CIViC + OncoKB + ESCAT

### Scoring Hierarchy

```python
# Priority order for combined score:
1. ESCAT (European standard)
2. OncoKB (US FDA-focused)
3. CIViC (Community curated)

# Example: EGFR L858R
ESCAT: Tier I-A (100) ← selected
OncoKB: Level 1 (100)
CIViC: Level A (100)
Combined Score: 100 × 1.15 = 115 → capped at 100
```

## Testing

### Run standalone test:
```bash
python3 annotators/escat_annotator.py
```

### Run combined test:
```bash
python3 -c "
from annotators.combined_annotator import CombinedAnnotator
annotator = CombinedAnnotator()
result = annotator.annotate_variant('EGFR', 'L858R', 'NSCLC')
report = annotator.get_clinical_report(result)
print(f'ESCAT Tier: {report[\"escat_classification\"][\"tier\"]}')
print(f'Sources: {report[\"evidence_sources\"]}')
"
```

### Expected output:
```
ESCAT Tier: I-A
Sources: ['CIViC', 'OncoKB', 'ESCAT']
```

## Comparison with Other Standards

| Feature | ESCAT | OncoKB | CIViC |
|---------|-------|--------|-------|
| Focus | European/ESMO | US/FDA | Community |
| Levels | 9 tiers | 8 levels | 5 levels |
| Language | EN/IT | English | English |
| Approval | EMA focus | FDA focus | Global |
| Guidelines | ESMO, AIOM | NCCN | Multiple |
| Resistance | Tier X | R1/R2 | Evidence type |
| Off-label | Tier I-C, III-A | Level 3B | Level C |
| Updates | Manual | API | API |

## Clinical Workflow Integration

### Molecular Tumor Board Report

```
VARIANTE: EGFR L858R
TUMORE: Adenocarcinoma polmonare stadio IV

CLASSIFICAZIONE ESCAT:
  Tier: I-A
  Score: 100/100
  Stato: ✓ ACTIONABLE
  Descrizione: Target pronto per uso routinario - Approvazione regolatoria

FARMACI APPROVATI (Tier I):
  ✓ Osimertinib (EMA, FDA, AIFA)
  ✓ Gefitinib (EMA, FDA, AIFA)
  ✓ Erlotinib (EMA, FDA, AIFA)
  ✓ Afatinib (EMA, FDA, AIFA)

LINEE GUIDA:
  - ESMO Guidelines: First-line therapy
  - AIOM Guidelines: Raccomandato
  - ESMO-MCBS Score: 4/5

EVIDENZE:
  - Approval: EMA, FDA, AIFA
  - PMID: 24065731, 26522272
  - Clinical trials: Multiple Phase 3

RACCOMANDAZIONE:
  ESCAT Tier I-A: Uso routinario raccomandato. Osimertinib approvato
  da EMA/FDA per questa indicazione. Terapia standard secondo linee
  guida ESMO/AIOM. Prima linea preferita: Osimertinib.
```

## References

### Primary Source
- **Mateo J, et al.** A framework to rank genomic alterations as targets for cancer precision medicine: the ESMO Scale for Clinical Actionability of molecular Targets (ESCAT). *Ann Oncol.* 2018;29(9):1895-1902.
- DOI: 10.1093/annonc/mdy263
- PMID: 30137196

### ESMO Guidelines
- ESMO Precision Medicine Working Group
- https://www.esmo.org/guidelines/precision-medicine
- ESMO-MCBS: Magnitude of Clinical Benefit Scale

### Italian Guidelines
- AIOM (Associazione Italiana di Oncologia Medica)
- Linee Guida AIOM per test biomarcatori
- AIFA (Agenzia Italiana del Farmaco) - Lista farmaci oncologici

### Regulatory Agencies
- **EMA:** European Medicines Agency
- **FDA:** US Food and Drug Administration
- **AIFA:** Agenzia Italiana del Farmaco

## Future Enhancements

### Planned Features
1. **Dynamic updates:** Integrazione con ESMO Precision Medicine Database
2. **ESMO-MCBS calculator:** Calcolo automatico magnitude of benefit
3. **Basket trial matching:** Identificazione trial tissue-agnostic
4. **Resistance pathways:** Mappatura meccanismi di resistenza
5. **Cost-effectiveness:** Integrazione dati farmacoeconomici AIFA

### Extended Coverage
- Aggiungere tier IV, V con evidenze precliniche
- Integrare alterazioni rare da letteratura ESMO
- Supporto per varianti germline (BRCA1/2, Lynch)
- Pathway analysis per co-occurring alterations

## Compliance

### GDPR Compliance
- No patient data storage
- Local processing only
- No external API calls (mock mode)

### Medical Device Regulation
- **Non è un dispositivo medico**
- Solo supporto decisionale
- Richiede validazione clinica
- Uso sotto supervisione medica

## License & Attribution

**Required citation for clinical use:**
> Mateo J, et al. A framework to rank genomic alterations as targets for cancer precision medicine: the ESMO Scale for Clinical Actionability of molecular Targets (ESCAT). Ann Oncol. 2018;29(9):1895-1902.

**Usage:**
- Academic research: ✓ Permitted
- Clinical decision support: ✓ Permitted with disclaimer
- Commercial use: Contact ESMO for licensing

---

**Implementation by:** MTBParser System v1.1.0
**Date:** 2025-10-22
**Contact:** See repository for updates
