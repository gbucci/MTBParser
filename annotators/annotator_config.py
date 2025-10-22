#!/usr/bin/env python3
"""
Annotator Configuration System
Allows selective enabling/disabling of clinical annotation sources based on:
- License availability (OncoKB requires paid license)
- User preference
- Performance requirements
- API availability
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class AnnotatorType(Enum):
    """Available clinical annotator types"""
    CIVIC = "civic"          # Free, open access, community-curated
    ONCOKB = "oncokb"        # Commercial license required for clinical use
    ESCAT = "escat"          # Free, ESMO-based, European standard


class LicenseType(Enum):
    """License requirements for annotators"""
    FREE = "free"            # No license required
    ACADEMIC = "academic"    # Academic/research license required
    COMMERCIAL = "commercial"  # Commercial license required


@dataclass
class AnnotatorMetadata:
    """Metadata for each annotator"""
    name: str
    type: AnnotatorType
    license: LicenseType
    description: str
    requires_api_key: bool = False
    cost: str = "Free"
    update_frequency: str = "Unknown"
    coverage: str = "Unknown"
    focus: str = "Global"

    # Licensing info
    license_url: Optional[str] = None
    terms_url: Optional[str] = None


# Annotator metadata registry
ANNOTATOR_METADATA = {
    AnnotatorType.CIVIC: AnnotatorMetadata(
        name="CIViC",
        type=AnnotatorType.CIVIC,
        license=LicenseType.FREE,
        description="Clinical Interpretations of Variants in Cancer (community-curated)",
        requires_api_key=False,
        cost="Free (CC0 Public Domain)",
        update_frequency="Continuous (community)",
        coverage="~3000+ variants",
        focus="Global, multi-source",
        license_url="https://civicdb.org/about",
        terms_url="https://civicdb.org/terms"
    ),

    AnnotatorType.ONCOKB: AnnotatorMetadata(
        name="OncoKB",
        type=AnnotatorType.ONCOKB,
        license=LicenseType.COMMERCIAL,
        description="Precision Oncology Knowledge Base (MSK-curated)",
        requires_api_key=True,
        cost="Free tier: 1000 requests/month; Commercial: Contact MSK",
        update_frequency="Regular (curated team)",
        coverage="~5000+ variants",
        focus="US/FDA, clinical trials",
        license_url="https://www.oncokb.org/apiAccess",
        terms_url="https://www.oncokb.org/terms"
    ),

    AnnotatorType.ESCAT: AnnotatorMetadata(
        name="ESCAT",
        type=AnnotatorType.ESCAT,
        license=LicenseType.FREE,
        description="ESMO Scale for Clinical Actionability of molecular Targets",
        requires_api_key=False,
        cost="Free (citation required)",
        update_frequency="Annual (ESMO guidelines)",
        coverage="~50+ tier-classified alterations",
        focus="European/ESMO, EMA approval",
        license_url="https://www.esmo.org/guidelines/precision-medicine",
        terms_url=None
    )
}


@dataclass
class AnnotatorConfig:
    """
    Configuration for clinical annotators

    Allows selective enabling of annotation sources based on:
    - Available licenses
    - User preferences
    - Performance requirements
    """

    # Enabled annotators
    enabled_annotators: Set[AnnotatorType] = field(default_factory=lambda: {
        AnnotatorType.CIVIC,  # Free by default
        AnnotatorType.ESCAT   # Free by default
    })

    # API keys (if available)
    oncokb_api_key: Optional[str] = None

    # Preferences
    prefer_free_sources: bool = True
    prefer_european_standards: bool = False  # Prefer ESCAT over OncoKB

    # Performance
    enable_caching: bool = True
    parallel_queries: bool = False

    def __post_init__(self):
        """Validate configuration"""
        # If OncoKB is enabled but no API key, warn user
        if AnnotatorType.ONCOKB in self.enabled_annotators and not self.oncokb_api_key:
            import warnings
            warnings.warn(
                "OncoKB is enabled but no API key provided. "
                "Using mock data. For production, obtain API key at "
                "https://www.oncokb.org/apiAccess"
            )

    @classmethod
    def free_only(cls) -> 'AnnotatorConfig':
        """
        Configuration using only free annotators (CIViC + ESCAT)

        Recommended for:
        - Academic research
        - Testing/development
        - Budget-constrained projects
        """
        return cls(
            enabled_annotators={AnnotatorType.CIVIC, AnnotatorType.ESCAT},
            prefer_free_sources=True
        )

    @classmethod
    def escat_only(cls) -> 'AnnotatorConfig':
        """
        Configuration using only ESCAT (European standard)

        Recommended for:
        - European hospitals
        - ESMO guideline compliance
        - EMA-approval focused decisions
        """
        return cls(
            enabled_annotators={AnnotatorType.ESCAT},
            prefer_european_standards=True
        )

    @classmethod
    def civic_only(cls) -> 'AnnotatorConfig':
        """
        Configuration using only CIViC (community-curated)

        Recommended for:
        - Maximum coverage
        - Research publications
        - Community-driven evidence
        """
        return cls(
            enabled_annotators={AnnotatorType.CIVIC},
            prefer_free_sources=True
        )

    @classmethod
    def oncokb_only(cls, api_key: str) -> 'AnnotatorConfig':
        """
        Configuration using only OncoKB (MSK-curated)

        Recommended for:
        - US hospitals
        - FDA-focused decisions
        - Clinical trial matching

        Args:
            api_key: OncoKB API key (obtain from oncokb.org)
        """
        return cls(
            enabled_annotators={AnnotatorType.ONCOKB},
            oncokb_api_key=api_key,
            prefer_free_sources=False
        )

    @classmethod
    def all_sources(cls, oncokb_api_key: Optional[str] = None) -> 'AnnotatorConfig':
        """
        Configuration using all available annotators

        Provides maximum validation through triple-source concordance.

        Recommended for:
        - Molecular Tumor Boards
        - High-stakes clinical decisions
        - Maximum evidence validation

        Args:
            oncokb_api_key: Optional OncoKB API key
        """
        return cls(
            enabled_annotators={
                AnnotatorType.CIVIC,
                AnnotatorType.ONCOKB,
                AnnotatorType.ESCAT
            },
            oncokb_api_key=oncokb_api_key,
            prefer_free_sources=False
        )

    @classmethod
    def european_clinical(cls) -> 'AnnotatorConfig':
        """
        Configuration optimized for European clinical use

        Prioritizes ESCAT (European standard) with CIViC as backup.
        Excludes OncoKB to avoid licensing costs.

        Recommended for:
        - European hospitals
        - ESMO guideline compliance
        - Budget-conscious institutions
        """
        return cls(
            enabled_annotators={AnnotatorType.ESCAT, AnnotatorType.CIVIC},
            prefer_european_standards=True,
            prefer_free_sources=True
        )

    @classmethod
    def us_clinical(cls, oncokb_api_key: str) -> 'AnnotatorConfig':
        """
        Configuration optimized for US clinical use

        Prioritizes OncoKB (FDA-focused) with CIViC as backup.

        Recommended for:
        - US hospitals
        - FDA approval-focused decisions
        - NCCN guideline compliance

        Args:
            oncokb_api_key: OncoKB API key
        """
        return cls(
            enabled_annotators={AnnotatorType.ONCOKB, AnnotatorType.CIVIC},
            oncokb_api_key=oncokb_api_key,
            prefer_european_standards=False
        )

    def is_enabled(self, annotator_type: AnnotatorType) -> bool:
        """Check if an annotator is enabled"""
        return annotator_type in self.enabled_annotators

    def enable(self, annotator_type: AnnotatorType):
        """Enable an annotator"""
        self.enabled_annotators.add(annotator_type)

    def disable(self, annotator_type: AnnotatorType):
        """Disable an annotator"""
        self.enabled_annotators.discard(annotator_type)

    def get_enabled_names(self) -> List[str]:
        """Get names of enabled annotators"""
        return [
            ANNOTATOR_METADATA[atype].name
            for atype in self.enabled_annotators
        ]

    def get_licensing_info(self) -> Dict:
        """Get licensing information for enabled annotators"""
        info = {}
        for atype in self.enabled_annotators:
            metadata = ANNOTATOR_METADATA[atype]
            info[metadata.name] = {
                'license': metadata.license.value,
                'cost': metadata.cost,
                'requires_api_key': metadata.requires_api_key,
                'license_url': metadata.license_url,
                'terms_url': metadata.terms_url
            }
        return info

    def validate_licenses(self) -> Dict[str, bool]:
        """
        Validate that necessary licenses/API keys are available

        Returns:
            Dict mapping annotator name to validation status
        """
        validation = {}

        for atype in self.enabled_annotators:
            metadata = ANNOTATOR_METADATA[atype]

            if atype == AnnotatorType.ONCOKB:
                # OncoKB requires API key for production
                validation[metadata.name] = (
                    self.oncokb_api_key is not None or
                    "Using mock data (no API key)"
                )
            else:
                # CIViC and ESCAT are free
                validation[metadata.name] = True

        return validation

    def summary(self) -> str:
        """Generate configuration summary"""
        lines = []
        lines.append("="*70)
        lines.append("CLINICAL ANNOTATOR CONFIGURATION")
        lines.append("="*70)

        lines.append(f"\nEnabled annotators: {', '.join(self.get_enabled_names())}")
        lines.append(f"Total sources: {len(self.enabled_annotators)}")

        lines.append("\nLicensing Information:")
        for name, info in self.get_licensing_info().items():
            lines.append(f"\n  {name}:")
            lines.append(f"    License: {info['license']}")
            lines.append(f"    Cost: {info['cost']}")
            if info['requires_api_key']:
                lines.append(f"    API Key: {'✓ Configured' if self.oncokb_api_key else '✗ Missing (using mock)'}")
            if info['license_url']:
                lines.append(f"    Info: {info['license_url']}")

        lines.append("\nPreferences:")
        lines.append(f"  Prefer free sources: {self.prefer_free_sources}")
        lines.append(f"  Prefer European standards: {self.prefer_european_standards}")
        lines.append(f"  Enable caching: {self.enable_caching}")

        lines.append("\nValidation:")
        for name, status in self.validate_licenses().items():
            if isinstance(status, bool):
                status_str = "✓ Valid" if status else "✗ Invalid"
            else:
                status_str = f"⚠ {status}"
            lines.append(f"  {name}: {status_str}")

        lines.append("\n" + "="*70)

        return "\n".join(lines)


# Example usage and presets
if __name__ == "__main__":
    print("ANNOTATOR CONFIGURATION EXAMPLES\n")

    # Example 1: Free only (default)
    print("1. FREE SOURCES ONLY (CIViC + ESCAT)")
    print("-" * 70)
    config = AnnotatorConfig.free_only()
    print(config.summary())

    # Example 2: ESCAT only (European)
    print("\n\n2. ESCAT ONLY (European Standard)")
    print("-" * 70)
    config = AnnotatorConfig.escat_only()
    print(config.summary())

    # Example 3: European clinical
    print("\n\n3. EUROPEAN CLINICAL (ESCAT + CIViC)")
    print("-" * 70)
    config = AnnotatorConfig.european_clinical()
    print(config.summary())

    # Example 4: All sources (with OncoKB)
    print("\n\n4. ALL SOURCES (Maximum validation)")
    print("-" * 70)
    config = AnnotatorConfig.all_sources(oncokb_api_key="demo_key_12345")
    print(config.summary())

    # Example 5: Custom configuration
    print("\n\n5. CUSTOM CONFIGURATION")
    print("-" * 70)
    config = AnnotatorConfig()
    config.enable(AnnotatorType.CIVIC)
    config.enable(AnnotatorType.ESCAT)
    config.disable(AnnotatorType.ONCOKB)
    config.prefer_european_standards = True
    print(config.summary())
