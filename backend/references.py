"""Nearest normal reference photos: an explanation aid, never part of the verdict.

Each product has a small set of diverse normal training photos, each summarised by one descriptor (the unit-length mean
of its foreground patch features from the same encoder as the detector). For a new photo the same descriptor is
compared with them and the closest few are named in the result, so a person can look at a similar normal photo next
to the flagged one. The detector's score, threshold and verdict do not depend on any of this.
"""

from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F


def descriptor(tokens, mask):
    """Unit-length mean of the foreground patch features (all patches if the mask is empty)."""
    features = F.normalize(tokens.float(), dim=-1)
    keep = np.asarray(mask, dtype=bool)
    if keep.any():
        features = features[torch.as_tensor(keep, device=features.device)]
    return F.normalize(features.mean(0), dim=0)


class ReferenceIndex:
    """Loads references/<product>.npz lazily; a missing file simply means there are no references to show."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.loaded = {}

    def load(self, category, device):
        key = (category, str(device))
        if key not in self.loaded:
            path = self.directory / f"{category}.npz"
            if not path.exists():
                self.loaded[key] = None
            else:
                with np.load(path, allow_pickle=False) as saved:
                    ids = [str(i) for i in saved["ids"]]
                    vectors = torch.from_numpy(saved["descriptors"].astype("float32"))
                self.loaded[key] = (ids, F.normalize(vectors, dim=-1).to(device))
        return self.loaded[key]

    def nearest(self, category, tokens, mask, k=3):
        found = self.load(category, tokens.device)
        if found is None:
            return []
        ids, vectors = found
        similarity = vectors @ descriptor(tokens, mask)
        top = similarity.topk(min(k, len(ids)))
        return [{"id": ids[int(i)], "similarity": round(float(s), 4)} for s, i in zip(top.values, top.indices)]
