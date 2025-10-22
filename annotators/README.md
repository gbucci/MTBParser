# Clinical Annotators Module

Integration with precision oncology knowledge bases for variant clinical interpretation.

## Overview

This module provides clinical annotation for genomic variants identified in MTB reports by integrating with:
- **CIViC** (Clinical Interpretations of Variants in Cancer)
- **OncoKB** (Precision Oncology Knowledge Base)

## Features

### 1. CIViC Annotator (`civic_annotator.py`)

Queries CIViC database for variant clinical significance with evidence levels A-E.

**Evidence Types:**
- Diagnostic: Biomarker for disease detection
- Prognostic: Impact on patient outcomes
- Predictive: Response to therapy

**Evidence Levels:**
- **Level A:** FDA/EMA approved therapy
- **Level B:** Clinical evidence in multiple studies
- **Level C:** Case reports or preclinical evidence
- **Level D:** Preclinical evidence only
- **Level E:** Indirect evidence

**Example:**
```python
from annotators.civic_annotator import CIViCAnnotator

annotator = CIViCAnnotator()
annotation = annotator.annotate_variant("EGFR", "L858R", "Lung Adenocarcinoma")

# Get evidence summary
summary = annotator.get_evidence_summary(annotation)
print(f"Max Evidence Level: {summary['max_evidence_level']}")
print(f"Actionable Drugs: {summary['actionable_drugs']}")
```

### 2. OncoKB Annotator (`oncokb_annotator.py`)

Queries OncoKB for therapeutic implications with FDA approval status.

**Evidence Levels:**
- **Level 1:** FDA-recognized biomarker for FDA-approved drug
- **Level 2:** Standard care (NCCN guidelines)
- **Level 3A:** Compelling clinical evidence
- **Level 3B:** Different tumor type or preclinical
- **Level 4:** Biological evidence
- **Level R1/R2:** Resistance biomarkers

**Oncogenic Classification:**
- Oncogenic
- Likely Oncogenic
- Variant of Uncertain Significance (VUS)
- Likely Neutral

**Example:**
```python
from annotators.oncokb_annotator import OncoKBAnnotator

annotator = OncoKBAnnotator()
annotation = annotator.annotate_variant("BRAF", "V600E", "Melanoma")

# Get therapeutic summary
summary = annotator.get_therapeutic_summary(annotation)
print(f"Oncogenic: {summary['oncogenic']}")
print(f"FDA Approved: {summary['fda_approved_drugs']}")
```

### 3. Combined Annotator (`combined_annotator.py`)

Aggregates evidence from both CIViC and OncoKB for comprehensive interpretation.

**Actionability Scoring (0-100):**
- FDA-approved: 100 points
- Guideline (Level 2/B): 80 points
- Clinical evidence (3A/C): 60 points
- Preclinical (3B/D): 40 points
- Biological (4/E): 20 points

**Therapeutic Categorization:**
- FDA-approved therapies
- Guideline-recommended therapies
- Investigational therapies
- Resistance markers

**Example:**
```python
from annotators.combined_annotator import CombinedAnnotator

annotator = CombinedAnnotator()
combined = annotator.annotate_variant("KRAS", "G12C", "NSCLC")

# Generate clinical report
report = annotator.get_clinical_report(combined)

print(f"Actionability: {report['actionability']['score']}/100")
print(f"FDA Drugs: {report['therapeutic_options']['fda_approved']}")
print(f"Recommendation: {report['recommendation']}")
```

## Mock vs Production Mode

### Current Implementation (Mock Mode)

The current implementation uses **mock databases** with common actionable variants:

**Advantages:**
- ✓ No API dependencies
- ✓ Works offline
- ✓ Fast response times
- ✓ No rate limits
- ✓ Consistent results

**Mock Database Coverage:**

CIViC (8 variants):
- EGFR: L858R, T790M
- BRAF: V600E
- KRAS: G12C
- ALK, RET: Fusions
- BRCA1: Loss-of-function
- ERBB2: Amplification

OncoKB (10+ variants):
- All CIViC variants plus:
- KRAS: G12D
- PIK3CA: H1047R
- Additional resistance markers

### Production API Integration

To use real APIs instead of mock data:

#### 1. CIViC API

Register and use GraphQL endpoint:

```python
import requests

CIVIC_API_URL = "https://civicdb.org/api/graphql"

query = """
query {
  variants(entrezSymbol: "EGFR", name: "L858R") {
    id
    name
    variantTypes { name }
    evidenceItems {
      id
      evidenceType
      evidenceLevel
      clinicalSignificance
      drugs { name }
      disease { name }
      source {
        sourceType
        citationId
      }
    }
  }
}
"""

response = requests.post(CIVIC_API_URL, json={'query': query})
data = response.json()
```

**Resources:**
- API Docs: https://docs.civicdb.org/
- GraphQL Explorer: https://civicdb.org/api/graphql
- No API key required (public access)

#### 2. OncoKB API

Register for API token:

```python
import requests
import os

ONCOKB_API_URL = "https://www.oncokb.org/api/v1"
API_TOKEN = os.environ.get('ONCOKB_API_TOKEN')

headers = {
    'Authorization': f'Bearer {API_TOKEN}'
}

params = {
    'hugoSymbol': 'EGFR',
    'alteration': 'L858R',
    'tumorType': 'Lung Adenocarcinoma'
}

response = requests.get(
    f"{ONCOKB_API_URL}/annotate/mutations/byProteinChange",
    headers=headers,
    params=params
)

annotation = response.json()
```

**Resources:**
- Register: https://www.oncokb.org/apiAccess
- API Docs: https://www.oncokb.org/api/
- Requires institutional email for academic use
- Rate limit: 1000 requests/month (free tier)

#### 3. Environment Setup

```bash
# .env file
ONCOKB_API_TOKEN=your_token_here
CIVIC_API_URL=https://civicdb.org/api/graphql

# Enable in Python
from dotenv import load_dotenv
load_dotenv()

annotator = OncoKBAnnotator(api_token=os.getenv('ONCOKB_API_TOKEN'))
```

## Integration with MTBParser

Full example with clinical annotations:

```python
from core.mtb_parser import MTBParser
from annotators.combined_annotator import CombinedAnnotator

# Parse MTB report
parser = MTBParser()
report = parser.parse_report(mtb_text)

# Annotate variants
annotator = CombinedAnnotator()

for variant in report.variants:
    # Get clinical annotation
    annotation = annotator.annotate_variant(
        gene=variant.gene,
        variant=variant.protein_change or variant.cdna_change,
        tumor_type=report.diagnosis.primary_diagnosis
    )

    # Generate clinical report
    clinical_report = annotator.get_clinical_report(annotation)

    # Display results
    print(f"\n{variant.gene} {variant.protein_change}")
    print(f"Actionable: {clinical_report['actionability']['is_actionable']}")
    print(f"Score: {clinical_report['actionability']['score']}/100")
    print(f"FDA Drugs: {clinical_report['therapeutic_options']['fda_approved']}")
    print(f"Recommendation: {clinical_report['recommendation']}")
```

See `example_annotated_parsing.py` for complete working example.

## Data Models

### CIViC Evidence

```python
@dataclass
class CIViCEvidence:
    evidence_id: str
    evidence_type: str  # Diagnostic, Prognostic, Predictive
    evidence_level: str  # A, B, C, D, E
    evidence_direction: str  # Supports, Does not support
    clinical_significance: str  # Sensitivity/Response, Resistance
    drug_names: List[str]
    disease: str
    source_type: str
    citation: str
    rating: Optional[float]
```

### OncoKB Treatment

```python
@dataclass
class OncoKBTreatment:
    drug_names: List[str]
    level: str  # LEVEL_1, LEVEL_2, LEVEL_3A, etc.
    cancer_type: str
    indication: str
    fda_approved: bool
    evidence_pmids: List[str]
```

### Combined Evidence

```python
@dataclass
class CombinedEvidence:
    gene: str
    variant: str
    is_actionable: bool
    actionability_score: float  # 0-100
    fda_approved_therapies: List[str]
    guideline_therapies: List[str]
    investigational_therapies: List[str]
    resistance_therapies: List[str]
    highest_evidence_level: str
    oncogenic_classification: str
    civic_url: str
    oncokb_url: str
```

## Testing

Run individual annotators:

```bash
# Test CIViC
python3 -m annotators.civic_annotator

# Test OncoKB
python3 -m annotators.oncokb_annotator

# Test Combined
python3 -m annotators.combined_annotator
```

Run full integration test:

```bash
python3 example_annotated_parsing.py
```

## Performance Considerations

### Caching
All annotators include in-memory caching:
- Cache key: `{gene}_{variant}_{tumor_type}`
- Recommended: Add Redis for persistent cache in production

### Rate Limiting
For production APIs:
- CIViC: No official rate limit (use respectfully)
- OncoKB: 1000 requests/month (free tier)
- Implement exponential backoff for retries
- Cache results aggressively

### Batch Processing
For processing many reports:

```python
# Process variants in batches
from concurrent.futures import ThreadPoolExecutor

def annotate_batch(variants):
    annotator = CombinedAnnotator()
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                annotator.annotate_variant,
                v.gene, v.protein_change, tumor_type
            )
            for v in variants
        ]

        for future in futures:
            results.append(future.result())

    return results
```

## Error Handling

Annotators gracefully handle:
- Unknown variants (return empty annotation)
- API failures (fallback to cached data)
- Network timeouts (retry with backoff)
- Invalid gene symbols (skip annotation)

## Future Enhancements

Potential additions:
1. **ClinVar** integration for germline variants
2. **My Cancer Genome** for narrative summaries
3. **Cancer Genome Interpreter** (CGI) for driver predictions
4. **PharmGKB** for pharmacogenomic associations
5. **Clinical trial matching** (ClinicalTrials.gov API)
6. **Variant normalization** (HGVS validation)
7. **VEP/SnpEff** for consequence prediction

## References

**Primary Sources:**
- Griffith M, et al. CIViC is a community knowledgebase for expert crowdsourcing the clinical interpretation of variants in cancer. Nat Genet. 2017;49(2):170-174.
- Chakravarty D, et al. OncoKB: A Precision Oncology Knowledge Base. JCO Precis Oncol. 2017;2017:PO.17.00011.

**Guidelines:**
- AMP/ASCO/CAP Standards for interpretation of sequence variants
- NCCN Biomarker testing guidelines
- ESMO Precision Medicine recommendations

## License

Academic use permitted with proper attribution.

**Required citations for production use:**
- CIViC: CC0 (public domain)
- OncoKB: Academic license required (register at oncokb.org)
