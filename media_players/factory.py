from abc import ABC, abstractmethod
from media_players.spotify import SpotifyMetadataWorker, SpotifyMetadataHandler, SpotifyPlaybackWorker
from media_players.fb2k import FB2KMetadataWorker, FB2KMetadataHandler, FB2KPlaybackWorker
from typing import TYPE_CHECKING

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from ui.music_card.card import MusicCard
  from ui.music_card.handlers import UpdateHandler
  from media_players.base import IMetadataWorker, IMetadataHandler, IPlaybackWorker

class IMediaPlayerFactory(ABC):
  @abstractmethod
  def create_metadata_worker(self) -> "IMetadataWorker":
    pass

  @abstractmethod
  def create_metadata_handler(self, card: "MusicCard", updater: "UpdateHandler") -> "IMetadataHandler":
    pass

  @abstractmethod
  def create_playback_worker(self, card: "MusicCard") -> "IPlaybackWorker":
    pass


class SpotifyFactory(IMediaPlayerFactory):
  def create_metadata_worker(self) -> "IMetadataWorker":
    return SpotifyMetadataWorker()

  def create_metadata_handler(self, card: "MusicCard", updater: "UpdateHandler") -> "IMetadataHandler":
    return SpotifyMetadataHandler(card, updater)

  def create_playback_worker(self, card: "MusicCard") -> "IPlaybackWorker":
    return SpotifyPlaybackWorker(card)


class FB2KFactory(IMediaPlayerFactory):
  def create_metadata_worker(self) -> "IMetadataWorker":
    return FB2KMetadataWorker()

  def create_metadata_handler(self, card: "MusicCard", updater: "UpdateHandler") -> "IMetadataHandler":
    return FB2KMetadataHandler(card, updater)

  def create_playback_worker(self, card: "MusicCard") -> "IPlaybackWorker":
    return FB2KPlaybackWorker(card)


def get_factory(media_player: str) -> IMediaPlayerFactory:
  if media_player == "spotify":
    return SpotifyFactory()
  elif media_player == "fb2k":
    return FB2KFactory()
  else:
    raise ValueError(f"Unknown media player: {media_player}")
