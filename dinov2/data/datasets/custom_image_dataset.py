import os
import random
import pandas as pd

from typing import List, Optional
from pathlib import PosixPath
from omegaconf.listconfig import ListConfig
from torch.utils.data import Dataset
from .decoders import ImageDataDecoder


class ImageDataset(Dataset):
    def __init__(
        self,
        root,
        transform=None,
        path_preserved: List[str] = [],
        frac: float = 0.1,
        is_valid=True,
    ):
        self.root = root
        self.transform = transform
        self.path_preserved = path_preserved if isinstance(path_preserved, (list, ListConfig)) else [path_preserved]
        self.frac = frac
        self.preserved_images = []
        self.is_valid = is_valid
        self.images_list = self._get_images(root)

    def _get_images(self, path):
        images = []
        match path:
            case str() | PosixPath():
                p = path
                preserve = p in self.path_preserved
                try:
                    images.extend(
                        self._retrieve_from_path(p, preserve=preserve, frac=self.frac, is_valid=self.is_valid)
                    )
                except OSError:
                    print(f"the path indicated at {p} cannot be found.")

            case list():
                for p in path:
                    images.extend(self._get_images(p))

            case _:
                raise SyntaxError("The entry is neither a list or a str")

        return images

    def _retrieve_from_path(self, path, is_valid=True, preserve=False, frac=1):
        images_ini = len(self.preserved_images)
        images = []
        for root, _, files in os.walk(path):
            images_dir = []
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".tiff")):
                    im = os.path.join(root, file)
                    if is_valid:
                        try:
                            with open(im, "rb") as f:
                                image_data = f.read()
                            ImageDataDecoder(image_data).decode()
                            images_dir.append(im)

                        except OSError:
                            print(f"Image at path {im} could not be opened.")
                    else:
                        images_dir.append(im)

            if preserve:
                random.seed(24)
                random.shuffle(images_dir)
                split_index = int(len(images_dir) * frac)
                self.preserved_images.extend(images_dir[:split_index])
                images.extend(images_dir[split_index:])

            else:
                images.extend(images_dir)

        images_end = len(self.preserved_images)
        if preserve:
            print(f"{images_end - images_ini} images have been saved for the dataset at path {path}")

        return images

    def _get_image_data(self, index: int):
        path = self.images_list[index]
        with open(path, "rb") as f:
            image_data = f.read()

        return image_data

    def __len__(self) -> int:
        return len(self.images_list)

    def __getitem__(self, index: int):
        try:
            image_data = self._get_image_data(index)
            image = ImageDataDecoder(image_data).decode()
        except Exception as e:
            raise RuntimeError(f"Can nor read image for sample {index}") from e
        if self.transform is not None:
            image = self.transform(image)

        return image


class LabelledDataset(Dataset):
    def __init__(
        self,
        data_path: str,
        root: Optional[str] = None,
        transform=None,
    ):
        self.root = root
        self.transform = transform
        self.images_list, self.labels = self._get_images_and_labels(data_path)
        self.translate_dict = self._make_translate_dict()

    def _get_images_and_labels(self, data_path: str) -> tuple[list]:
        match data_path:
            case str() | PosixPath() as s if str(s).endswith(".csv"):
                df = pd.read_csv(data_path)
                images_list, labels = df["names"].tolist(), df["pseudo_labels"].tolist()

                if self.root:
                    images_list = [os.path.join(self.root, im.split("/")[-1]) for im in images_list]

            case str() | PosixPath() as s if os.path.isdir(s):
                images_list, labels = [], []
                folders = [e for e in os.listdir(s) if os.path.isdir(os.path.join(s, e))]
                for f in folders:
                    images = [
                        os.path.join(s, f, im)
                        for im in os.listdir(os.path.join(s, f))
                        if im.endswith((".png", ".jpg", ".jpeg", ".tiff"))
                    ]
                    images_list.extend(images)
                    labels.extend([f] * len(images))

            case _:
                raise SyntaxError("The data_path format isn't recognized.")

        return images_list, labels

    def _make_translate_dict(self):

        return {label: i for i, label in enumerate(set(self.labels))}

    def _get_image_data(self, index: int):
        path = self.images_list[index]
        with open(path, "rb") as f:
            image_data = f.read()

        return image_data

    def __len__(self) -> int:
        return len(self.images_list)

    def __getitem__(self, index: int):
        try:
            image_data = self._get_image_data(index)
            label = self.translate_dict[self.labels[index]]
            image = ImageDataDecoder(image_data).decode()
        except Exception as e:
            raise RuntimeError(f"can not read image for sample {index}") from e

        if self.transform is not None:
            image = self.transform(image)

        return image, label
