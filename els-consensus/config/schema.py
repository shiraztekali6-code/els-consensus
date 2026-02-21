QUESTION_SCHEMA = {
    "cell_types_present": {
        "type": "multi",
        "options": [
            "B cells",
            "T cells",
            "Proliferating cells (Ki67+)"
        ]
    },

    "dominant_cell_type": {
        "type": "single",
        "options": [
            "B cells dominant",
            "T cells dominant",
            "Ki67+ dominant",
            "No dominant population",
            "Very few cells"
        ]
    },

    "cell_density": {
        "type": "single",
        "options": [
            "High density",
            "Moderate density",
            "Low density",
            "Very low density"
        ]
    },

    "b_t_separation": {
        "type": "single",
        "options": [
            "Not applicable",
            "Not separated",
            "Low separation",
            "Moderate separation",
            "High separation"
        ]
    },

    "t_cell_ring": {
        "type": "single",
        "options": [
            "Not applicable",
            "No ring",
            "Weak ring",
            "Moderate ring",
            "Clear ring"
        ]
    },

    "gc_like_structure": {
        "type": "single",
        "options": [
            "No GC-like structure",
            "GC-like structure present"
        ]
    }
}
