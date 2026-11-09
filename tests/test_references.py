"""Nearest normal reference photos: ranking, missing index and independence from the verdict."""

import numpy as np
import torch

from backend.references import ReferenceIndex, descriptor


def write_index(folder, vectors):
    folder.mkdir(parents=True, exist_ok=True)
    ids = np.array([f"pcb1/{i:02d}" for i in range(len(vectors))])
    np.savez_compressed(folder / "pcb1.npz", ids=ids, descriptors=np.asarray(vectors, dtype="float16"))


def test_the_descriptor_is_unit_length_and_uses_only_foreground_patches():
    tokens = torch.tensor([[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])
    value = descriptor(tokens, np.array([True, False, False]))
    assert torch.allclose(value, torch.tensor([1.0, 0.0]))
    assert torch.isclose(descriptor(tokens, np.array([False, False, False])).norm(), torch.tensor(1.0))


def test_the_closest_references_come_first(tmp_path):
    write_index(tmp_path, [[1, 0], [0, 1], [0.9, 0.1]])
    index = ReferenceIndex(tmp_path)
    tokens = torch.tensor([[1.0, 0.05]] * 4)
    found = index.nearest("pcb1", tokens, np.ones(4, dtype=bool), k=2)
    assert [item["id"] for item in found] == ["pcb1/00", "pcb1/02"]
    assert found[0]["similarity"] >= found[1]["similarity"] > 0.9


def test_a_product_without_an_index_gives_no_references(tmp_path):
    index = ReferenceIndex(tmp_path)
    assert index.nearest("candle", torch.ones(3, 2), np.ones(3, dtype=bool)) == []


def test_asking_for_more_than_exist_returns_all(tmp_path):
    write_index(tmp_path, [[1, 0], [0, 1]])
    found = ReferenceIndex(tmp_path).nearest("pcb1", torch.tensor([[1.0, 1.0]]), np.ones(1, dtype=bool), k=5)
    assert len(found) == 2
