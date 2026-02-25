QUESTION_SCHEMA = {

    # -------------------------
    # 1. Cell types present
    # -------------------------
"cell_types_present": {
"type": "multi",
"options": [
            "B cells present",
            "T cells present",
            "Proliferating cells (Ki67+) present"
            "B cells are present",
            "T cells are present",
            "Proliferating cells (Ki67+) are present"
],
        "description": "Select all cell types that are clearly present."
        "description": (
            "Color legend: Yellow = B cells, Red = T cells, Green = Proliferating cells (Ki67+).\n\n"
            "Select all cell types that are clearly present within the ELS. "
            "Base your answer on clear, specific staining rather than faint or ambiguous signal."
        )
},

    # -------------------------
    # 2. Dominant population
    # -------------------------
"dominant_cell_population": {
"type": "single",
"options": [
            "B cells are dominant",
            "T cells are dominant",
            "Proliferating cells (Ki67+) are dominant",
            "No dominant population",
            "Very few cells present overall"
            "B cells are the most abundant",
            "T cells are the most abundant",
            "Proliferating cells (Ki67+) are the most abundant",
            "Cell populations appear similar in abundance",
            "Very few cells are present overall"
],
        "description": "Which population is dominant?"
        "description": (
            "Which cell population appears to be the most abundant within the ELS?"
        )
},

    # -------------------------
    # 3. Cell density
    # -------------------------
"cell_density": {
"type": "single",
"options": [
            "High density",
            "Moderate density",
            "Low density",
            "Very low density"
            "High density (cells are tightly packed and overlapping)",
            "Moderate density (cells are very close but individually distinguishable)",
            "Low density (cells are separated with visible background between them)",
            "Very low density (isolated cells with large dark background or staining noise)"
],
        "description": "Overall cell density."
        "description": (
            "Estimate the overall cellular density within the ELS."
        )
},

    # -------------------------
    # 4. B / T spatial separation
    # -------------------------
"b_t_separation": {
"type": "single",
"options": [
            "Not applicable",
            "Not separated",
            "Low separation",
            "Moderate separation",
            "High separation"
            "Not applicable (only one cell type present)",
            "Not separated (completely mixed, no distinct areas)",
            "Low separation (early area formation but mostly mixed)",
            "Moderate separation (distinct areas with some overlap)",
            "High separation (clearly separated areas with relatively sharp boundaries)"
],
        "description": "Degree of B/T separation."
        "description": (
            "Assess the degree of spatial separation between B-cell–rich and T-cell–rich areas."
        )
},

    # -------------------------
    # 5. T-cell ring
    # -------------------------
"t_cell_ring": {
"type": "single",
"options": [
            "Not applicable",
            "No T-cell ring",
            "Weak T-cell ring",
            "Moderate T-cell ring",
            "Clear T-cell ring"
            "Not applicable (no T cells present)",
            "No ring present",
            "Weak ring formation",
            "Moderate ring formation",
            "Clear ring formation"
],
        "description": "Presence of T-cell ring."
        "description": (
            "Is there a ring-like accumulation of T cells at the periphery of the ELS?"
        )
},

    # -------------------------
    # 6. GC-like structure
    # -------------------------
"gc_like_structure": {
"type": "single",
"options": [
            "No GC-like structure",
            "No GC-like structure present",
"GC-like structure present"
],
        "description": "GC-like structure presence."
        "description": (
            "GC-like structure is defined as a clearly localized cluster of proliferating "
            "(Ki67+) cells situated within or tightly surrounded by a B- or T-cell–rich area "
            "(yellow or red), and not diffusely distributed across the entire ELS."
        )
}
}
