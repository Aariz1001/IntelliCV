from __future__ import annotations

from jsonschema import validate
from jsonschema.exceptions import ValidationError


CV_INPUT_SCHEMA = {
    "type": "object",
    "required": ["name", "contact", "summary", "experience", "skills"],
    "properties": {
        "name": {"type": "string"},
        "title": {"type": "string"},
        "contact": {
            "type": "object",
            "required": ["email"],
            "properties": {
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["label", "url"],
                        "properties": {
                            "label": {"type": "string"},
                            "url": {"type": "string"},
                        },
                    },
                },
            },
        },
        "summary": {
            "type": "array",
            "items": {"type": "string"},
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["company", "role", "dates", "bullets"],
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "location": {"type": "string"},
                    "dates": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "bullets"],
                "properties": {
                    "name": {"type": "string"},
                    "link": {"type": "string"},
                    "dates": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["school", "degree", "dates"],
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "location": {"type": "string"},
                    "dates": {"type": "string"},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "skills": {
            "type": "object",
            "required": ["groups"],
            "properties": {
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "items"],
                        "properties": {
                            "name": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                }
            },
        },
        "certifications": {
            "type": "array",
            "items": {"type": "string"},
        },
        "awards": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["name", "title", "contact", "summary", "experience", "skills"],
    "properties": {
        "name": {"type": "string"},
        "title": {"type": "string"},
        "contact": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "url": {"type": "string"},
                        },
                    },
                },
            },
        },
        "summary": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "location": {"type": "string"},
                    "dates": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "link": {"type": "string"},
                    "dates": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "school": {"type": "string"},
                    "degree": {"type": "string"},
                    "location": {"type": "string"},
                    "dates": {"type": "string"},
                    "details": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "skills": {
            "type": "object",
            "properties": {
                "groups": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                }
            },
        },
        "certifications": {"type": "array", "items": {"type": "string"}},
        "awards": {"type": "array", "items": {"type": "string"}},
        "metrics": {
            "type": "object",
            "properties": {
                "word_count": {"type": "integer"},
                "page_count": {"type": "integer"},
                "source_format": {"type": "string"},
                "extracted_fonts": {
                    "type": "object",
                    "properties": {
                        "family": {"type": "string"},
                        "detected_sizes": {
                            "type": "object",
                            "additionalProperties": {"type": "integer"},
                        },
                    },
                },
                "margins": {
                    "type": "object",
                    "properties": {
                        "top": {"type": "number"},
                        "bottom": {"type": "number"},
                        "left": {"type": "number"},
                        "right": {"type": "number"},
                    },
                },
                "extraction_timestamp": {"type": "string"},
            },
        },
    },
}


def validate_input_cv(data: dict) -> None:
    try:
        validate(instance=data, schema=CV_INPUT_SCHEMA)
    except ValidationError as exc:
        raise ValueError(f"CV JSON validation error: {exc.message}") from exc


def validate_output_cv(data: dict) -> None:
    try:
        validate(instance=data, schema=OUTPUT_SCHEMA)
    except ValidationError as exc:
        raise ValueError(f"Generated CV validation error: {exc.message}") from exc
