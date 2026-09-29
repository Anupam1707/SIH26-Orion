"""
pipeline — End-to-End Input-to-Leads Processing Pipeline
SIH PS 189 · I4C / Ministry of Home Affairs

Transforms raw multi-source inputs (FIR text, CDR feeds, Transaction streams)
into validated, explainable, and Section 63 BSA-certified investigative leads.
"""

from .run_pipeline import run_input_to_leads_pipeline

__all__ = ["run_input_to_leads_pipeline"]
