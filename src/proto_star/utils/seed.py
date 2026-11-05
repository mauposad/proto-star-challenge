import os
import random

import numpy as np


def set_seed(seed: int) -> None:
    """Seed every RNG we use so runs are reproducible."""
    random.seed(seed)
    np.random.seed(seed)  # noqa: NPY002 - seeds legacy global RNG used by some libraries
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
