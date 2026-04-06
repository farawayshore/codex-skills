# Course Lab Finalize QC Baseline Failures

- No standalone `course-lab-finalize-qc` skill package exists yet.
- Final compile and QC behavior still lives in the parent report skill instead of a focused leaf skill.
- There is no local copied compile-and-QC toolchain under one finalize-QC folder.
- PDF-size checking is not isolated behind a dedicated final-QC contract.
- Compiled PDF page count is not recorded as a visible soft QC warning against the preferred `20-30` page band.
- Final handoff gaps are not emitted through a dedicated standalone package.
