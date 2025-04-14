from PyQt5.QtWidgets import QApplication
from ui.music_card.window import MusicCardWindow


def init_app():
  app: QApplication = QApplication([])
  card_window: MusicCardWindow = MusicCardWindow(app)
  card_window.show()
  app.exec_()

# Run the app
if __name__ == "__main__":
  init_app()
