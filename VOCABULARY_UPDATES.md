# Vocabulary Update System - Complete Guide

**Version**: 1.0  
**Date**: October 22, 2025  
**Status**: ✅ Operational

---

## 📋 Overview

The MTBParser vocabulary update system provides **automatic updates from external APIs** for controlled vocabularies, ensuring that gene nomenclature, drug codes, and clinical terminology remain current with international standards.

### Supported Vocabularies

| Vocabulary | API Source | Auto-Update | Manual Update |
|------------|-----------|-------------|---------------|
| **HGNC** | HGNC REST API | ✅ Yes | ✅ Yes |
| **RxNorm** | NLM RxNorm API | ✅ Yes | ✅ Yes |
| **ICD-O** | Manual | ❌ No | ✅ Yes |
| **SNOMED-CT** | Manual | ❌ No | ✅ Yes |
| **LOINC** | Manual | ❌ No | ✅ Yes |

---

## 🏗️ System Architecture

```
MTBParser/
├── updaters/
│   ├── __init__.py
│   ├── base_updater.py         # Abstract base class
│   ├── hgnc_updater.py          # HGNC gene updater
│   ├── rxnorm_updater.py        # RxNorm drug updater
│   └── update_manager.py        # Centralized manager
├── vocabularies/
│   ├── hgnc_genes.json
│   ├── rxnorm_drugs.json
│   ├── backups/                 # Auto-created backup directory
│   └── update_history.json      # Update log
└── update_vocabularies.py       # CLI tool
```

### Key Components

1. **VocabularyUpdater** (base_updater.py)
   - Abstract base class for all updaters
   - Backup/rollback functionality
   - Version control
   - Change tracking

2. **HGNCUpdater** (hgnc_updater.py)
   - Fetches gene data from HGNC REST API
   - Updates 37 cancer-relevant genes
   - Includes HGNC IDs, aliases, Entrez IDs, Ensembl IDs

3. **RxNormUpdater** (rxnorm_updater.py)
   - Fetches drug data from NLM RxNorm API
   - Updates 26+ oncology targeted therapies
   - Includes RxCUI codes, targets, indications

4. **UpdateManager** (update_manager.py)
   - Centralized management of all updaters
   - Update history tracking
   - Batch updates

5. **CLI Tool** (update_vocabularies.py)
   - User-friendly command-line interface
   - Status, update, history, backup commands

---

## 🚀 Quick Start

### Installation

The update system requires the `requests` library:

```bash
pip3 install requests
```

### Basic Usage

```bash
# Check vocabulary status
python3 update_vocabularies.py status

# Update all vocabularies (dry run first)
python3 update_vocabularies.py update all --dry-run

# Update all vocabularies (for real)
python3 update_vocabularies.py update all

# Update specific vocabulary
python3 update_vocabularies.py update hgnc
```

---

## 📚 CLI Commands Reference

### 1. Status

Show current status of all vocabularies:

```bash
python3 update_vocabularies.py status
```

**Output:**
```
📊 VOCABULARY STATUS
🔹 HGNC
   File: hgnc_genes.json
   Last Updated: 2025-10-22
   Version: 1.0
   Items: 37
```

### 2. Update

Update vocabularies from external APIs:

```bash
# Dry run (no changes saved)
python3 update_vocabularies.py update all --dry-run
python3 update_vocabularies.py update hgnc --dry-run

# Real update
python3 update_vocabularies.py update all
python3 update_vocabularies.py update rxnorm
```

**Features:**
- ✅ Automatic backup before update
- ✅ Change tracking (added/modified/removed items)
- ✅ Error handling with detailed logs
- ✅ Dry run mode for testing

### 3. History

View update history:

```bash
# Show last 10 updates (all vocabularies)
python3 update_vocabularies.py history

# Filter by vocabulary
python3 update_vocabularies.py history --vocabulary hgnc

# Show last 20 updates
python3 update_vocabularies.py history --limit 20
```

**Output:**
```
📜 UPDATE HISTORY
🕒 2025-10-22 14:30:00 - HGNC
   File: hgnc_genes.json
   Changes: +2 / ~5 / -0
```

### 4. Backups

List available backups:

```bash
python3 update_vocabularies.py backups hgnc
python3 update_vocabularies.py backups rxnorm
```

**Output:**
```
💾 BACKUPS - HGNC
📦 hgnc_genes_20251022_143000.json
   Created: 2025-10-22 14:30:00
   Size: 15.2 KB
```

### 5. Rollback

Revert to a previous version:

```bash
# Rollback to most recent backup (with confirmation)
python3 update_vocabularies.py rollback hgnc

# Rollback without confirmation
python3 update_vocabularies.py rollback hgnc --yes
```

**Safety Features:**
- ✅ Shows available backups before rollback
- ✅ Confirmation prompt (unless --yes flag)
- ✅ Current version backed up before rollback

### 6. Clean

Remove old backups to save space:

```bash
# Clean all vocabularies, keep last 5 backups
python3 update_vocabularies.py clean all --keep 5

# Clean specific vocabulary
python3 update_vocabularies.py clean hgnc --keep 3

# Skip confirmation
python3 update_vocabularies.py clean all --keep 5 --yes
```

---

## 🔌 API Integration Details

### HGNC API

**Endpoint**: `https://rest.genenames.org/fetch/symbol/{gene_symbol}`

**Rate Limiting**: 10 requests/second (0.1s delay between requests)

**Data Fetched**:
- HGNC ID (e.g., HGNC:3236)
- Gene name
- Chromosome location
- Aliases and previous symbols
- Entrez ID, Ensembl ID, UniProt IDs
- Gene groups

**Example Request**:
```bash
curl -H "Accept: application/json" \
  https://rest.genenames.org/fetch/symbol/EGFR
```

**Cancer Genes List** (37 genes):
```
EGFR, KRAS, BRAF, ALK, ROS1, RET, MET, NTRK1, ERBB2, PIK3CA, AKT1, PTEN,
TP53, BRCA1, BRCA2, ATM, PALB2, CHEK2, FGFR1-4, CDK4, CDKN2A, MDM2, KIT,
PDGFRA, NF1, APC, MLH1, MSH2, MSH6, PMS2, EPCAM, STK11, VHL, TSC1, TSC2
```

### RxNorm API

**Endpoint**: `https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}`

**Rate Limiting**: 5 requests/second (0.2s delay between requests)

**Data Fetched**:
- RxCUI (RxNorm Concept Unique Identifier)
- Drug name (generic)
- Drug properties

**Example Request**:
```bash
curl "https://rxnav.nlm.nih.gov/REST/rxcui.json?name=osimertinib"
```

**Oncology Drugs List** (26+ drugs):
```
osimertinib, afatinib, erlotinib, gefitinib, amivantamab (EGFR)
sotorasib, adagrasib (KRAS)
dabrafenib, vemurafenib, trametinib (BRAF/MEK)
crizotinib, alectinib, brigatinib, lorlatinib (ALK)
entrectinib, larotrectinib (NTRK)
selpercatinib, pralsetinib (RET)
capmatinib, tepotinib (MET)
erdafitinib, pemigatinib (FGFR)
olaparib, rucaparib, niraparib, talazoparib (PARP)
pembrolizumab, nivolumab, atezolizumab (PD-1/PD-L1)
trastuzumab, pertuzumab (HER2)
imatinib, sunitinib, sorafenib (multi-kinase)
```

---

## 🔒 Safety Features

### 1. Automatic Backups

**Before every update**, the current vocabulary is automatically backed up:

```
vocabularies/backups/hgnc_genes_20251022_143000.json
```

**Backup naming convention**: `{vocabulary}_{YYYYMMDD}_{HHMMSS}.json`

### 2. Dry Run Mode

Test updates without making changes:

```bash
python3 update_vocabularies.py update all --dry-run
```

**Benefits**:
- ✅ See what would change
- ✅ Detect API errors before committing
- ✅ Review added/modified/removed items

### 3. Change Tracking

Every update logs detailed changes:

```json
{
  "added": ["IDH1", "IDH2"],
  "modified": ["EGFR", "KRAS"],
  "removed": [],
  "unchanged": 33
}
```

### 4. Update History

All updates logged to `vocabularies/update_history.json`:

```json
[
  {
    "vocabulary": "hgnc",
    "timestamp": "2025-10-22T14:30:00",
    "changes": {...},
    "filename": "hgnc_genes.json"
  }
]
```

### 5. Rollback Capability

Quickly revert to any previous backup:

```bash
python3 update_vocabularies.py rollback hgnc
```

---

## 🛠️ Advanced Usage

### Programmatic Use

```python
from updaters.update_manager import UpdateManager

# Initialize manager
manager = UpdateManager()

# Check status
status = manager.get_update_status()
print(status['hgnc'])

# Update vocabulary
result = manager.update_vocabulary('hgnc', dry_run=False)

if result['success']:
    changes = result['changes']
    print(f"Added: {len(changes['added'])}")
    print(f"Modified: {len(changes['modified'])}")

# View history
history = manager.get_update_history('hgnc', limit=5)

# Rollback if needed
manager.rollback('hgnc')
```

### Custom Gene List Update

```python
from updaters.hgnc_updater import HGNCUpdater

updater = HGNCUpdater()

# Update only specific genes
result = updater.update_specific_genes(['NTRK1', 'NTRK2', 'NTRK3'])
```

### Extending the System

To add a new vocabulary updater:

1. Create new updater class inheriting from `VocabularyUpdater`
2. Implement required methods:
   - `fetch_data()` - Fetch from API
   - `transform_data()` - Transform to vocabulary format
   - `get_vocabulary_filename()` - Return filename

```python
from updaters.base_updater import VocabularyUpdater

class MyUpdater(VocabularyUpdater):
    def get_vocabulary_filename(self):
        return 'my_vocabulary.json'
    
    def fetch_data(self):
        # Fetch from external API
        return raw_data
    
    def transform_data(self, raw_data):
        # Transform to standard format
        return {
            'metadata': {...},
            'items': {...}
        }
```

3. Register in `UpdateManager`:

```python
self.updaters['my_vocab'] = MyUpdater(vocab_dir)
```

---

## 📅 Recommended Update Schedule

### Production Environment

- **HGNC Genes**: Monthly (genes change infrequently)
- **RxNorm Drugs**: Quarterly (new drug approvals)
- **Manual Vocabularies** (ICD-O, SNOMED-CT, LOINC): Annually

### Development/Testing

- **Before major releases**: Update all vocabularies
- **After API changes**: Test with dry run first

### Automation

Set up cron job for automated updates:

```bash
# Update vocabularies first Monday of every month at 2 AM
0 2 1-7 * 1 cd /path/to/MTBParser && python3 update_vocabularies.py update all
```

---

## ⚠️ Troubleshooting

### API Connection Issues

**Problem**: `Request error: Connection timeout`

**Solution**:
1. Check internet connection
2. Verify API endpoint is accessible
3. Retry with increased timeout
4. Use dry run to test

### No Changes Detected

**Problem**: Update shows 0 changes

**Possible reasons**:
- Vocabulary is already up-to-date
- API returned same data
- No new genes/drugs in curated list

### Backup Directory Full

**Problem**: Too many backups consuming disk space

**Solution**:
```bash
# Keep only last 3 backups
python3 update_vocabularies.py clean all --keep 3 --yes
```

### Failed Update Recovery

**Problem**: Update failed mid-process

**Solution**:
```bash
# Rollback to last known good version
python3 update_vocabularies.py rollback hgnc --yes

# Check status
python3 update_vocabularies.py status
```

---

## 📊 Update System Metrics

### Performance

- **HGNC Update**: ~10-15 seconds (37 genes, 10 req/sec)
- **RxNorm Update**: ~10-15 seconds (26+ drugs, 5 req/sec)
- **Backup Creation**: <1 second
- **Rollback**: <1 second

### Storage

- **Vocabulary File**: ~10-20 KB each
- **Backup File**: Same as vocabulary
- **Recommended Backups**: Keep last 5 (×2 = 10 backups = ~200 KB)

---

## 🔗 External Resources

### Official APIs

- **HGNC**: https://www.genenames.org/help/rest/
- **RxNorm**: https://lhncbc.nlm.nih.gov/RxNav/APIs/
- **LOINC**: https://loinc.org/downloads/
- **SNOMED-CT**: https://www.snomed.org/

### Documentation

- **FHIR Terminology**: https://www.hl7.org/fhir/terminologies.html
- **GA4GH Standards**: https://www.ga4gh.org/
- **OMOP Vocabularies**: https://athena.ohdsi.org/

---

## ✅ Best Practices

1. **Always dry run first**: Test updates before applying
2. **Review changes**: Check added/modified/removed items
3. **Keep backups**: Maintain at least 5 recent backups
4. **Monitor history**: Review update logs regularly
5. **Test after update**: Run integration tests
6. **Document changes**: Note significant updates in changelog

---

## 📝 Change Log

### Version 1.0 (2025-10-22)
- ✅ Initial release
- ✅ HGNC updater with REST API integration
- ✅ RxNorm updater with REST API integration
- ✅ UpdateManager for centralized control
- ✅ CLI tool with 6 commands
- ✅ Automatic backup/rollback system
- ✅ Update history tracking
- ✅ Change detection and logging

---

**Status**: ✅ **FULLY OPERATIONAL**

The vocabulary update system is production-ready and actively maintains gene and drug nomenclature standards for the MTBParser system.
