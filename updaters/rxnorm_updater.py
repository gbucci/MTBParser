#!/usr/bin/env python3
"""
RxNorm Updater - Updates drug vocabulary from RxNorm API
API Documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from .base_updater import VocabularyUpdater


class RxNormUpdater(VocabularyUpdater):
    """
    Updates RxNorm drug vocabulary from NLM RxNorm API
    """

    def __init__(self, vocab_dir: Optional[str] = None, backup_dir: Optional[str] = None):
        super().__init__(vocab_dir, backup_dir)
        self.base_url = "https://rxnav.nlm.nih.gov/REST"
        
        # Targeted oncology therapies to fetch
        self.oncology_drugs = [
            'osimertinib', 'afatinib', 'erlotinib', 'gefitinib', 'amivantamab',
            'sotorasib', 'adagrasib', 'dabrafenib', 'vemurafenib', 'trametinib',
            'encorafenib', 'binimetinib', 'crizotinib', 'alectinib', 'brigatinib',
            'lorlatinib', 'entrectinib', 'larotrectinib', 'selpercatinib',
            'pralsetinib', 'capmatinib', 'tepotinib', 'erdafitinib', 'pemigatinib',
            'olaparib', 'rucaparib', 'niraparib', 'talazoparib', 'pembrolizumab',
            'nivolumab', 'atezolizumab', 'durvalumab', 'ipilimumab', 'trastuzumab',
            'pertuzumab', 'trastuzumab-deruxtecan', 'imatinib', 'sunitinib',
            'sorafenib'
        ]

        # Gene targets for drugs (manual curation)
        self.drug_targets = {
            'osimertinib': ['EGFR'], 'afatinib': ['EGFR'], 'erlotinib': ['EGFR'],
            'gefitinib': ['EGFR'], 'amivantamab': ['EGFR', 'MET'],
            'sotorasib': ['KRAS'], 'adagrasib': ['KRAS'],
            'dabrafenib': ['BRAF'], 'vemurafenib': ['BRAF'], 'trametinib': ['MEK1', 'MEK2'],
            'encorafenib': ['BRAF'], 'binimetinib': ['MEK1', 'MEK2'],
            'crizotinib': ['ALK', 'ROS1', 'MET'], 'alectinib': ['ALK'], 'brigatinib': ['ALK'],
            'lorlatinib': ['ALK', 'ROS1'], 'entrectinib': ['NTRK1', 'NTRK2', 'NTRK3', 'ROS1', 'ALK'],
            'larotrectinib': ['NTRK1', 'NTRK2', 'NTRK3'], 'selpercatinib': ['RET'],
            'pralsetinib': ['RET'], 'capmatinib': ['MET'], 'tepotinib': ['MET'],
            'erdafitinib': ['FGFR1', 'FGFR2', 'FGFR3', 'FGFR4'], 'pemigatinib': ['FGFR1', 'FGFR2', 'FGFR3'],
            'olaparib': ['PARP'], 'rucaparib': ['PARP'], 'niraparib': ['PARP'], 'talazoparib': ['PARP'],
            'pembrolizumab': ['PD-1'], 'nivolumab': ['PD-1'], 'atezolizumab': ['PD-L1'],
            'durvalumab': ['PD-L1'], 'ipilimumab': ['CTLA-4'],
            'trastuzumab': ['ERBB2'], 'pertuzumab': ['ERBB2'], 'trastuzumab-deruxtecan': ['ERBB2'],
            'imatinib': ['BCR-ABL', 'KIT', 'PDGFRA'], 'sunitinib': ['VEGFR', 'PDGFR', 'KIT'],
            'sorafenib': ['VEGFR', 'RAF']
        }

        # Indications (manual curation)
        self.drug_indications = {
            'osimertinib': 'NSCLC with EGFR T790M',
            'afatinib': 'NSCLC with EGFR exon 19 del or L858R',
            'sotorasib': 'NSCLC with KRAS G12C',
            'dabrafenib': 'Melanoma with BRAF V600E/K',
            'vemurafenib': 'Melanoma with BRAF V600E',
            'crizotinib': 'NSCLC with ALK or ROS1 rearrangement',
            'erdafitinib': 'Urothelial cancer with FGFR2/3 alterations',
            'olaparib': 'Ovarian/breast/pancreatic cancer with BRCA1/2 mutations',
            'pembrolizumab': 'Various cancers with high MSI/TMB',
            'trastuzumab': 'HER2+ breast/gastric cancer'
        }

    def get_vocabulary_filename(self) -> str:
        return 'rxnorm_drugs.json'

    def fetch_data(self) -> Dict:
        """
        Fetch drug data from RxNorm API

        Returns:
            Dictionary with drug data
        """
        drugs_data = {}
        total = len(self.oncology_drugs)
        
        self._log(f"Fetching {total} oncology drugs from RxNorm API...")

        for i, drug_name in enumerate(self.oncology_drugs, 1):
            try:
                self._log(f"[{i}/{total}] Fetching {drug_name}...")
                drug_info = self._fetch_drug(drug_name)
                
                if drug_info:
                    drugs_data[drug_name] = drug_info
                    time.sleep(0.2)  # Rate limiting
                else:
                    self._log(f"  Warning: No RxNorm code found for {drug_name}")

            except Exception as e:
                self._log(f"  Error fetching {drug_name}: {e}")
                continue

        self._log(f"Successfully fetched {len(drugs_data)}/{total} drugs")
        return drugs_data

    def _fetch_drug(self, drug_name: str) -> Optional[Dict]:
        """
        Fetch single drug from RxNorm API

        Args:
            drug_name: Drug name (generic)

        Returns:
            Drug information dictionary
        """
        # Search for drug
        search_url = f"{self.base_url}/rxcui.json"
        params = {'name': drug_name}
        
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                rxnorm_ids = data['idGroup']['rxnormId']
                if rxnorm_ids:
                    rxcui = rxnorm_ids[0]  # Take first result
                    
                    # Get additional info
                    properties = self._get_drug_properties(rxcui)
                    
                    return {
                        'rxcui': rxcui,
                        'name': drug_name,
                        'properties': properties
                    }
            
            return None

        except requests.exceptions.RequestException as e:
            self._log(f"  Request error for {drug_name}: {e}")
            return None

    def _get_drug_properties(self, rxcui: str) -> Dict:
        """
        Get drug properties from RxNorm

        Args:
            rxcui: RxNorm concept unique identifier

        Returns:
            Drug properties
        """
        url = f"{self.base_url}/rxcui/{rxcui}/properties.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'properties' in data:
                return data['properties']
            
        except:
            pass
        
        return {}

    def transform_data(self, raw_data: Dict) -> Dict:
        """
        Transform RxNorm API data to vocabulary format

        Args:
            raw_data: Raw data from RxNorm API

        Returns:
            Transformed vocabulary structure
        """
        drugs = {}

        for drug_name, drug_info in raw_data.items():
            rxcui = drug_info.get('rxcui', '')
            
            drugs[drug_name] = {
                'code': str(rxcui),
                'system': 'RxNorm',
                'display': drug_name,
                'target': self.drug_targets.get(drug_name, []),
                'indication': self.drug_indications.get(drug_name, 'Various oncology indications'),
                'evidence_level': 'FDA Approved',  # Assume FDA approved for this list
                'rxcui': rxcui,
                'properties': drug_info.get('properties', {})
            }

        # Create vocabulary structure
        vocabulary = {
            'metadata': {
                'version': '2.0',
                'system': 'RxNorm',
                'description': 'RxNorm codes for targeted oncology therapies',
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'NLM RxNorm',
                'total_drugs': len(drugs),
                'guidelines': {
                    'AIOM': 'Associazione Italiana di Oncologia Medica',
                    'NCCN': 'National Comprehensive Cancer Network',
                    'AMP-ASCO-CAP': 'Standards and Guidelines for Interpretation of Sequence Variants'
                }
            },
            'drugs': drugs
        }

        return vocabulary


# Example usage
if __name__ == "__main__":
    updater = RxNormUpdater()
    
    print("="*80)
    print("RxNorm Drug Vocabulary Updater")
    print("="*80)
    
    # Dry run
    print("\n🔍 Running dry run...")
    result = updater.update(dry_run=True)
    
    print(f"\n📊 Update Result:")
    print(f"  Success: {result['success']}")
    print(f"  Filename: {result['filename']}")
    
    if result['success']:
        response = input("\n💾 Save changes? (y/n): ")
        if response.lower() == 'y':
            final_result = updater.update(dry_run=False)
            print(f"✅ Update complete")
