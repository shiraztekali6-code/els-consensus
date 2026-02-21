QUESTION_SCHEMA = {

    # 1. אילו סוגי תאים נוכחים
    "cell_types_present": {
        "type": "multi",
        "options": [
            "B cells present",
            "T cells present",
            "Proliferating cells (Ki67+) present"
        ],
        "description": (
            "Select all cell types that are clearly present within the ELS. "
            "Base your answer on clear, specific staining rather than faint or ambiguous signal."
        )
    },

    # 2. מי האוכלוסייה הדומיננטית
    "dominant_cell_population": {
        "type": "single",
        "options": [
            "B cells are dominant",
            "T cells are dominant",
            "Proliferating cells (Ki67+) are dominant",
            "No dominant population (similar abundance)",
            "Very few cells present overall"
        ],
        "description": (
            "Which cell population appears to be the most abundant within the ELS?"
        )
    },

    # 3. צפיפות כללית
    "cell_density": {
        "type": "single",
        "options": [
            "High density (tightly packed cells)",
            "Moderate density (closely packed but distinguishable)",
            "Low density (cells separated with visible background)",
            "Very low density (isolated cells or mostly background)"
        ],
        "description": (
            "Estimate the overall cellular density within the ELS."
        )
    },

    # 4. הפרדה בין אזורי B ו-T
    "b_t_separation": {
        "type": "single",
        "options": [
            "Not applicable (only one cell type present)",
            "Not separated (completely mixed)",
            "Low separation (early or partial area formation)",
            "Moderate separation (distinct areas with some overlap)",
            "High separation (clearly separated areas)"
        ],
        "description": (
            "Assess the degree of spatial separation between B-cell–rich and T-cell–rich areas."
        )
    },

    # 5. טבעת תאי T
    "t_cell_ring": {
        "type": "single",
        "options": [
            "Not applicable (no T cells present)",
            "No T-cell ring",
            "Weak T-cell ring",
            "Moderate T-cell ring",
            "Clear T-cell ring"
        ],
        "description": (
            "Is there a ring-like accumulation of T cells at the periphery of the ELS?"
        )
    },

    # 6. מבנה דמוי GC
    "gc_like_structure": {
        "type": "single",
        "options": [
            "No GC-like structure",
            "GC-like structure present"
        ],
        "description": (
            "GC-like structure is defined as a localized cluster of proliferating (Ki67+) cells "
            "situated within or tightly surrounded by a B- or T-cell–rich area, "
            "and not diffusely distributed across the entire ELS."
        )
    }
}
