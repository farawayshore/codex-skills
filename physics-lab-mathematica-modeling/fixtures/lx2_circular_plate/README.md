# LX2 Circular Plate Fixture

This fixture is a regression example for `physics-lab-mathematica-modeling`.

Use it to confirm that the generic `run_config.json` contract can represent a real experiment without hardcoding LX2-specific logic into the shared runner, validator, or workflow builder.

This fixture is not the center of the skill. It is only:

- an example input contract
- an example batch-discovery contract
- an example handout-only extra case
- an example handout-expectation shape
- a reminder that real experiments can still fit the generic artifact-only workflow

Keep LX2-specific physics assumptions inside fixture examples or experiment-local workflow files, not inside the generic orchestration code.

The sample config is batch-first:

- it discovers all required `m,n` cases from the LX2 picture-result folder
- it merges an extra handout-only case
- it uses strict batch success
- it allows up to `3 Mathematica` plus `3 Python` retries per case
