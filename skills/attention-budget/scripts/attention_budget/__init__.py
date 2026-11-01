"""attention-budget: measure what an agent makes a human read, and enforce a budget.

Every reply an agent sends a human is one of four kinds (decision, status, closure,
explanation), each with its own word budget. Terms the reader has never used and the
agent did not expand count as breaches. Enforcement is measured after the fact, never
requested in a prompt. Stdlib only; no LLM in this path.
"""
__version__ = "0.1.0"
