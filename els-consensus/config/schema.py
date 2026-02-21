# config/schema.py

QUESTION_SCHEMA = {
    "cell_types": {
        "type": "multi",
        "options": ["B", "T", "Ki67"]
    },
    "dominant_population": {
        "type": "single",
        "options": ["B", "T", "Ki67", "mixed", "few_cells"]
    },
    "density": {
        "type": "single",
        "options": ["high", "moderate", "low", "very_low"]
    },
    "b_t_separation": {
        "type": "single",
        "options": ["na", "none", "low", "moderate", "high"]
    },
    "t_ring": {
        "type": "single",
        "options": ["na", "none", "weak", "moderate", "clear"]
    },
    "gc_like": {
        "type": "boolean"
    }
}