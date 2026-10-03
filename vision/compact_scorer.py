"""Local scoring using the same compact normal bank and one-class head as the Space."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from vision.normal_autoencoder import NormalPatchAutoencoder, reconstruction_distances, top_tenth_score


class CompactDINOv3Scorer:
    def __init__(self, category: str, encoder, memory_path: Path, head_path: Path | None = None) -> None:
        self.encoder = encoder
        self.device = encoder.device
        saved = torch.load(memory_path, map_location="cpu", weights_only=True)
        if saved.get("category") != category:
            raise ValueError(f"Compact normal-memory category mismatch: {memory_path}")
        memory = saved["patches"]
        if memory.ndim != 2 or memory.shape[0] == 0:
            raise ValueError(f"Invalid compact normal-memory shape: {memory_path}")
        self.memory_bank = F.normalize(memory.float().to(self.device), p=2, dim=1)
        self.head = None
        if head_path is not None and head_path.is_file():
            checkpoint = torch.load(head_path, map_location="cpu", weights_only=True)
            if checkpoint.get("category") != category or checkpoint.get("dimension") != memory.shape[1]:
                raise ValueError(f"Trained head does not match the {category} bank: {head_path}")
            self.head = NormalPatchAutoencoder(checkpoint["dimension"], checkpoint["bottleneck"])
            self.head.load_state_dict(checkpoint["state_dict"])
            self.head = self.head.eval().to(self.device)
        self.available_methods = ("baseline", "trained", "fusion") if self.head is not None else ("baseline",)

    @torch.inference_mode()
    def score_image(self, image_path: str | Path, method: str = "baseline") -> dict:
        if method not in self.available_methods:
            raise ValueError(f"The {method} method needs a seed 42 trained head for this product.")
        patches = F.normalize(self.encoder.encode(image_path)["patches"].squeeze(0).float().to(self.device), p=2, dim=1)
        if patches.ndim != 2 or patches.shape[1] != self.memory_bank.shape[1]:
            raise ValueError("DINOv3 patch dimensions do not match the compact normal memory.")
        baseline = torch.cat([1.0 - (chunk @ self.memory_bank.T).max(dim=1).values for chunk in patches.split(64)])
        maps = {"baseline": baseline}
        if self.head is not None:
            trained = reconstruction_distances(self.head, patches)
            maps.update(trained=trained, fusion=(baseline + trained) / 2.0)
        selected = maps[method]
        grid = int(selected.numel() ** .5)
        if grid * grid != selected.numel():
            raise ValueError("DINOv3 did not produce a square patch grid.")
        raw_map = selected.reshape(grid, grid).cpu().numpy()
        low, high = float(raw_map.min()), float(raw_map.max())
        display_map = (raw_map - low) / (high - low) if high > low else np.zeros_like(raw_map)
        best = int(selected.argmax().item())
        return {
            "anomaly_score": top_tenth_score(selected),
            "comparison_scores": {name: top_tenth_score(values) for name, values in maps.items()},
            "anomaly_map": display_map,
            "max_patch": (best // grid, best % grid),
        }
