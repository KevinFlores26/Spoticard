import base64, re
from abc import ABC, abstractmethod
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from typing import Union, TYPE_CHECKING, get_args

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  import mutagen

BASE64_IMAGE_REGEX = r"^data:image\/[a-zA-Z0-9+.-]+;base64,"
EmbeddedImage: Union = Union[
  str,
  bytes,
  mutagen.id3.APIC,
  mutagen.mp4.MP4Cover,
  mutagen.flac.Picture,
]

class IImageExtractor(ABC):
  """
  Abstract base class for extracting embedded album art from audio files
  """
  @abstractmethod
  def extract_image(self, filepath: str) -> bytes | str | None:
    pass

  @staticmethod
  def get_available_image(images: list[EmbeddedImage], img_index: int = 0) -> EmbeddedImage:
    found_image: EmbeddedImage = ''

    for i, image in enumerate(images):
      if not isinstance(image, get_args(EmbeddedImage)):
        continue
      if isinstance(image, str) and not re.match(BASE64_IMAGE_REGEX, image):
        continue # continue if not a valid base64 encoded image

      found_image = image
      if found_image and img_index == i:
        return found_image

    if (img_index + 1) > len(images):
      return found_image # if index is out of bounds, return the last found image and an empty string if no image was found

    return images[0] # return the first image if index was not found

  @staticmethod
  def convert_image_to_bytes(image) -> bytes | None:
    if isinstance(image, bytes):
      return image

    if isinstance(image, str) and re.match(BASE64_IMAGE_REGEX, image):
      return base64.b64decode(image.split(",")[1])

    if isinstance(image, (mutagen.id3.APIC, mutagen.flac.Picture)) and hasattr(image, "data"):
      return image.data

    if isinstance(image, mutagen.mp4.MP4Cover) and hasattr(image, "data"):
      return bytes(image)


"""Extractors"""
class MP3Extractor(IImageExtractor):
  def extract_image(self, filepath: str) -> bytes | None:
    audio: MP3 = MP3(filepath, ID3=ID3)
    images: list[mutagen.id3.APIC] = [ ]

    for tag in audio.tags.values():
      if hasattr(tag, "data") or tag.__class__.__name__ == "APIC":
        images.append(tag)

    image: EmbeddedImage = self.get_available_image(images)
    return self.convert_image_to_bytes(image)


class FLACExtractor(IImageExtractor):
  def extract_image(self, filepath: str) -> bytes | None:
    audio: FLAC = FLAC(filepath)
    images: list[mutagen.flac.Picture] = [ ]

    for tag in audio.pictures:
      if hasattr(tag, "data") or tag.__class__.__name__ == "Picture":
        images.append(tag)

    image: EmbeddedImage = self.get_available_image(images)
    return self.convert_image_to_bytes(image)


class MP4Extractor(IImageExtractor):
  def extract_image(self, filepath: str) -> bytes | None:
    audio = MP4(filepath)
    images: list[mutagen.mp4.MP4Cover] = [cover for cover in audio.tags.get("covr", [ ])]

    image: EmbeddedImage = self.get_available_image(images)
    return self.convert_image_to_bytes(image)


class OggExtractor(IImageExtractor):
  def extract_image(self, filepath: str) -> bytes | None:
    audio: OggVorbis | OggOpus = OggVorbis(filepath) if filepath.endswith(".ogg") else OggOpus(filepath)
    images: list[EmbeddedImage] = [pict for pict in audio.get("metadata_block_picture", [ ])]

    image: EmbeddedImage = self.get_available_image(images)
    return self.convert_image_to_bytes(image)


class ImageExtractorFactory:
  """
  Factory for creating the correct extractor based on file extension
  """
  extractors = {
    ".mp3": MP3Extractor,
    ".flac": FLACExtractor,
    ".m4a": MP4Extractor,
    ".mp4": MP4Extractor,
    ".ogg": OggExtractor,
    ".opus": OggExtractor,
  }

  @classmethod
  def get_extractor(cls, filepath: str) -> IImageExtractor | None:
    for ext, extractor in cls.extractors.items():
      if filepath.endswith(ext):
        return extractor()

    return None


def extract_embedded_image(filepath: str) -> bytes | None:
  extractor = ImageExtractorFactory.get_extractor(filepath)
  return extractor.extract_image(filepath) if extractor else None
