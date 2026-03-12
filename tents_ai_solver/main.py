import sys                                          # FIX: was missing
from PyQt5.QtWidgets import QApplication            # FIX: was missing
from ai_logic import AILogic
from gui import GameGUI
from game_state import GameState


def main():
    app = QApplication(sys.argv)
    G = GameState(8)
    ai = AILogic(G)
    gui = GameGUI(G, ai)                            # FIX: was GameGUI(G, None, ai)
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
