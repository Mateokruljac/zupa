# Target data architecture (intent)

**Primary:** `MDs/DB_ARCHITECTURE_PROPOSAL.md`  
**Bases:** `core/models.py`

1. Every business model is DIM SCD1 / SCD2 / SCD2A or FACT FCTA (FCTB only if volume requires it).
2. **Person** is SCD1. **Household** is SCD2A. **HouseholdMembership** is SCD2.
3. Sacraments and register lines are **FCTA**. Books are **SCD1**.
4. Finance: one cashbook **FCTA**, four ledger codes.
5. Calendar events and tasks are two **FCTA** models.
6. Public submissions are **FCTA** intake, never auto-locked registers.
7. Inherit `core.models`; call `save_new` for SCD; `content_hash` is on the bases.
