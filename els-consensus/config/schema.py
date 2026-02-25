QUESTION_SCHEMA = {
    "cell_types_present": {
        "type": "multi",
        "options": [
            "B cells present",
            "T cells present",
            "Proliferating cells (Ki67+) present"
        ],
        "description": "Select all cell types that are clearly present."
    },

    "dominant_cell_population": {
        "type": "single",
        "options": [
            "B cells are dominant",
            "T cells are dominant",
            "Proliferating cells (Ki67+) are dominant",
            "No dominant population",
            "Very few cells present overall"
        ],
        "description": "Which population is dominant?"
    },

    "cell_density": {
        "type": "single",
        "options": [
            "High density",
            "Moderate density",
            "Low density",
            "Very low density"
        ],
        "description": "Overall cell density."
    },

    "b_t_separation": {
        "type": "single",
        "options": [
            "Not applicable",
            "Not separated",
            "Low separation",
            "Moderate separation",
            "High separation"
        ],
        "description": "Degree of B/T separation."
    },

    "t_cell_ring": {
        "type": "single",
        "options": [
            "Not applicable",
            "No T-cell ring",
            "Weak T-cell ring",
            "Moderate T-cell ring",
            "Clear T-cell ring"
        ],
        "description": "Presence of T-cell ring."
    },

    "gc_like_structure": {
        "type": "single",
        "options": [
            "No GC-like structure",
            "GC-like structure present"
        ],
        "description": "GC-like structure presence."
    }
}


