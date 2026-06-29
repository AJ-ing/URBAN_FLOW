# UrbanFlow — Repository Cleanup Report

Generated: 2026-06-22

---

## Deletion Candidates

### 1. Duplicate Root-Level Config
- **File**: `adaptive_params.json` (root)
- **Reason**: Identical duplicate of `configs/adaptive_params.json`.
- **Dependency check**: **Zero dependencies** — loader reads from `configs/`. Safe to delete (deleted in previous phase).

### 2. Auto-Generated CSV Export Artifacts
- **Files**:
  - `urbanflow_autoexport_20260622_203606.csv` (latest runtime export)
  - 11 older CSV exports (`urbanflow_autoexport_*.csv`, `urbanflow_export_*.csv`)
- **Reason**: Written at runtime by `DataLogger` and `CSVExporter`. These are build/runtime artifacts and should not be in the repository.
- **Dependency check**: **Zero dependencies** — not imported or referenced. Safe to delete.

### 3. Duplicate `src/urbanflow/` Mirror
- **Reason**: All files were duplicate mirrors of root modules with no active imports.
- **Dependency check**: **Zero dependencies** — deleted in previous phase.

### 4. Empty Directories
- **Directories**: `scripts/`
- **Reason**: Empty and unused.
- **Dependency check**: **Zero dependencies** — deleted.

---

## Dependency Verification

```bash
grep -r "from src.urbanflow" . --include="*.py"  # → 0 results
grep -r "import src.urbanflow" . --include="*.py"  # → 0 results
```

---

## Summary

| Category | Files | Status |
|----------|-------|--------|
| Duplicate config | 1 | Deleted |
| CSV export artifacts | 12 | Deletion pending / Deleted |
| Duplicate src/ mirror | 33 | Deleted |
| Empty directories | 1 | Deleted |
