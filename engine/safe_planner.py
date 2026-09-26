from typing import List, Tuple, Optional
from engine.schema import ActionableDeepLink, StepGroup, ValidationDeepLink


class SafePlanOrderer:
    """
    Enforces safe plan ordering logic for troubleshooting engines:
    - Safe, non-invasive toggles (power saving, adaptive brightness, cache clears) strictly FIRST.
    - Destructive actions (network resets, factory resets, wipe data) strictly LAST.
    - Groups steps into human-readable diagnostic phases.
    """

    VALIDATION_DEFAULTS = {
        "Battery": (
            "Battery diagnostics check",
            "It will test battery physical health.",
            "bixby://settings/device_care/battery_diagnostics",
            "Battery drain rate normalized below 2% per hour idle."
        ),
        "Display": (
            "Adaptive brightness control",
            "It will adjust light based brightness.",
            "bixby://settings/display/adaptive_brightness",
            "Display panel refresh rate and auto-lux sensor functioning correctly."
        ),
        "Camera": (
            "Clean camera lens",
            "It will remind physical lens cleaning.",
            "bixby://settings/camera/lens_clean_guidance",
            "Camera viewfinder launches without error code or focus hunting."
        ),
        "Performance": (
            "Device care optimize",
            "It will clean memory and cache.",
            "bixby://settings/device_care/optimize_now",
            "Available RAM increased and system frame drops eliminated."
        ),
        "Connectivity": (
            "Wifi network list",
            "It will search available wifi signals.",
            "bixby://settings/connections/wifi/networks",
            "Cellular and Wi-Fi handshakes completed with valid IP lease."
        ),
        "Sound": (
            "Dolby atmos audio",
            "It will enrich spatial surround sound.",
            "bixby://settings/sound/dolby_atmos",
            "Acoustic audio stream renders clean audio without distortion."
        ),
        "Default": (
            "Device care optimize",
            "It will clean memory and cache.",
            "bixby://settings/device_care/optimize_now",
            "System diagnostics check reports all hardware modules nominal."
        )
    }

    @classmethod
    def order_steps(cls, raw_steps: List[ActionableDeepLink]) -> Tuple[List[ActionableDeepLink], List[StepGroup]]:
        """
        Sorts steps strictly by invasive_level:
        Level 1: Non-invasive toggles & diagnostics
        Level 2: Moderate / app cache & data
        Level 3: Destructive operations (strictly last)
        """
        if not raw_steps:
            return [], []

        # Stable sort by invasive level
        sorted_steps = sorted(raw_steps, key=lambda s: (s.invasive_level, s.is_destructive))

        # Re-assign sequential step numbers
        reindexed_steps: List[ActionableDeepLink] = []
        phase1_indices: List[int] = []
        phase2_indices: List[int] = []
        phase3_indices: List[int] = []

        for i, step in enumerate(sorted_steps, start=1):
            cloned = step.model_copy(update={"step_number": i})
            reindexed_steps.append(cloned)
            if cloned.invasive_level == 1 and not cloned.is_destructive:
                phase1_indices.append(i)
            elif cloned.invasive_level == 2 and not cloned.is_destructive:
                phase2_indices.append(i)
            else:
                phase3_indices.append(i)

        # Build step groups
        groups: List[StepGroup] = []
        if phase1_indices:
            groups.append(
                StepGroup(
                    group_id="phase_1_non_invasive",
                    name="Phase 1: Non-Invasive Toggles",
                    description="Safest settings adjustments and immediate optimizations without data loss.",
                    step_numbers=phase1_indices
                )
            )
        if phase2_indices:
            groups.append(
                StepGroup(
                    group_id="phase_2_cache_maintenance",
                    name="Phase 2: Cache & Service Diagnostics",
                    description="App-level cache clearing and service maintenance steps.",
                    step_numbers=phase2_indices
                )
            )
        if phase3_indices:
            groups.append(
                StepGroup(
                    group_id="phase_3_destructive_recovery",
                    name="Phase 3: System Recovery & Reset",
                    description="Destructive recovery operations applied only if prior phases fail to resolve the issue.",
                    step_numbers=phase3_indices
                )
            )

        return reindexed_steps, groups

    @classmethod
    def get_validation_link(cls, domain: str) -> ValidationDeepLink:
        entry = cls.VALIDATION_DEFAULTS.get(domain.capitalize(), cls.VALIDATION_DEFAULTS["Default"])
        return ValidationDeepLink(
            title=entry[0],
            description=entry[1],
            uri=entry[2],
            expected_outcome=entry[3]
        )
