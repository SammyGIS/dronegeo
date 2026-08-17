# JOSS Publication Submission Package: `DroneGeo`

This directory contains the complete publication package for submitting **DroneGeo** to the [Journal of Open Source Software (JOSS)](https://joss.theoj.org/).

---

## 📁 Directory Contents

| File | Purpose |
| :--- | :--- |
| **[`paper.md`](paper.md)** | Main JOSS manuscript in Markdown format, with YAML metadata, statement of need, research application, architecture, and JOSS 2026 AI disclosure statement. |
| **[`paper.bib`](paper.bib)** | BibTeX bibliography containing DOIs and citations for all referenced scientific literature and foundational libraries. |
| **[`figure1_pipeline.png`](figure1_pipeline.png)** | High-resolution publication schematic (300 DPI) visualizing DroneGeo's end-to-end processing pipeline. |
| **[`generate_figures.py`](generate_figures.py)** | Standalone Python script to regenerate publication-quality figures. |

---

## 🚀 How to Submit to JOSS

1. **Verify Online Repository State**:
   - Ensure the repository is public on GitHub: [https://github.com/SammyGIS/dronegeo](https://github.com/SammyGIS/dronegeo).
   - Ensure tests are passing on CI.
   - Ensure documentation is deployed and accessible: [https://sammygis.github.io/dronegeo/](https://sammygis.github.io/dronegeo/).

2. **Test Paper Compilation Locally or via Whedon**:
   - You can test compilation locally using the official JOSS Docker image (`openjournals/inara`):
     ```bash
     docker run --rm -v $(pwd):/data openjournals/inara -p -o pdf paper/paper.md
     ```
   - Or test on the web at [https://whedon.theoj.org/](https://whedon.theoj.org/).

3. **Submit Paper**:
   - Visit [https://joss.theoj.org/papers/new](https://joss.theoj.org/papers/new).
   - Provide the repository URL: `https://github.com/SammyGIS/dronegeo`
   - Specify the branch name and paper path: `paper/paper.md`
   - Specify software title, version, and primary research track (Earth Sciences / GIS / Remote Sensing).
