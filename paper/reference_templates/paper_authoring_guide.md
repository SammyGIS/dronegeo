# JOSS Paper Authoring & Markdown Reference Guide

The **Journal of Open Source Software (JOSS)** enforces specific structural, citation, and editorial conventions. This guide provides a quick reference for writing compliant `paper.md` manuscripts.

---

## 1. Frontmatter (YAML Header)

The YAML header at the beginning of `paper.md` is strictly parsed by Whedon / Inara.

```yaml
---
title: 'Title of the Software Package'
tags:
  - Python
  - remote sensing
  - LiDAR
authors:
  - name: Jane Doe
    orcid: 0000-0002-1825-0097
    corresponding: true
    affiliation: "1, 2"
  - name: John Smith
    orcid: 0000-0001-5109-3700
    affiliation: 2
affiliations:
  - name: Department of Earth Sciences, Stanford University, USA
    index: 1
  - name: Remote Sensing Laboratory, ETH Zurich, Switzerland
    index: 2
date: 17 August 2026
bibliography: paper.bib
---
```

---

## 2. Required Sections

JOSS papers are intentionally short (typically 1,000–2,500 words). They must focus on the **software itself**, its **architecture**, **statement of need**, and **research application**, rather than presenting novel experimental research findings.

### Mandatory Sections:
1. **Summary**: Brief elevator pitch describing the package, domain, and purpose.
2. **Statement of Need**: Why does this software exist? What specific scientific gaps does it fill that existing software does not?
3. **State of the Field**: How does it compare to other tools in the ecosystem? (Feature tables are highly appreciated by reviewers).
4. **Architecture / Design Overview**: High-level structural description of modules and algorithms.
5. **AI Usage Disclosure (JOSS 2026 Requirement)**:
   - Tool(s) used and models/versions.
   - Nature and scope of assistance (e.g. test scaffolding, refactoring, copy-editing).
   - Statement affirming human review and authorial responsibility.
6. **References**: Automatically populated from `paper.bib`.

---

## 3. Citations & BibTeX (`paper.bib`)

JOSS uses **Pandoc Citeproc** for citations:

- **In-text citation**: `@author2023` -> *Author (2023)*
- **Parenthetical citation**: `[@author2023]` -> *(Author, 2023)*
- **Multiple citations**: `[@author2023; @other2022]` -> *(Author, 2023; Other, 2022)*
- **With page or locator**: `[@author2023, pp. 45-48]` -> *(Author, 2023, pp. 45–48)*

### BibTeX Quality Standard:
Every entry in `paper.bib` should include a valid **DOI** wherever possible:
```bibtex
@article{harris2020numpy,
  title={{Array programming with NumPy}},
  author={Harris, Charles R. and Millman, K. Jarrod and others},
  journal={Nature},
  volume={585},
  number={7825},
  pages={357--362},
  year={2020},
  doi={10.1038/s41586-020-2649-2}
}
```

---

## 4. Figures & Code Listings

- **Figure syntax**:
  ```markdown
  ![Caption describing the architecture diagram or workflow.](figure1_pipeline.png)
  ```
  *(Keep figure files in the same directory as `paper.md` or a direct relative subfolder).*

- **Code syntax**:
  ```python
  import dronegeo as dg
  report = dg.autoqc.inspect_point_cloud("flight.las")
  ```

---

## 5. Local PDF Preview Options

1. **Docker (Official Inara compiler)**:
   ```bash
   docker run --rm -v $(pwd):/data openjournals/inara -p -o pdf paper/paper.md
   ```

2. **Online Whedon Web Service**:
   Upload your repository URL or branch to [https://whedon.theoj.org/](https://whedon.theoj.org/) for an instant preview.
