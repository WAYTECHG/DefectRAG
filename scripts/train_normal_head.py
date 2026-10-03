"""Train a one-class anomaly head without using LOCO AD test images or masks."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

from vision.normal_autoencoder import NormalPatchAutoencoder

CATEGORIES = (
    "breakfast_box",
    "juice_bottle",
    "pushpins",
    "screw_bag",
    "splicing_connectors",
)


def load_patches(
    paths: list[Path],
    max_patches: int,
    generator: torch.Generator,
) -> torch.Tensor:
    patches = []
    for path in paths:
        data = torch.load(path, map_location="cpu", weights_only=True)
        patches.append(
            F.normalize(data["patches"].squeeze(0).float(), dim=-1)
        )

    result = torch.cat(patches, dim=0)
    if len(result) > max_patches:
        indices = torch.randperm(
            len(result),
            generator=generator,
        )[:max_patches]
        result = result[indices]

    return result


def train_category(
    category: str,
    args: argparse.Namespace,
    device: torch.device,
) -> dict:
    paths = sorted(
        (args.features / category / "train" / "good").glob("*.pt")
    )
    if len(paths) < 10:
        raise ValueError(
            f"{category} requires at least 10 normal image feature files; "
            f"found {len(paths)}"
        )

    rng = random.Random(args.seed)
    rng.shuffle(paths)

    split = max(1, round(len(paths) * args.val_fraction))
    val_paths, train_paths = paths[:split], paths[split:]

    generator = torch.Generator().manual_seed(args.seed)
    train = load_patches(
        train_paths,
        args.max_train_patches,
        generator,
    )
    val = load_patches(
        val_paths,
        args.max_val_patches,
        generator,
    )

    if train.shape[1] != val.shape[1]:
        raise ValueError("Feature dimensions do not match")

    model = NormalPatchAutoencoder(
        dimension=train.shape[1],
        bottleneck=args.bottleneck,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=1e-4,
    )
    loader = DataLoader(
        TensorDataset(train),
        batch_size=args.batch_size,
        shuffle=True,
        generator=generator,
    )

    best_loss = float("inf")
    best_epoch = 0
    patience_left = args.patience
    history = []

    args.output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.output / f"{category}_head.pt"

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []

        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad(set_to_none=True)

            output = model(batch)
            loss = (
                1.0 - F.cosine_similarity(output, batch, dim=-1)
            ).mean()

            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))

        model.eval()
        with torch.inference_mode():
            val_losses = []
            for batch in val.split(args.batch_size):
                batch = batch.to(device)
                output = model(batch)
                val_loss_batch = (
                    1.0 - F.cosine_similarity(output, batch, dim=-1)
                ).mean()
                val_losses.append(float(val_loss_batch.item()))

        val_loss = sum(val_losses) / len(val_losses)
        train_loss = sum(losses) / len(losses)

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
        })
        print(
            f"{category} epoch {epoch:02d}: "
            f"train={train_loss:.6f} val={val_loss:.6f}",
            flush=True,
        )

        if val_loss < best_loss - 1e-5:
            best_loss = val_loss
            best_epoch = epoch
            patience_left = args.patience

            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "dimension": train.shape[1],
                    "bottleneck": args.bottleneck,
                    "category": category,
                    "best_epoch": epoch,
                    "seed": args.seed,
                    "train_images": len(train_paths),
                    "val_images": len(val_paths),
                },
                checkpoint_path,
            )
        else:
            patience_left -= 1
            if patience_left == 0:
                break

    return {
        "category": category,
        "best_epoch": best_epoch,
        "best_normal_val_loss": best_loss,
        "train_images": len(train_paths),
        "val_images": len(val_paths),
        "train_patches": len(train),
        "val_patches": len(val),
        "history": history,
        "checkpoint": str(checkpoint_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("features"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("cloud/space/assets"),
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--bottleneck", type=int, default=96)
    parser.add_argument("--val-fraction", type=float, default=0.10)
    parser.add_argument("--max-train-patches", type=int, default=100_000)
    parser.add_argument("--max-val-patches", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if (
        not 0 < args.val_fraction < 0.5
        or min(
            args.epochs,
            args.patience,
            args.batch_size,
            args.max_train_patches,
            args.max_val_patches,
        ) < 1
    ):
        parser.error("invalid training settings")

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    print(
        f"Training small anomaly heads on {device}; "
        "DINOv3 stays frozen."
    )

    reports = [
        train_category(category, args, device)
        for category in CATEGORIES
    ]
    (args.output / "training_summary.json").write_text(
        json.dumps(reports, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()