# Workflow Patch Rules

- Keep original workflow sources unchanged.
- Generate or patch run-local workflow copies only.
- Preserve generated `.wl` or `.py` files inside each case directory, not in one shared flat folder.
- Include attempt context in generated workflow headers when retry strategy changes.
- Record which workflow path actually ran in `case_run_result.json`.
- Keep Python fallback bounded and explicit.
- Retry with different solve strategies across attempts instead of blindly rerunning the same workflow.
