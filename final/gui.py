from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from game_state import *

class GameGUI(QWidget):
    def __init__(self, G, player, ai):
        super().__init__()
        self.G = G
        self.player = player
        self.ai = ai

        self.setWindowTitle("Tents Game – Player vs AI")

        self.cells = [[None]*G.size for _ in range(G.size)]
        layout = QVBoxLayout()
        self.score = QLabel()
        layout.addWidget(self.score)

        grid = QGridLayout()
        for r in range(G.size):
            for c in range(G.size):
                btn = QPushButton()
                btn.setFixedSize(45,45)
                btn.clicked.connect(lambda _, rr=r, cc=c: self.cell_clicked(rr, cc))
                self.cells[r][c] = btn
                grid.addWidget(btn, r, c)

        for r in range(G.size):
            grid.addWidget(QLabel(str(G.row_targets[r])), r, G.size)
        for c in range(G.size):
            grid.addWidget(QLabel(str(G.col_targets[c])), G.size, c)

        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self.restart)

        layout.addLayout(grid)
        layout.addWidget(self.restart_btn)
        self.setLayout(layout)
        self.update_board()

    def update_board(self):
        for r in range(self.G.size):
            for c in range(self.G.size):
                btn = self.cells[r][c]
                if self.G.board[r][c] == TREE:
                    btn.setText("🌳")
                elif self.G.board[r][c] == TENT:
                    btn.setText("⛺")
                else:
                    btn.setText("")
        self.score.setText(f"Player: {self.G.player_score}   AI: {self.ai.score}")

    def cell_clicked(self, r, c):
        if self.player.player_move(r, c):
            self.G.player_score += 1
            self.update_board()
            QTimer.singleShot(200, self.ai_turn)

    def ai_turn(self):
        if self.ai.ai_move():
            self.ai.score += 1
        self.update_board()

    def restart(self):
        self.G.generate_solvable_trees_and_targets()
        self.G.player_score = 0
        self.ai.score = 0
        self.update_board()