#!/usr/bin/env python3
"""
NGS Panel Definitions - Common oncology gene panels
"""

from typing import Dict, List

# Standard NGS panels used in oncology
NGS_PANELS = {
    "FoundationOne CDx": {
        "description": "Comprehensive genomic profiling - 324 genes",
        "genes": [
            "ABL1", "ACVR1B", "AKT1", "AKT2", "AKT3", "ALK", "ALOX12B", "AMER1", "APC", "AR",
            "ARAF", "ARFRP1", "ARID1A", "ARID1B", "ARID2", "ASXL1", "ATM", "ATR", "ATRX", "AURKA",
            "AURKB", "AXIN1", "AXL", "BAP1", "BARD1", "BCL2", "BCL2L1", "BCL2L11", "BCL2L2", "BCL6",
            "BCOR", "BCORL1", "BRAF", "BRCA1", "BRCA2", "BRD4", "BRIP1", "BTK", "C11orf30", "CALR",
            "CARD11", "CASP8", "CBFB", "CBL", "CCND1", "CCND2", "CCND3", "CCNE1", "CD274", "CD79A",
            "CD79B", "CDC73", "CDH1", "CDK12", "CDK4", "CDK6", "CDK8", "CDKN1A", "CDKN1B", "CDKN2A",
            "CDKN2B", "CDKN2C", "CEBPA", "CHEK1", "CHEK2", "CIC", "CREBBP", "CRKL", "CRLF2", "CSF1R",
            "CTCF", "CTLA4", "CTNNB1", "CUL3", "CYLD", "DAXX", "DDR2", "DICER1", "DIS3", "DNMT3A",
            "DOT1L", "EGFR", "EP300", "EPCAM", "EPHA3", "EPHA5", "EPHB1", "ERBB2", "ERBB3", "ERBB4",
            "ERCC2", "ERCC3", "ERCC4", "ERCC5", "ERG", "ESR1", "ETV1", "ETV4", "ETV5", "ETV6",
            "EWSR1", "EZH2", "FAM46C", "FANCA", "FANCC", "FANCD2", "FANCE", "FANCF", "FANCG", "FANCL",
            "FAS", "FBXW7", "FGF10", "FGF14", "FGF19", "FGF23", "FGF3", "FGF4", "FGF6", "FGFR1",
            "FGFR2", "FGFR3", "FGFR4", "FH", "FLCN", "FLT1", "FLT3", "FLT4", "FOXL2", "FOXP1",
            "GATA1", "GATA2", "GATA3", "GID4", "GNA11", "GNA13", "GNAQ", "GNAS", "GPR124", "GRIN2A",
            "GRM3", "GSK3B", "H3F3A", "HGF", "HIST1H1C", "HIST1H2BD", "HIST1H3B", "HNF1A", "HRAS",
            "IDH1", "IDH2", "IFNGR1", "IGF1R", "IGF2", "IKBKE", "IKZF1", "IL7R", "INHBA", "INPP4B",
            "IRF2", "IRF4", "IRS2", "JAK1", "JAK2", "JAK3", "JUN", "KDM5A", "KDM5C", "KDM6A",
            "KDR", "KEAP1", "KIT", "KLHL6", "KMT2A", "KMT2C", "KMT2D", "KRAS", "LATS1", "LATS2",
            "LMO1", "LYN", "MAGI2", "MAP2K1", "MAP2K2", "MAP2K4", "MAP3K1", "MAP3K13", "MAPK1", "MAX",
            "MCL1", "MDM2", "MDM4", "MED12", "MEF2B", "MEN1", "MET", "MITF", "MLH1", "MLL", "MLL2",
            "MPL", "MRE11A", "MSH2", "MSH3", "MSH6", "MST1R", "MTOR", "MUTYH", "MYC", "MYCL", "MYCN",
            "MYD88", "NBN", "NF1", "NF2", "NFE2L2", "NFKBIA", "NKX2-1", "NOTCH1", "NOTCH2", "NOTCH3",
            "NPM1", "NRAS", "NSD1", "NTRK1", "NTRK2", "NTRK3", "NUP93", "PAK3", "PALB2", "PARK2",
            "PAX5", "PBRM1", "PDCD1", "PDCD1LG2", "PDGFRA", "PDGFRB", "PDK1", "PHF6", "PIK3CA", "PIK3CB",
            "PIK3R1", "PIM1", "PMS2", "POLD1", "POLE", "PPARG", "PPP2R1A", "PRDM1", "PREX2", "PRKAR1A",
            "PRKCI", "PRKDC", "PTCH1", "PTEN", "PTPN11", "PTPRO", "QKI", "RAC1", "RAD21", "RAD50",
            "RAD51", "RAD51B", "RAD51C", "RAD51D", "RAD52", "RAD54L", "RAF1", "RANBP2", "RARA", "RB1",
            "RBM10", "RECQL4", "REL", "RET", "RFWD2", "RHEB", "RHOA", "RICTOR", "RIT1", "RNF43",
            "ROS1", "RPS6KA4", "RPS6KB2", "RPTOR", "RRAGC", "RRAS", "RRAS2", "RUNX1", "RUNX1T1", "SDHA",
            "SDHB", "SDHC", "SDHD", "SETD2", "SF3B1", "SGKSFK", "SH2D1A", "SMAD2", "SMAD4", "SMARCA4",
            "SMARCB1", "SMO", "SNCAIP", "SOCS1", "SOS1", "SOX10", "SOX2", "SOX9", "SPEN", "SPOP",
            "SRC", "STAG2", "STAT3", "STAT4", "STK11", "SUFU", "SYK", "TBX3", "TERC", "TERT", "TET2",
            "TGFBR2", "TMEM127", "TMPRSS2", "TNFAIP3", "TNFRSF14", "TOP1", "TP53", "TP63", "TRAF2",
            "TRAF7", "TSC1", "TSC2", "TSHR", "U2AF1", "UBR5", "VEGFA", "VHL", "WHSC1", "WHSC1L1",
            "WT1", "XPO1", "XRCC2", "ZNF217", "ZNF703"
        ],
        "biomarkers": ["TMB", "MSI", "HRD"],
        "methodology": "Hybrid capture-based NGS",
        "provider": "Foundation Medicine"
    },
    
    "OncoPanel Plus": {
        "description": "Targeted sequencing - 447 genes",
        "genes": [
            "EGFR", "KRAS", "BRAF", "ALK", "ROS1", "RET", "MET", "NTRK1", "NTRK2", "NTRK3",
            "ERBB2", "PIK3CA", "AKT1", "PTEN", "TP53", "BRCA1", "BRCA2", "ATM", "PALB2", "CHEK2",
            "FGFR1", "FGFR2", "FGFR3", "FGFR4", "CDK4", "CDK6", "CDKN2A", "MDM2", "KIT", "PDGFRA",
            "NF1", "APC", "MLH1", "MSH2", "MSH6", "PMS2", "EPCAM", "STK11", "VHL", "TSC1", "TSC2",
            "POLE", "POLD1", "IDH1", "IDH2", "ARID1A", "ATRX", "DAXX", "CTNNB1", "SMAD4", "SMARCA4"
        ],
        "biomarkers": ["TMB", "MSI"],
        "methodology": "Targeted NGS panel",
        "provider": "Multiple labs"
    },
    
    "Comprehensive Cancer Panel": {
        "description": "Comprehensive panel - 170 genes",
        "genes": [
            "ABL1", "AKT1", "ALK", "APC", "AR", "ARID1A", "ATM", "ATRX", "AURKA", "AXL",
            "BAP1", "BARD1", "BCL2", "BCL6", "BCOR", "BRAF", "BRCA1", "BRCA2", "BRD4", "BRIP1",
            "BTK", "CARD11", "CBFB", "CBL", "CCND1", "CCND2", "CCND3", "CCNE1", "CD274", "CD79B",
            "CDC73", "CDH1", "CDK12", "CDK4", "CDK6", "CDKN1B", "CDKN2A", "CDKN2B", "CEBPA", "CHEK1",
            "CHEK2", "CIC", "CREBBP", "CSF1R", "CTCF", "CTNNB1", "DAXX", "DDR2", "DNMT3A", "DOT1L",
            "EGFR", "EP300", "EPCAM", "ERBB2", "ERBB3", "ERBB4", "ERG", "ESR1", "ETV1", "ETV6",
            "EWSR1", "EZH2", "FAM46C", "FBXW7", "FGFR1", "FGFR2", "FGFR3", "FGFR4", "FH", "FLCN",
            "FLT3", "FOXL2", "GATA1", "GATA2", "GATA3", "GNA11", "GNAQ", "GNAS", "H3F3A", "HNF1A",
            "HRAS", "IDH1", "IDH2", "IFNGR1", "IGF1R", "IKBKE", "IKZF1", "IL7R", "IRF4", "JAK1",
            "JAK2", "JAK3", "JUN", "KDM5C", "KDM6A", "KDR", "KEAP1", "KIT", "KMT2A", "KMT2D",
            "KRAS", "MAP2K1", "MAP2K2", "MAP3K1", "MAX", "MCL1", "MDM2", "MDM4", "MED12", "MEF2B",
            "MEN1", "MET", "MITF", "MLH1", "MPL", "MRE11A", "MSH2", "MSH6", "MTOR", "MUTYH",
            "MYC", "MYCN", "MYD88", "NBN", "NF1", "NF2", "NFE2L2", "NOTCH1", "NOTCH2", "NPM1",
            "NRAS", "NTRK1", "NTRK2", "NTRK3", "PALB2", "PARK2", "PAX5", "PBRM1", "PDCD1", "PDGFRA",
            "PDGFRB", "PHF6", "PIK3CA", "PIK3R1", "PMS2", "POLD1", "POLE", "PPP2R1A", "PRDM1", "PTCH1",
            "PTEN", "PTPN11", "QKI", "RAC1", "RAD21", "RAD50", "RAD51", "RAF1", "RARA", "RB1",
            "RET", "RHOA", "RIT1", "RNF43", "ROS1", "RUNX1", "SDHA", "SDHB", "SDHC", "SDHD",
            "SETD2", "SF3B1", "SMAD2", "SMAD4", "SMARCA4", "SMARCB1", "SMO", "SOCS1", "SOS1", "SOX2",
            "SOX9", "SPOP", "SRC", "STAG2", "STAT3", "STK11", "SUFU", "SYK", "TET2", "TGFBR2",
            "TNFAIP3", "TP53", "TSC1", "TSC2", "U2AF1", "VEGFA", "VHL", "WT1"
        ],
        "biomarkers": ["TMB", "MSI", "HRD"],
        "methodology": "Hybrid capture NGS",
        "provider": "Various"
    }
}


def get_panel(panel_name: str = "Comprehensive Cancer Panel") -> Dict:
    """
    Get NGS panel information
    
    Args:
        panel_name: Panel name
    
    Returns:
        Panel information dictionary
    """
    return NGS_PANELS.get(panel_name, NGS_PANELS["Comprehensive Cancer Panel"])


def get_panel_genes(panel_name: str = "Comprehensive Cancer Panel") -> List[str]:
    """
    Get list of genes in panel
    
    Args:
        panel_name: Panel name
    
    Returns:
        List of gene symbols
    """
    panel = get_panel(panel_name)
    return panel.get("genes", [])


def detect_panel_from_genes(detected_genes: List[str]) -> str:
    """
    Detect which panel was likely used based on detected genes
    
    Args:
        detected_genes: List of gene symbols found in report
    
    Returns:
        Most likely panel name
    """
    max_overlap = 0
    best_panel = "Comprehensive Cancer Panel"
    
    for panel_name, panel_info in NGS_PANELS.items():
        panel_genes = set(panel_info["genes"])
        overlap = len(set(detected_genes) & panel_genes)
        
        if overlap > max_overlap:
            max_overlap = overlap
            best_panel = panel_name
    
    return best_panel


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("NGS Panels Available")
    print("=" * 80)
    
    for panel_name, info in NGS_PANELS.items():
        print(f"\n{panel_name}")
        print(f"  Description: {info['description']}")
        print(f"  Genes: {len(info['genes'])}")
        print(f"  Biomarkers: {', '.join(info['biomarkers'])}")
        print(f"  Methodology: {info['methodology']}")
