from __future__ import annotations

from pathlib import Path
from typing import Dict, Union

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel


class DINOv3Encoder:
    """
    Frozen DINOv3 ViT-S/16 feature extractor.

    Returns:
        pooled:
            Global image representation from DINOv3.

        cls:
            CLS token.

        registers:
            Four DINOv3 register tokens.

        patches:
            Spatial patch tokens only.

    For a standard 224x224 ViT-S/16 input:
        CLS       = 1 token
        Registers = 4 tokens
        Patches   = 196 tokens (14 x 14)
    """

    def __init__(
        self,
        model_name: str = "facebook/dinov3-vits16-pretrain-lvd1689m",
        device: str | None = None,
        dtype: torch.dtype = torch.float16,
    ) -> None:

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device)

        if self.device.type == "cpu":
            dtype = torch.float32

        self.dtype = dtype
        self.model_name = model_name

        print(f"Loading processor: {model_name}")

        self.processor = AutoImageProcessor.from_pretrained(
            model_name
        )

        print(f"Loading model: {model_name}")

        self.model = AutoModel.from_pretrained(
            model_name
        )

        self.model = self.model.to(self.device)

        if self.device.type == "cuda":
            self.model = self.model.to(dtype=self.dtype)

        self.model.eval()

        # Freeze the model completely.
        for parameter in self.model.parameters():
            parameter.requires_grad = False

        print(f"Model loaded on: {self.device}")
        print(f"Model dtype: {self.dtype}")

    @torch.inference_mode()
    def encode(
        self,
        image: Union[Image.Image, str, Path],
    ) -> Dict[str, torch.Tensor]:

        # --------------------------------------------------
        # Load image
        # --------------------------------------------------

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        else:
            image = image.convert("RGB")

        # --------------------------------------------------
        # Preprocess
        # --------------------------------------------------

        inputs = self.processor(
            images=image,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        # Convert floating-point inputs to FP16 on GPU.
        if self.device.type == "cuda":
            inputs = {
                key: (
                    value.to(dtype=self.dtype)
                    if value.is_floating_point()
                    else value
                )
                for key, value in inputs.items()
            }

        # --------------------------------------------------
        # Forward pass
        # --------------------------------------------------

        outputs = self.model(**inputs)

        last_hidden = outputs.last_hidden_state

        # DINOv3 ViT structure:
        #
        # token 0        = CLS
        # tokens 1:5     = 4 register tokens
        # tokens 5:end   = spatial patch tokens
        #
        # For 224x224 with patch size 16:
        # 1 + 4 + 196 = 201 tokens

        cls_token = last_hidden[:, 0, :]

        register_tokens = last_hidden[:, 1:5, :]

        patch_tokens = last_hidden[:, 5:, :]

        # Official pooled representation.
        pooled = outputs.pooler_output

        # --------------------------------------------------
        # Return CPU float32 tensors
        # --------------------------------------------------
        #
        # We intentionally move them to CPU so the feature
        # extraction process doesn't accumulate GPU memory.

        return {
            "pooled": pooled.detach().float().cpu(),
            "cls": cls_token.detach().float().cpu(),
            "registers": register_tokens.detach().float().cpu(),
            "patches": patch_tokens.detach().float().cpu(),
        }


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Extract DINOv3 features from one image."
    )

    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to input image.",
    )

    args = parser.parse_args()

    encoder = DINOv3Encoder()

    features = encoder.encode(args.image)

    print("\n=== DINOv3 Feature Extraction ===")

    print("Image:")
    print(args.image)

    print("\nFeature shapes:")

    print(
        "Pooled:",
        tuple(features["pooled"].shape)
    )

    print(
        "CLS:",
        tuple(features["cls"].shape)
    )

    print(
        "Registers:",
        tuple(features["registers"].shape)
    )

    print(
        "Patches:",
        tuple(features["patches"].shape)
    )