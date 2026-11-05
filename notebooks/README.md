# Notebooks

Exploration and visualization only. Anything reused moves into `src/proto_star/`.

- Naming: `NN_initials_topic.ipynb` (e.g. `01_mp_eda.ipynb`)
- Launch: `uv run jupyter lab`
- Outputs are stripped on commit (nbstripout pre-commit hook)
- Load data through the package (`proto_star.data.load`) so notebooks and training see the same data
