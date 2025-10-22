#!/usr/bin/env python3
"""
Clinical Annotators Module
Provides integration with external clinical evidence databases
"""

from .civic_annotator import CIViCAnnotator
from .oncokb_annotator import OncoKBAnnotator
from .escat_annotator import ESCATAnnotator
from .combined_annotator import CombinedAnnotator

__all__ = ['CIViCAnnotator', 'OncoKBAnnotator', 'ESCATAnnotator', 'CombinedAnnotator']
