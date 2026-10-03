from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn.functional as F

CATEGORIES = ("breakfast_box", "juice_bottle", "pushpins", "screw_bag", "splicing_connectors")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact normal-memory banks for cloud deployment.")
    parser.add_argument("--features", type=Path, default=Path("features"))
    parser.add_argument("--output", type=Path, default=Path("cloud/space/assets"))
    parser.add_argument("--max-patches", type=int, default=20_000)
    args = parser.parse_args()
    if args.max_patches < 1000:
        raise ValueError("--max-patches must be at least 1000.")
    args.output.mkdir(parents=True, exist_ok=True)
    generator = torch.Generator().manual_seed(42)

    for category in CATEGORIES:
        source = args.features / category / "train" / "good"
        files = sorted(source.glob("*.pt"))
        if not files:
            print(f"Skipping {category}: no feature files in {source}")
            continue
        patches = []
        for path in files:
            data = torch.load(path, map_location="cpu", weights_only=True)
            patches.append(data["patches"].squeeze(0).float())
        memory = torch.cat(patches, dim=0)
        if len(memory) > args.max_patches:
            memory = memory[torch.randperm(len(memory), generator=generator)[: args.max_patches]]
        memory = F.normalize(memory, p=2, dim=1).half().contiguous()
        destination = args.output / f"{category}.pt"
        torch.save({"category": category, "patches": memory, "source_files": len(files)}, destination)
        print(f"{category}: {tuple(memory.shape)} -> {destination} ({destination.stat().st_size / 1_048_576:.1f} MiB)")


if __name__ == "__main__":
    main()
