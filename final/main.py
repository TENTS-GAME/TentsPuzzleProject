import sys
from PyQt5.QtWidgets import QApplication
from game_state import GameState
from player_logic import PlayerLogic
from ai_logic import AILogic
from gui import GameGUI

def main():
    app = QApplication(sys.argv)

    G = GameState(8)
    player = PlayerLogic(G)
    ai = AILogic(G)

    gui = GameGUI(G, player, ai)
    gui.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
