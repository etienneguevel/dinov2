import os
from pathlib import Path

from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from dinov2.data.datasets import ImageDataset


def test_single_path():
    path_dataset_test = Path(__file__).parent / "dataset1"
    transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    dataset = ImageDataset(path_dataset_test, transform=transform)

    dataloader = DataLoader(dataset, batch_size=32)
    for i in dataloader:
        assert len(i) == 32
        break


base_path = Path(os.getcwd())
dirs = ["dataset1", "dataset2"]


def test_several_paths():
    transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.226]),
        ]
    )

    dataset = ImageDataset(root=dirs, transform=transform)

    expected_length = len(
        [
            f
            for d in dirs
            for d, _, files in os.walk(d)
            for f in files
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".tiff"))
        ]
    )
    assert dataset.__len__() == expected_length

    dataloader = DataLoader(dataset, batch_size=32)
    for i in dataloader:
        assert len(i) == 32
        break


if __name__ == "__main__":
    test_single_path()
    test_several_paths()
