#!/usr/bin/env python3
"""
PDF Report Generator for MTBParser
Generates standardized PDF reports from parsed MTB data
"""

from .ngs_panels import get_panel, get_panel_genes, detect_panel_from_genes

__all__ = ['get_panel', 'get_panel_genes', 'detect_panel_from_genes']
