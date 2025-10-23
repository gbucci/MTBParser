"""
ESCAT Pyramid Visualization

ESCAT (ESMO Scale for Clinical Actionability of molecular Targets) Framework:
- Tier I: Targets with clinical utility in specific tumor type
  - I-A: FDA/EMA approved in that tumor type
  - I-B: Clinical guidelines recommendation
- Tier II: Targets with clinical utility in another tumor type
  - II-A: FDA/EMA approved in different tumor type
  - II-B: Clinical guidelines in different tumor type
- Tier III: Clinical benefit in tumor type proven in clinical trials
  - III-A: Prospective clinical trials
  - III-B: Retrospective data
- Tier IV: Preclinical evidence
- Tier X: Lack of evidence or resistance
"""

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from typing import Dict, List, Optional


# ESCAT Level Definitions
ESCAT_LEVELS = {
    'I-A': {
        'label': 'I-A',
        'description': 'FDA/EMA approved biomarker',
        'color': colors.HexColor('#27ae60'),  # Dark green
        'tier': 1
    },
    'I-B': {
        'label': 'I-B',
        'description': 'Clinical guidelines',
        'color': colors.HexColor('#2ecc71'),  # Green
        'tier': 1
    },
    'II-A': {
        'label': 'II-A',
        'description': 'Approved in other tumor',
        'color': colors.HexColor('#f39c12'),  # Orange
        'tier': 2
    },
    'II-B': {
        'label': 'II-B',
        'description': 'Guidelines in other tumor',
        'color': colors.HexColor('#f1c40f'),  # Yellow
        'tier': 2
    },
    'III-A': {
        'label': 'III-A',
        'description': 'Prospective trials',
        'color': colors.HexColor('#3498db'),  # Blue
        'tier': 3
    },
    'III-B': {
        'label': 'III-B',
        'description': 'Retrospective evidence',
        'color': colors.HexColor('#5dade2'),  # Light blue
        'tier': 3
    },
    'IV': {
        'label': 'IV',
        'description': 'Preclinical evidence',
        'color': colors.HexColor('#95a5a6'),  # Gray
        'tier': 4
    },
    'X': {
        'label': 'X',
        'description': 'Resistance/No evidence',
        'color': colors.HexColor('#e74c3c'),  # Red
        'tier': 5
    }
}


def get_escat_level_info(level: str) -> Optional[Dict]:
    """Get ESCAT level information"""
    return ESCAT_LEVELS.get(level.upper())


def get_escat_color(level: str) -> colors.Color:
    """Get color for ESCAT level"""
    info = get_escat_level_info(level)
    return info['color'] if info else colors.grey


def create_escat_pyramid(width: float = 12*cm, include_legend: bool = True) -> List:
    """
    Create ESCAT pyramid visualization as reportlab flowables

    Args:
        width: Width of pyramid in cm
        include_legend: Whether to include legend with descriptions

    Returns:
        List of flowable elements
    """
    elements = []

    # Title
    title_style = ParagraphStyle(
        'ESCATTitle',
        fontSize=11,
        textColor=colors.HexColor('#1a5490'),
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph("ESCAT - Scala di Actionability Clinica", title_style))

    # Pyramid structure - from top (narrowest) to bottom (widest)
    pyramid_data = [
        # Each row: [level, relative_width]
        ['I-A', 0.3],
        ['I-B', 0.4],
        ['II-A', 0.5],
        ['II-B', 0.6],
        ['III-A', 0.7],
        ['III-B', 0.8],
        ['IV', 0.9],
        ['X', 1.0],
    ]

    # Create pyramid rows
    for level, rel_width in pyramid_data:
        info = ESCAT_LEVELS[level]

        # Calculate width for this level
        level_width = width * rel_width

        # Create single-cell table for pyramid level
        level_text = f"<b>{info['label']}</b>"
        if include_legend:
            level_text += f"<br/><font size='8'>{info['description']}</font>"

        cell_data = [[Paragraph(level_text, ParagraphStyle(
            'ESCATLevel',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.white if level != 'IV' else colors.black
        ))]]

        level_table = Table(cell_data, colWidths=[level_width])
        level_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), info['color']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.white),
        ]))

        elements.append(level_table)
        elements.append(Spacer(1, 2))  # Small space between levels

    # Add interpretation note
    note_style = ParagraphStyle(
        'ESCATNote',
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontStyle='italic'
    )
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Tier I (verde): Massima evidenza clinica | Tier X (rosso): Resistenza o assenza evidenza",
        note_style
    ))

    return elements


def create_escat_legend() -> List:
    """Create detailed ESCAT legend table"""
    elements = []

    # Legend title
    title_style = ParagraphStyle(
        'LegendTitle',
        fontSize=10,
        textColor=colors.HexColor('#1a5490'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    elements.append(Paragraph("Legenda ESCAT", title_style))

    # Legend data
    legend_data = [["Livello", "Descrizione", "Evidenza Clinica"]]

    for level_key in ['I-A', 'I-B', 'II-A', 'II-B', 'III-A', 'III-B', 'IV', 'X']:
        info = ESCAT_LEVELS[level_key]

        # Create colored level cell
        level_para = Paragraph(
            f"<b>{info['label']}</b>",
            ParagraphStyle('Level', fontSize=9, alignment=TA_CENTER, textColor=colors.white if level_key != 'IV' else colors.black)
        )

        desc_para = Paragraph(info['description'], ParagraphStyle('Desc', fontSize=8))

        # Evidence description
        evidence_map = {
            'I-A': 'Approvato da agenzie regolatorie (FDA/EMA) per questo tumore',
            'I-B': 'Raccomandato da linee guida cliniche per questo tumore',
            'II-A': 'Approvato per un tumore diverso',
            'II-B': 'Raccomandato da linee guida per un tumore diverso',
            'III-A': 'Beneficio clinico dimostrato in trial prospettici',
            'III-B': 'Evidenza retrospettiva di beneficio clinico',
            'IV': 'Evidenza solo preclinica (in vitro/in vivo)',
            'X': 'Marcatore di resistenza o assenza di evidenza'
        }
        evidence_para = Paragraph(evidence_map[level_key], ParagraphStyle('Evidence', fontSize=8))

        legend_data.append([level_para, desc_para, evidence_para])

    legend_table = Table(legend_data, colWidths=[2*cm, 4*cm, 7*cm])
    legend_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Level column colored backgrounds
        *[('BACKGROUND', (0, i+1), (0, i+1), ESCAT_LEVELS[level]['color'])
          for i, level in enumerate(['I-A', 'I-B', 'II-A', 'II-B', 'III-A', 'III-B', 'IV', 'X'])],

        # General styling
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(legend_table)
    return elements


def map_variant_to_escat(variant: Dict, diagnosis: str) -> Optional[str]:
    """
    Map a variant to ESCAT level based on actionability and context

    Args:
        variant: Variant dictionary with gene, classification, etc.
        diagnosis: Primary diagnosis

    Returns:
        ESCAT level string (e.g., 'I-A', 'II-B') or None
    """
    gene = variant.get('gene', '').upper()
    classification = variant.get('classification', '').lower()

    # High evidence actionable variants (examples - should be expanded)
    tier_1a_variants = {
        'EGFR': ['NSCLC', 'lung'],
        'BRAF': ['melanoma', 'colorectal'],
        'ALK': ['NSCLC', 'lung'],
        'ROS1': ['NSCLC', 'lung'],
        'ERBB2': ['breast', 'gastric'],
        'KIT': ['GIST'],
        'KRAS': ['colorectal', 'NSCLC'],
    }

    # Resistance markers
    resistance_markers = {
        'EGFR': ['T790M'],  # EGFR TKI resistance
        'KRAS': ['G12C', 'G12V', 'G13D'],  # May indicate resistance to certain therapies
    }

    # Check if variant is pathogenic/likely pathogenic
    if classification not in ['pathogenic', 'likely pathogenic']:
        return 'IV'  # VUS or benign -> preclinical at best

    # Check for resistance
    protein_change = variant.get('protein_change', '')
    if gene in resistance_markers:
        for res_marker in resistance_markers[gene]:
            if res_marker in protein_change:
                return 'X'

    # Check for tier I-A (FDA approved in this tumor)
    if gene in tier_1a_variants:
        diagnoses_lower = diagnosis.lower() if diagnosis else ''
        for tumor_type in tier_1a_variants[gene]:
            if tumor_type.lower() in diagnoses_lower:
                return 'I-A'
        # Approved but in different tumor
        return 'II-A'

    # Gene fusions are often actionable
    if '::' in gene or variant.get('protein_change') == 'fusion':
        if any(fusion_gene in gene for fusion_gene in ['ALK', 'ROS1', 'RET', 'NTRK', 'FGFR']):
            return 'I-B'

    # Default to tier IV (preclinical)
    return 'IV'
