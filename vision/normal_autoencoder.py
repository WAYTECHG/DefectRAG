"""Small one-class head trained on frozen DINOv3 normal patch embeddings."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class NormalPatchAutoencoder(nn.Module):
    def __init__(self, dimension: int = 384, bottleneck: int = 96) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(dimension, 256), nn.GELU(),
            nn.Linear(256, bottleneck), nn.GELU(),
            nn.Linear(bottleneck, 256), nn.GELU(),
            nn.Linear(256, dimension),
        )

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        return F.normalize(
            self.network(F.normalize(patches.float(), dim=-1)),
            dim=-1,
        )


def reconstruction_distances(
    model: NormalPatchAutoencoder,
    patches: torch.Tensor,
) -> torch.Tensor:
    normalized = F.normalize(patches.float(), dim=-1)
    return 1.0 - F.cosine_similarity(
        model(normalized),
        normalized,
        dim=-1,
    )


def top_tenth_score(distances: torch.Tensor) -> float:
    count = max(1, int(distances.numel() * 0.10))
    return float(
        torch.topk(distances.flatten(), count).values.mean().item()
    )