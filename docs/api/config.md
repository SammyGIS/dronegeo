# Hardware & Compute Configuration API (`dronegeo.config`)

Multi-core CPU scaling, memory chunk buffering, and scoped execution context managers.

---

### `dronegeo.config.set_compute_profile`
???+ func "<span class='swagger-badge badge-func'>FUNCTION</span> `dg.set_compute_profile(profile_name) -> ComputeConfig`"

    **Overview & Real-World Use Case:**  
    Applies global hardware optimization presets:
    - `"maximum"`: Uses all available CPU cores and large 2M point buffers for workstation batch processing.
    - `"balanced"`: Uses $N-1$ cores to ensure system responsiveness during survey processing.
    - `"low_memory"`: Restricts memory buffer to 250k points for field laptops with $\le 8\text{GB}$ RAM.

---

### `dronegeo.config.compute_context`
??? func "<span class='swagger-badge badge-context'>CONTEXT MANAGER</span> `dg.compute_context(n_jobs=None, chunk_size=None, low_memory_mode=None)`"

    **Overview & Real-World Use Case:**  
    Scoped context manager that temporarily applies custom CPU worker counts and RAM chunking configurations to an isolated code block, automatically restoring previous settings upon exit.

---

## Full Module Docstrings

::: dronegeo.config.compute
    options:
      members:
        - set_compute_profile
        - compute_context
        - get_compute_config
        - reset_compute_config
        - ComputeConfig
        - ComputeProfile
