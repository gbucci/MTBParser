# Annotator Configuration System

**Data:** 2025-10-22
**Versione:** 1.1.0

## Overview

Il sistema di configurazione degli annotatori permette di scegliere quali sorgenti di evidenza clinica utilizzare per l'annotazione delle varianti genomiche. Questo è essenziale perché alcune sorgenti richiedono licenze commerciali mentre altre sono gratuite.

## Available Annotators

### CIViC (Clinical Interpretations of Variants in Cancer)
- **License:** FREE (CC0 Public Domain)
- **Source:** Community-curated
- **Evidence Levels:** A-E
- **Focus:** Global, multi-source
- **Coverage:** ~3000+ variants
- **Updates:** Continuous (community-driven)
- **API Key:** Not required
- **URL:** https://civicdb.org

### OncoKB (Precision Oncology Knowledge Base)
- **License:** COMMERCIAL (Free tier: 1000 requests/month)
- **Source:** MSK-curated
- **Evidence Levels:** 1-4, R1-R2
- **Focus:** US/FDA, clinical trials
- **Coverage:** ~5000+ variants
- **Updates:** Regular (curated team)
- **API Key:** Required for production use
- **URL:** https://www.oncokb.org

### ESCAT (ESMO Scale for Clinical Actionability)
- **License:** FREE (citation required)
- **Source:** ESMO guidelines
- **Evidence Levels:** 9 tiers (I-A through X)
- **Focus:** European/ESMO, EMA approval
- **Coverage:** ~50+ tier-classified alterations
- **Updates:** Annual (ESMO guidelines)
- **API Key:** Not required
- **Reference:** Mateo J, et al. Ann Oncol. 2018;29(9):1895-1902

## License Comparison

| Annotator | License Type | Cost | API Key | Best For |
|-----------|-------------|------|---------|----------|
| CIViC | FREE | Free (CC0) | No | Academic research, open data |
| OncoKB | COMMERCIAL | Free tier / Paid | Yes | US hospitals, FDA focus |
| ESCAT | FREE | Free | No | European hospitals, ESMO guidelines |

## Usage

### Quick Start - Free Sources Only (Default)

```python
from annotators.combined_annotator import CombinedAnnotator

# Default: CIViC + ESCAT (both free)
annotator = CombinedAnnotator()

result = annotator.annotate_variant('EGFR', 'L858R', 'NSCLC')
report = annotator.get_clinical_report(result)
```

### Preset Configurations

#### 1. Free Sources Only (CIViC + ESCAT)

```python
from annotators.combined_annotator import CombinedAnnotator
from annotators.annotator_config import AnnotatorConfig

config = AnnotatorConfig.free_only()
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- Academic research
- Testing/development
- Budget-constrained projects
- Maximum coverage with free data

**Output:**
```
Enabled annotators: CIViC, ESCAT
Sources: ['CIViC', 'ESCAT']
License: FREE
```

#### 2. ESCAT Only (European Standard)

```python
config = AnnotatorConfig.escat_only()
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- European hospitals
- ESMO guideline compliance
- EMA approval-focused decisions
- Italian/European clinical practice

**Output:**
```
Enabled annotators: ESCAT
Sources: ['ESCAT']
ESCAT Tier: I-A
```

#### 3. CIViC Only (Community-Curated)

```python
config = AnnotatorConfig.civic_only()
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- Maximum variant coverage
- Research publications
- Community-driven evidence
- Open-source projects

#### 4. OncoKB Only (US/FDA Standard)

```python
config = AnnotatorConfig.oncokb_only(api_key="your_oncokb_api_key")
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- US hospitals
- FDA approval-focused decisions
- NCCN guideline compliance
- Clinical trial matching

**Note:** Requires OncoKB API key from https://www.oncokb.org/apiAccess

#### 5. All Sources (Maximum Validation)

```python
config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- Molecular Tumor Boards
- High-stakes clinical decisions
- Triple-source validation
- Maximum evidence concordance

**Benefits:**
- 10% bonus if 2 sources agree
- 15% bonus if all 3 sources agree
- Cross-validation of evidence

**Output:**
```
Enabled annotators: CIViC, OncoKB, ESCAT
Sources: ['CIViC', 'OncoKB', 'ESCAT']
Actionability Score: 100 × 1.15 = 115 → capped at 100
```

#### 6. European Clinical (ESCAT + CIViC)

```python
config = AnnotatorConfig.european_clinical()
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- European hospitals
- ESMO guideline compliance
- Budget-conscious institutions
- Avoiding OncoKB licensing costs

**Output:**
```
Enabled annotators: ESCAT, CIViC
Sources: ['ESCAT', 'CIViC']
Prefer European standards: True
```

#### 7. US Clinical (OncoKB + CIViC)

```python
config = AnnotatorConfig.us_clinical(oncokb_api_key="your_key")
annotator = CombinedAnnotator(config=config)
```

**Best for:**
- US hospitals
- FDA approval-focused decisions
- NCCN guideline compliance

### Custom Configuration

```python
from annotators.annotator_config import AnnotatorConfig, AnnotatorType

# Create custom configuration
config = AnnotatorConfig()

# Enable/disable specific annotators
config.enable(AnnotatorType.CIVIC)
config.enable(AnnotatorType.ESCAT)
config.disable(AnnotatorType.ONCOKB)

# Set preferences
config.prefer_european_standards = True
config.enable_caching = True

annotator = CombinedAnnotator(config=config)
```

## Configuration Details

### Viewing Configuration Summary

```python
config = AnnotatorConfig.free_only()
print(config.summary())
```

**Output:**
```
======================================================================
CLINICAL ANNOTATOR CONFIGURATION
======================================================================

Enabled annotators: CIViC, ESCAT
Total sources: 2

Licensing Information:

  CIViC:
    License: free
    Cost: Free (CC0 Public Domain)
    Info: https://civicdb.org/about

  ESCAT:
    License: free
    Cost: Free (citation required)
    Info: https://www.esmo.org/guidelines/precision-medicine

Preferences:
  Prefer free sources: True
  Prefer European standards: False
  Enable caching: True

Validation:
  CIViC: ✓ Valid
  ESCAT: ✓ Valid

======================================================================
```

### Checking Enabled Annotators

```python
config = AnnotatorConfig.free_only()

# Check if specific annotator is enabled
if config.is_enabled(AnnotatorType.CIVIC):
    print("CIViC is enabled")

# Get list of enabled annotators
enabled = config.get_enabled_names()
print(f"Enabled: {enabled}")  # ['CIViC', 'ESCAT']
```

### License Validation

```python
config = AnnotatorConfig.all_sources(oncokb_api_key="demo_key")

# Validate licenses
validation = config.validate_licenses()
for annotator, status in validation.items():
    print(f"{annotator}: {status}")
```

**Output:**
```
OncoKB: ✓ Valid
CIViC: ✓ Valid
ESCAT: ✓ Valid
```

### Licensing Information

```python
config = AnnotatorConfig.free_only()

# Get licensing details
licensing = config.get_licensing_info()
for annotator, info in licensing.items():
    print(f"\n{annotator}:")
    print(f"  License: {info['license']}")
    print(f"  Cost: {info['cost']}")
    print(f"  Requires API Key: {info['requires_api_key']}")
    if info['license_url']:
        print(f"  Info: {info['license_url']}")
```

## Actionability Scoring

The combined annotator calculates an actionability score (0-100) based on evidence from enabled sources.

### Scoring Priority

1. **ESCAT** (European standard) - if enabled
2. **OncoKB** (US/FDA standard) - if enabled
3. **CIViC** (Community curated) - if enabled

### Tier/Level Scoring

| ESCAT Tier | OncoKB Level | CIViC Level | Score |
|------------|--------------|-------------|-------|
| I-A | LEVEL_1 | A | 100 |
| I-B | LEVEL_2 | B | 80-90 |
| I-C | - | - | 80 |
| II-A | LEVEL_3A | C | 60-70 |
| II-B | LEVEL_3B | D | 40-60 |
| III-A | - | - | 50 |
| IV | LEVEL_4 | E | 20-30 |
| X | R1/R2 | - | 0 |

### Concordance Bonus

- **2 sources agree:** +10% bonus
- **3 sources agree:** +15% bonus
- **Maximum score:** Capped at 100

### Actionability Threshold

**Actionable:** Score ≥ 50 (ESCAT Tier III-A or equivalent)

## Clinical Workflow Examples

### Example 1: European Hospital (Free Sources)

```python
from annotators.combined_annotator import CombinedAnnotator
from annotators.annotator_config import AnnotatorConfig

# Use ESCAT + CIViC (both free)
config = AnnotatorConfig.european_clinical()
annotator = CombinedAnnotator(config=config)

# Annotate variant
result = annotator.annotate_variant('EGFR', 'L858R', 'NSCLC')
report = annotator.get_clinical_report(result)

# Clinical report
print(f"Variant: {report['variant']}")
print(f"ESCAT Tier: {report['escat_classification']['tier']}")
print(f"Actionability: {report['actionability']['score']}/100")
print(f"FDA Drugs: {report['therapeutic_options']['fda_approved']}")
print(f"Recommendation: {report['recommendation']}")
```

**Output:**
```
Variant: EGFR L858R
ESCAT Tier: I-A
Actionability: 100/100
FDA Drugs: ['Osimertinib', 'Gefitinib', 'Erlotinib', 'Afatinib']
Recommendation: FDA-approved targeted therapy available: Osimertinib, Gefitinib, Erlotinib
```

### Example 2: US Hospital (OncoKB + CIViC)

```python
# Use OncoKB (paid) + CIViC (free)
config = AnnotatorConfig.us_clinical(oncokb_api_key="your_key")
annotator = CombinedAnnotator(config=config)

result = annotator.annotate_variant('BRAF', 'V600E', 'Melanoma')
report = annotator.get_clinical_report(result)

print(f"Oncogenic: {report['oncogenicity']['classification']}")
print(f"OncoKB Level: {report['actionability']['level']}")
print(f"Sources: {report['evidence_sources']}")
```

### Example 3: Molecular Tumor Board (All Sources)

```python
# Maximum validation with all three sources
config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")
annotator = CombinedAnnotator(config=config)

result = annotator.annotate_variant('KRAS', 'G12C', 'NSCLC')
report = annotator.get_clinical_report(result)

print(f"Evidence Sources: {report['evidence_sources']}")
print(f"Concordance Score: {report['actionability']['score']}/100")
print(f"ESCAT: {report['escat_classification']['tier']}")
print(f"Oncogenic: {report['oncogenicity']['classification']}")
```

**Output:**
```
Evidence Sources: ['CIViC', 'OncoKB', 'ESCAT']
Concordance Score: 100/100 (with 15% bonus)
ESCAT: I-A
Oncogenic: Oncogenic
```

## Migration Guide

### From Previous Version (Deprecated)

**Old usage:**
```python
# Deprecated: oncokb_token parameter
annotator = CombinedAnnotator(oncokb_token="your_key")
```

**New usage:**
```python
# Use AnnotatorConfig instead
from annotators.annotator_config import AnnotatorConfig

config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")
annotator = CombinedAnnotator(config=config)
```

**Note:** The `oncokb_token` parameter is deprecated but still supported for backward compatibility.

## OncoKB API Key Setup

### Getting an API Key

1. Visit https://www.oncokb.org/apiAccess
2. Register for an account (academic or commercial)
3. Request API token
4. Free tier: 1000 requests/month
5. Commercial: Contact MSK for licensing

### Using the API Key

```python
from annotators.annotator_config import AnnotatorConfig

# For production with OncoKB
config = AnnotatorConfig.all_sources(oncokb_api_key="your_actual_key_here")

# For testing without OncoKB
config = AnnotatorConfig.free_only()  # Uses CIViC + ESCAT
```

### Environment Variable (Optional)

```bash
export ONCOKB_API_KEY="your_key_here"
```

```python
import os
from annotators.annotator_config import AnnotatorConfig

oncokb_key = os.getenv('ONCOKB_API_KEY')
config = AnnotatorConfig.all_sources(oncokb_api_key=oncokb_key)
```

## Integration with MTBParser

```python
from core.mtb_parser import MTBParser
from annotators.combined_annotator import CombinedAnnotator
from annotators.annotator_config import AnnotatorConfig

# Parse MTB report
parser = MTBParser()
mtb_report = parser.parse_report(report_text)

# Configure annotator based on your needs
# Option 1: European hospital (free)
config = AnnotatorConfig.european_clinical()

# Option 2: US hospital (with OncoKB)
# config = AnnotatorConfig.us_clinical(oncokb_api_key="your_key")

# Option 3: Maximum validation
# config = AnnotatorConfig.all_sources(oncokb_api_key="your_key")

annotator = CombinedAnnotator(config=config)

# Annotate all variants
for variant in mtb_report.variants:
    result = annotator.annotate_variant(
        gene=variant.gene,
        variant=variant.protein_change or variant.cdna_change,
        tumor_type=mtb_report.diagnosis.primary_diagnosis
    )

    report = annotator.get_clinical_report(result)

    print(f"\nVariant: {report['variant']}")
    print(f"Actionability: {report['actionability']['score']}/100")
    print(f"ESCAT Tier: {report['escat_classification']['tier']}")
    print(f"Sources: {', '.join(report['evidence_sources'])}")
    print(f"Drugs: {report['therapeutic_options']['fda_approved']}")
```

## Testing

### Test All Configurations

```bash
python3 annotators/annotator_config.py
```

### Test Specific Configuration

```python
from annotators.combined_annotator import CombinedAnnotator
from annotators.annotator_config import AnnotatorConfig

# Test free sources
config = AnnotatorConfig.free_only()
print(config.summary())

annotator = CombinedAnnotator(config=config)
result = annotator.annotate_variant('EGFR', 'L858R', 'NSCLC')
report = annotator.get_clinical_report(result)

assert 'CIViC' in report['evidence_sources']
assert 'ESCAT' in report['evidence_sources']
assert 'OncoKB' not in report['evidence_sources']
print("✓ Test passed")
```

## Compliance & Legal

### GDPR Compliance
- No patient data is sent to external APIs
- All processing is local (mock data mode)
- CIViC/ESCAT: No API calls in current implementation
- OncoKB: Would require API calls (use with GDPR-compliant setup)

### Medical Device Regulation
- **Not a medical device**
- Decision support tool only
- Requires clinical validation
- Use under medical supervision

### Required Citations

**For ESCAT:**
> Mateo J, et al. A framework to rank genomic alterations as targets for cancer precision medicine: the ESMO Scale for Clinical Actionability of molecular Targets (ESCAT). Ann Oncol. 2018;29(9):1895-1902.

**For CIViC:**
> Griffith M, et al. CIViC is a community knowledgebase for expert crowdsourcing the clinical interpretation of variants in cancer. Nat Genet. 2017;49(2):170-174.

**For OncoKB:**
> Chakravarty D, et al. OncoKB: A Precision Oncology Knowledge Base. JCO Precis Oncol. 2017;2017:PO.17.00011.

## Troubleshooting

### Warning: OncoKB enabled but no API key

```
UserWarning: OncoKB is enabled but no API key provided. Using mock data.
```

**Solution:** Either provide API key or use free-only configuration:
```python
config = AnnotatorConfig.free_only()
```

### No evidence found

If all annotators return no evidence, the report will show:
```python
{
    'actionability_score': 0.0,
    'is_actionable': False,
    'evidence_sources': [],
    'recommendation': 'No high-level evidence for targeted therapy'
}
```

**Solution:** Check variant notation and tumor type spelling.

### Different scores from different sources

This is expected. The combined annotator takes the **highest** score from all enabled sources, then applies concordance bonus.

## References

- **CIViC:** https://civicdb.org
- **OncoKB:** https://www.oncokb.org
- **ESCAT:** https://www.esmo.org/guidelines/precision-medicine
- **MTBParser:** See repository README

---

**Implementation:** MTBParser System v1.1.0
**Date:** 2025-10-22
**Contact:** See repository for updates
