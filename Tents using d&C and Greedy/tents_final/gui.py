from PyQt5.QtWidgets import (QWidget, QPushButton, QGridLayout, QVBoxLayout,
                              QLabel, QMessageBox, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from game_state import *

class GameGUI(QWidget):
    def __init__(self, G, player, ai):
        super().__init__()
        self.G = G
        self.player = player
        self.ai = ai
        self.game_over_shown = False
        self.player_turn = True  # Player goes first

        self.setWindowTitle("Tents Game – Player vs AI")
        self.setStyleSheet("""
            QWidget { background-color: #1a2634; }
            QPushButton {
                border-radius: 4px;
                font-size: 20px;
                border: 1px solid #2e4057;
                background-color: #243447;
                color: white;
            }
            QPushButton:hover { background-color: #2e5077; }
            QLabel { color: #cdd6e0; font-size: 14px; }
        """)

        self.cells = [[None]*G.size for _ in range(G.size)]
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Score bar
        score_frame = QFrame()
        score_frame.setStyleSheet("background: #0f1923; border-radius: 8px; padding: 6px;")
        score_layout = QHBoxLayout(score_frame)
        self.player_score_lbl = QLabel("🧑 Player: 0")
        self.player_score_lbl.setFont(QFont("Arial", 16, QFont.Bold))
        self.player_score_lbl.setStyleSheet("color: #4fc3f7;")
        self.ai_score_lbl = QLabel("🤖 AI: 0")
        self.ai_score_lbl.setFont(QFont("Arial", 16, QFont.Bold))
        self.ai_score_lbl.setStyleSheet("color: #ef5350;")
        self.status_lbl = QLabel("Your turn!")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #aed581; font-size: 13px;")
        score_layout.addWidget(self.player_score_lbl)
        score_layout.addStretch()
        score_layout.addWidget(self.status_lbl)
        score_layout.addStretch()
        score_layout.addWidget(self.ai_score_lbl)
        main_layout.addWidget(score_frame)

        # Grid + row labels
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(3)

        for r in range(G.size):
            for c in range(G.size):
                btn = QPushButton()
                btn.setFixedSize(52, 52)
                btn.clicked.connect(lambda _, rr=r, cc=c: self.cell_clicked(rr, cc))
                self.cells[r][c] = btn
                grid.addWidget(btn, r, c)

        # Row targets (right side)
        self.row_target_lbls = []
        for r in range(G.size):
            lbl = QLabel(str(G.row_targets[r]))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 13, QFont.Bold))
            lbl.setStyleSheet("color: #ffb74d; min-width: 28px;")
            self.row_target_lbls.append(lbl)
            grid.addWidget(lbl, r, G.size)

        # Col targets (bottom)
        self.col_target_lbls = []
        for c in range(G.size):
            lbl = QLabel(str(G.col_targets[c]))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 13, QFont.Bold))
            lbl.setStyleSheet("color: #ffb74d; min-width: 28px;")
            self.col_target_lbls.append(lbl)
            grid.addWidget(lbl, G.size, c)

        main_layout.addWidget(grid_container)

        # Restart button
        self.restart_btn = QPushButton("🔄 New Game")
        self.restart_btn.setFixedHeight(40)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)
        self.restart_btn.clicked.connect(self.restart)
        main_layout.addWidget(self.restart_btn)

        self.update_board()

    def update_board(self):
        for r in range(self.G.size):
            for c in range(self.G.size):
                btn = self.cells[r][c]
                cell = self.G.board[r][c]
                if cell == TREE:
                    btn.setText("🌳")
                    btn.setStyleSheet("background-color: #1b4620; border: 1px solid #2d6a31;")
                elif cell == TENT:
                    btn.setText("⛺")
                    btn.setStyleSheet("background-color: #3e2723; border: 1px solid #6d4c41;")
                else:
                    btn.setText("")
                    btn.setStyleSheet("background-color: #243447; border: 1px solid #2e4057;")
                    btn.setStyleSheet("""
                        QPushButton { background-color: #243447; border: 1px solid #2e4057; }
                        QPushButton:hover { background-color: #2e5077; }
                    """)

        # Update row target labels with color hints
        for r in range(self.G.size):
            need = self.G.row_need(r)
            lbl = self.row_target_lbls[r]
            lbl.setText(f"{self.G.row_targets[r]}")
            if need == 0:
                lbl.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 13px;")  # done
            elif need < 0:
                lbl.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 13px;")  # over
            else:
                lbl.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 13px;")

        for c in range(self.G.size):
            need = self.G.col_need(c)
            lbl = self.col_target_lbls[c]
            lbl.setText(f"{self.G.col_targets[c]}")
            if need == 0:
                lbl.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 13px;")
            elif need < 0:
                lbl.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 13px;")
            else:
                lbl.setStyleSheet("color: #ffb74d; font-weight: bold; font-size: 13px;")

        self.player_score_lbl.setText(f"🧑 Player: {self.G.player_score}")
        self.ai_score_lbl.setText(f"🤖 AI: {self.ai.score}")

    def cell_clicked(self, r, c):
        if self.game_over_shown: return
        if not self.player_turn: return

        # Check if this is a forced move (same rule as AI)
        graph = self.ai.build_bipartite_graph()
        forced = self.ai.find_forced_move(graph)
        if forced == (r, c):
            pts = 7  # player found the forced move, same bonus as AI
        else:
            pts = self.G.score_for_placement(r, c)
        if self.player.player_move(r, c):
            self.G.player_score += pts
            self.player_turn = False
            self.status_lbl.setText("AI is thinking...")
            self.update_board()
            if self.G.is_game_over():
                QTimer.singleShot(300, self.show_game_over)
            else:
                QTimer.singleShot(400, self.ai_turn)

    def ai_turn(self):
        if self.game_over_shown: return
        if self.ai.ai_move():
            pass  # score already updated inside ai_move
        self.player_turn = True
        self.status_lbl.setText("Your turn!")
        self.update_board()
        if self.G.is_game_over():
            QTimer.singleShot(300, self.show_game_over)

    def show_game_over(self):
        if self.game_over_shown: return
        self.game_over_shown = True

        ps = self.G.player_score
        ai_s = self.ai.score

        if ps > ai_s:
            winner = "🎉 You Win!"
            msg = f"Congratulations! You beat the AI!\n\nPlayer: {ps}  vs  AI: {ai_s}"
            color = "#4fc3f7"
        elif ai_s > ps:
            winner = "🤖 AI Wins!"
            msg = f"The AI defeated you this time!\n\nPlayer: {ps}  vs  AI: {ai_s}"
            color = "#ef5350"
        else:
            winner = "🤝 It's a Draw!"
            msg = f"Equal scores!\n\nPlayer: {ps}  vs  AI: {ai_s}"
            color = "#ffb74d"

        box = QMessageBox(self)
        box.setWindowTitle("Game Over")
        box.setText(f"<h2 style='color:{color};'>{winner}</h2>")
        box.setInformativeText(msg)
        box.setStandardButtons(QMessageBox.Ok)
        box.setStyleSheet("""
            QMessageBox { background-color: #1a2634; }
            QLabel { color: white; font-size: 14px; }
            QPushButton { background-color: #2e7d32; color: white; padding: 6px 20px;
                          border-radius: 4px; font-size: 13px; }
        """)
        box.exec_()

    def restart(self):
        self.G.generate_solvable_trees_and_targets()
        self.G.player_score = 0
        self.ai.score = 0
        self.game_over_shown = False
        self.player_turn = True
        self.status_lbl.setText("Your turn!")
        # Rebuild target labels
        for r in range(self.G.size):
            self.row_target_lbls[r].setText(str(self.G.row_targets[r]))
        for c in range(self.G.size):
            self.col_target_lbls[c].setText(str(self.G.col_targets[c]))
        self.update_board()
