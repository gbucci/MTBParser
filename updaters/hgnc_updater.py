#!/usr/bin/env python3
"""
HGNC Updater - Updates gene vocabulary from HGNC REST API
API Documentation: https://www.genenames.org/help/rest/
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from .base_updater import VocabularyUpdater


class HGNCUpdater(VocabularyUpdater):
    """
    Updates HGNC gene vocabulary from official HGNC REST API
    """

    def __init__(self, vocab_dir: Optional[str] = None, backup_dir: Optional[str] = None):
        super().__init__(vocab_dir, backup_dir)
        self.base_url = "https://rest.genenames.org"
        self.headers = {'Accept': 'application/json'}
        
        # Cancer-relevant genes to fetch
        self.cancer_genes = [
            'EGFR', 'KRAS', 'BRAF', 'ALK', 'ROS1', 'RET', 'MET', 'NTRK1',
            'ERBB2', 'PIK3CA', 'AKT1', 'PTEN', 'TP53', 'BRCA1', 'BRCA2',
            'ATM', 'PALB2', 'CHEK2', 'FGFR1', 'FGFR2', 'FGFR3', 'FGFR4',
            'CDK4', 'CDKN2A', 'MDM2', 'KIT', 'PDGFRA', 'NF1', 'APC',
            'MLH1', 'MSH2', 'MSH6', 'PMS2', 'EPCAM', 'STK11', 'VHL',
            'TSC1', 'TSC2'
        ]
        
        # Actionable genes (with approved targeted therapies)
        self.actionable_genes = [
            'EGFR', 'KRAS', 'BRAF', 'ALK', 'ROS1', 'RET', 'MET',
            'NTRK1', 'BRCA1', 'BRCA2', 'PIK3CA', 'FGFR1', 'FGFR2',
            'FGFR3', 'ERBB2', 'KIT', 'PDGFRA', 'IDH1', 'IDH2', 'NF1',
            'ATM', 'PALB2'
        ]

    def get_vocabulary_filename(self) -> str:
        return 'hgnc_genes.json'

    def fetch_data(self) -> Dict:
        """
        Fetch gene data from HGNC REST API

        Returns:
            Dictionary with gene data
        """
        genes_data = {}
        total = len(self.cancer_genes)
        
        self._log(f"Fetching {total} cancer-relevant genes from HGNC API...")

        for i, gene_symbol in enumerate(self.cancer_genes, 1):
            try:
                self._log(f"[{i}/{total}] Fetching {gene_symbol}...")
                gene_info = self._fetch_gene(gene_symbol)
                
                if gene_info:
                    genes_data[gene_symbol] = gene_info
                    time.sleep(0.1)  # Rate limiting: 10 requests/second
                else:
                    self._log(f"  Warning: No data for {gene_symbol}")

            except Exception as e:
                self._log(f"  Error fetching {gene_symbol}: {e}")
                continue

        self._log(f"Successfully fetched {len(genes_data)}/{total} genes")
        return genes_data

    def _fetch_gene(self, symbol: str) -> Optional[Dict]:
        """
        Fetch single gene from HGNC API

        Args:
            symbol: Gene symbol (e.g., 'EGFR')

        Returns:
            Gene information dictionary
        """
        url = f"{self.base_url}/fetch/symbol/{symbol}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'response' in data and 'docs' in data['response']:
                docs = data['response']['docs']
                if docs:
                    return docs[0]  # Return first match
            
            return None

        except requests.exceptions.RequestException as e:
            self._log(f"  Request error for {symbol}: {e}")
            return None

    def transform_data(self, raw_data: Dict) -> Dict:
        """
        Transform HGNC API data to vocabulary format

        Args:
            raw_data: Raw data from HGNC API

        Returns:
            Transformed vocabulary structure
        """
        genes = {}

        for symbol, gene_info in raw_data.items():
            # Extract relevant fields
            hgnc_id = gene_info.get('hgnc_id', '').replace('HGNC:', '')
            
            genes[symbol] = {
                'code': f"HGNC:{hgnc_id}",
                'system': 'http://www.genenames.org',
                'name': gene_info.get('name', ''),
                'chromosome': gene_info.get('location', '').split('p')[0].split('q')[0] if 'location' in gene_info else '',
                'cancer_types': self._get_cancer_types(symbol),
                'actionable': symbol in self.actionable_genes,
                'aliases': gene_info.get('alias_symbol', []),
                'prev_symbols': gene_info.get('prev_symbol', []),
                'location': gene_info.get('location', ''),
                'gene_group': gene_info.get('gene_group', []),
                'entrez_id': gene_info.get('entrez_id', ''),
                'ensembl_id': gene_info.get('ensembl_gene_id', ''),
                'uniprot_ids': gene_info.get('uniprot_ids', [])
            }

        # Create vocabulary structure
        vocabulary = {
            'metadata': {
                'version': '2.0',
                'system': 'HGNC',
                'description': 'HUGO Gene Nomenclature Committee - Cancer-relevant genes',
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'https://www.genenames.org',
                'total_genes': len(genes),
                'actionable_genes': len([g for g in genes.values() if g['actionable']]),
                'api_version': 'REST API v1'
            },
            'genes': genes
        }

        return vocabulary

    def _get_cancer_types(self, symbol: str) -> List[str]:
        """
        Get associated cancer types for a gene
        (Manual curation based on oncology knowledge)

        Args:
            symbol: Gene symbol

        Returns:
            List of cancer types
        """
        cancer_type_map = {
            'EGFR': ['NSCLC', 'Glioblastoma', 'Colorectal'],
            'KRAS': ['NSCLC', 'Colorectal', 'Pancreatic'],
            'BRAF': ['Melanoma', 'Colorectal', 'Thyroid'],
            'ALK': ['NSCLC', 'Neuroblastoma', 'Lymphoma'],
            'ROS1': ['NSCLC', 'Glioblastoma'],
            'RET': ['Thyroid', 'NSCLC', 'MEN'],
            'MET': ['NSCLC', 'Gastric', 'Renal'],
            'NTRK1': ['Various solid tumors'],
            'ERBB2': ['Breast', 'Gastric', 'NSCLC'],
            'PIK3CA': ['Breast', 'Colorectal', 'Endometrial'],
            'BRCA1': ['Breast', 'Ovarian', 'Pancreatic'],
            'BRCA2': ['Breast', 'Ovarian', 'Pancreatic', 'Prostate'],
            'TP53': ['Various cancers'],
            'PTEN': ['Prostate', 'Endometrial', 'Glioblastoma'],
            'ATM': ['Breast', 'Pancreatic', 'Prostate'],
            'FGFR1': ['Breast', 'NSCLC'],
            'FGFR2': ['Cholangiocarcinoma', 'Gastric', 'Endometrial'],
            'FGFR3': ['Bladder', 'Multiple myeloma'],
            'KIT': ['GIST', 'Melanoma', 'AML'],
            'PDGFRA': ['GIST', 'Glioblastoma'],
            'MLH1': ['Colorectal', 'Endometrial', 'Lynch syndrome'],
            'MSH2': ['Colorectal', 'Endometrial', 'Lynch syndrome'],
            'VHL': ['Renal cell carcinoma']
        }
        
        return cancer_type_map.get(symbol, ['Various cancers'])

    def update_specific_genes(self, gene_symbols: List[str]) -> Dict:
        """
        Update only specific genes

        Args:
            gene_symbols: List of gene symbols to update

        Returns:
            Update result
        """
        # Temporarily override cancer_genes list
        original_genes = self.cancer_genes
        self.cancer_genes = gene_symbols
        
        # Run update
        result = self.update(dry_run=False)
        
        # Restore original list
        self.cancer_genes = original_genes
        
        return result


# Example usage
if __name__ == "__main__":
    updater = HGNCUpdater()
    
    print("="*80)
    print("HGNC Gene Vocabulary Updater")
    print("="*80)
    
    # Dry run first
    print("\n🔍 Running dry run...")
    result = updater.update(dry_run=True)
    
    print(f"\n📊 Update Result:")
    print(f"  Success: {result['success']}")
    print(f"  Filename: {result['filename']}")
    print(f"  Timestamp: {result['timestamp']}")
    
    if result.get('changes'):
        changes = result['changes']
        if 'new_file' not in changes:
            print(f"\n📈 Changes:")
            print(f"  Added: {len(changes.get('added', []))}")
            print(f"  Modified: {len(changes.get('modified', []))}")
            print(f"  Removed: {len(changes.get('removed', []))}")
            print(f"  Unchanged: {changes.get('unchanged', 0)}")
    
    if result.get('errors'):
        print(f"\n❌ Errors:")
        for error in result['errors']:
            print(f"  • {error}")
    
    # Ask for confirmation
    if result['success']:
        response = input("\n💾 Save changes? (y/n): ")
        if response.lower() == 'y':
            print("\n📥 Updating vocabulary...")
            final_result = updater.update(dry_run=False)
            print(f"✅ Update complete: {final_result['filename']}")
        else:
            print("❌ Update cancelled")
