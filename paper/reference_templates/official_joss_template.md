---
title: 'Author-Friendly Title of the Research Software'
tags:
  - Python
  - remote sensing
  - geospatial
  - quality control
authors:
  - name: First Author
    orcid: 0000-0000-0000-0000
    corresponding: true # (optional)
    equal-contrib: true # (optional)
    affiliation: "1, 2" # (matching affiliation index)
  - name: Second Author
    equal-contrib: true # (optional)
    affiliation: 2
  - name: Third Author
    affiliation: 1
affiliations:
  - name: Department of Earth Sciences, University of Example, Country
    index: 1
  - name: Institute for Remote Sensing and Applied GIS, Country
    index: 2
date: 17 August 2026
bibliography: paper.bib

# Optional fields if needed
# repository: https://github.com/org/repo
# archive_doi: 10.5281/zenodo.1234567
---

# Summary

A concise (1-2 paragraph) summary describing:
1. What the software is.
2. The core target audience (e.g. researchers, geoscientists, hydrologists).
3. The principal problems it solves.

# Statement of Need

A clear explanation of why this software was built and why existing tools are insufficient.
Highlight:
- Specific research bottlenecks in your field.
- Gaps in the existing software landscape.
- Key computational advantages (e.g., pure Python, automated diagnostics, memory-efficient spatial chunking).

# State of the Field & Research Impact

Compare your software against existing related tools in the scientific ecosystem.
A comparison table is strongly encouraged by JOSS reviewers:

| Feature / Metric | `YourSoftware` | `Alternative_A` | `Alternative_B` |
| :--- | :---: | :---: | :---: |
| **Language** | Python | C++ | Rust |
| **GUI Dependency** | None | Required | Optional |
| **Automated QC** | Native | Manual | None |

# Software Architecture & Key Features

Describe the key design principles, module structure, and algorithmic implementations:
- Submodule A: Data ingestion, point cloud parsing, CRS validation.
- Submodule B: Surface generation, interpolation algorithms.
- Submodule C: Hydrological flow direction and risk indices.

# Example Usage

Provide a short, copy-pasteable code snippet showing standard usage:

```python
import yoursoftware as ys

# 1. Load data
data = ys.load("sample.las")

# 2. Run analysis
results = ys.analyze(data)

# 3. Save outputs
results.export("output.tif")
```

# AI Usage Disclosure

*(Required for all submissions under the JOSS 2026 Policy)*
Disclose any use of Generative AI tools during development, testing, or manuscript drafting:
- **Tool(s) Used:** Name, version/model, and context of usage (e.g., docstring formatting, unit test scaffolding).
- **Scope & Nature of Assistance:** Detail the specific tasks assisted by AI.
- **Author Validation Statement:** Affirmation that human authors reviewed, verified, and take full scientific and ethical responsibility for all code, algorithms, and text.

# Acknowledgements

Acknowledge funding agencies, computing resources, and upstream open-source software libraries.

# References
