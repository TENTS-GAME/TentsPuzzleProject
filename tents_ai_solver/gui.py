from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QVBoxLayout, QLabel,
    QMessageBox, QHBoxLayout, QFrame, QListWidget, QListWidgetItem,
    QSlider, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from game_state import *


# ── colour palette ──────────────────────────────────────────────────────────
BG          = "#1a2634"
PANEL_BG    = "#0f1923"
CELL_EMPTY  = "#243447"
CELL_TREE   = "#1b4620"
CELL_TENT   = "#3e2723"
CELL_CURSOR = "#7b3f00"       # amber flash for the cell just placed
BORDER_TREE = "#2d6a31"
BORDER_TENT = "#6d4c41"
BORDER_DEF  = "#2e4057"
COL_GREEN   = "#66bb6a"
COL_RED     = "#ef5350"
COL_ORANGE  = "#ffb74d"
COL_CYAN    = "#4dd0e1"
COL_PURPLE  = "#ce93d8"


class GameGUI(QWidget):

    def __init__(self, G, ai):
        super().__init__()
        self.G  = G
        self.ai = ai
        self.game_over_shown = False
        self.started         = False      # whether Start has been pressed
        self._cursor_cell    = None       # cell to flash amber this tick
        self._cursor_timer   = QTimer()
        self._cursor_timer.setSingleShot(True)
        self._cursor_timer.timeout.connect(self._clear_cursor)

        self.setWindowTitle("Tents – AI Solver")
        self.setMinimumSize(820, 560)
        self.setStyleSheet(f"QWidget {{ background-color: {BG}; }}"
                           f"QLabel  {{ color: #cdd6e0; font-size: 13px; }}")

        # ── root layout ─────────────────────────────────────────────────────
        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(12, 12, 12, 12)

        # ── LEFT: grid + controls ────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)

        # score/status bar
        bar = QFrame()
        bar.setStyleSheet(f"background:{PANEL_BG}; border-radius:8px; padding:4px;")
        bar_h = QHBoxLayout(bar)

        self.status_lbl = QLabel("Press  ▶ Start  to begin solving")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color:{COL_GREEN}; font-size:13px; font-weight:bold;")
        self.status_lbl.setWordWrap(True)

        self.score_lbl = QLabel("🤖  Score: 0")
        self.score_lbl.setFont(QFont("Arial", 14, QFont.Bold))
        self.score_lbl.setStyleSheet(f"color:{COL_RED};")

        bar_h.addWidget(self.status_lbl, 3)
        bar_h.addWidget(self.score_lbl, 1)
        left.addWidget(bar)

        # grid
        grid_w = QWidget()
        self.grid = QGridLayout(grid_w)
        self.grid.setSpacing(3)
        self.cells = [[None] * G.size for _ in range(G.size)]

        for r in range(G.size):
            for c in range(G.size):
                btn = QPushButton()
                btn.setFixedSize(52, 52)
                btn.setEnabled(False)
                btn.setFont(QFont("Segoe UI Emoji", 18))
                self.cells[r][c] = btn
                self.grid.addWidget(btn, r, c)

        # row hints (right of grid)
        self.row_lbls = []
        for r in range(G.size):
            lbl = QLabel(str(G.row_targets[r]))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 13, QFont.Bold))
            lbl.setStyleSheet(f"color:{COL_ORANGE}; min-width:26px;")
            self.row_lbls.append(lbl)
            self.grid.addWidget(lbl, r, G.size)

        # col hints (below grid)
        self.col_lbls = []
        for c in range(G.size):
            lbl = QLabel(str(G.col_targets[c]))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 13, QFont.Bold))
            lbl.setStyleSheet(f"color:{COL_ORANGE}; min-width:26px;")
            self.col_lbls.append(lbl)
            self.grid.addWidget(lbl, G.size, c)

        left.addWidget(grid_w)

        # ── speed slider ─────────────────────────────────────────────────────
        sp_row = QHBoxLayout()
        sp_lbl = QLabel("Speed:")
        sp_lbl.setStyleSheet(f"color:{COL_CYAN}; font-size:12px;")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.setFixedWidth(120)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal { height:6px; background:#2e4057; border-radius:3px; }
            QSlider::handle:horizontal { width:14px; height:14px; margin:-4px 0;
                                         background:#4dd0e1; border-radius:7px; }
            QSlider::sub-page:horizontal { background:#4dd0e1; border-radius:3px; }
        """)
        self.speed_slider.valueChanged.connect(self._on_speed_change)
        self.speed_val_lbl = QLabel("5")
        self.speed_val_lbl.setStyleSheet(f"color:{COL_CYAN}; font-size:12px;")
        sp_row.addWidget(sp_lbl)
        sp_row.addWidget(self.speed_slider)
        sp_row.addWidget(self.speed_val_lbl)
        sp_row.addStretch()
        left.addLayout(sp_row)

        # ── buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton { background:#1565c0; color:white;
                          border-radius:6px; border:none; }
            QPushButton:hover { background:#1976d2; }
            QPushButton:disabled { background:#37474f; color:#78909c; }
        """)
        self.start_btn.clicked.connect(self.start_solving)

        self.restart_btn = QPushButton("🔄  New Puzzle")
        self.restart_btn.setFixedHeight(40)
        self.restart_btn.setFont(QFont("Arial", 13, QFont.Bold))
        self.restart_btn.setStyleSheet("""
            QPushButton { background:#2e7d32; color:white;
                          border-radius:6px; border:none; }
            QPushButton:hover { background:#388e3c; }
        """)
        self.restart_btn.clicked.connect(self.restart)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.restart_btn)
        left.addLayout(btn_row)

        root.addLayout(left, 3)

        # ── RIGHT: step log ──────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(6)

        log_title = QLabel("🧩  AI Solving Steps")
        log_title.setFont(QFont("Arial", 13, QFont.Bold))
        log_title.setStyleSheet(f"color:{COL_CYAN};")
        right.addWidget(log_title)

        self.step_list = QListWidget()
        self.step_list.setStyleSheet(f"""
            QListWidget {{
                background:{PANEL_BG}; border:1px solid #2e4057;
                border-radius:6px; color:#cdd6e0; font-size:12px;
            }}
            QListWidget::item {{ padding:4px 6px; border-bottom:1px solid #1e2e3e; }}
            QListWidget::item:selected {{ background:#1e3a5f; }}
        """)
        self.step_list.setWordWrap(True)
        self.step_list.setSpacing(1)
        right.addWidget(self.step_list, 1)

        # legend
        legend_frame = QFrame()
        legend_frame.setStyleSheet(f"background:{PANEL_BG}; border-radius:6px; padding:6px;")
        legend_layout = QVBoxLayout(legend_frame)
        legend_layout.setSpacing(2)
        legend_title = QLabel("Legend")
        legend_title.setFont(QFont("Arial", 11, QFont.Bold))
        legend_title.setStyleSheet(f"color:{COL_ORANGE};")
        legend_layout.addWidget(legend_title)
        for icon, text, color in [
            ("⚡", "Forced move (1 option only)",   COL_GREEN),
            ("🎯", "MCV + LCV branch choice",        COL_CYAN),
            ("✂️", "Forward-check prune",            COL_ORANGE),
            ("⬅️", "Backtrack",                      COL_RED),
            ("🔍", "Solver summary",                 COL_PURPLE),
            ("⚠️", "Greedy fallback",                COL_ORANGE),
        ]:
            row = QHBoxLayout()
            il = QLabel(icon); il.setFixedWidth(22)
            tl = QLabel(text); tl.setStyleSheet(f"color:{color}; font-size:11px;")
            row.addWidget(il); row.addWidget(tl); row.addStretch()
            legend_layout.addLayout(row)
        right.addWidget(legend_frame)

        root.addLayout(right, 2)

        # ── AI timer ─────────────────────────────────────────────────────────
        self.timer = QTimer()
        self.timer.timeout.connect(self.ai_turn)
        # Do NOT start yet — wait for Start button

        self.update_board()

    # ════════════════════════════════════════════════════════════════════════
    # Board rendering
    # ════════════════════════════════════════════════════════════════════════

    def update_board(self):
        for r in range(self.G.size):
            for c in range(self.G.size):
                btn  = self.cells[r][c]
                cell = self.G.board[r][c]
                is_cursor = (self._cursor_cell == (r, c))

                if cell == TREE:
                    btn.setText("🌳")
                    btn.setStyleSheet(
                        f"background:{CELL_TREE}; border:1px solid {BORDER_TREE};"
                        "border-radius:4px;")
                elif cell == TENT:
                    bg = CELL_CURSOR if is_cursor else CELL_TENT
                    btn.setText("⛺")
                    btn.setStyleSheet(
                        f"background:{bg}; border:2px solid "
                        f"{'#ff8f00' if is_cursor else BORDER_TENT};"
                        "border-radius:4px;")
                else:
                    btn.setText("")
                    btn.setStyleSheet(
                        f"background:{CELL_EMPTY}; border:1px solid {BORDER_DEF};"
                        "border-radius:4px;")

        # row hints
        for r in range(self.G.size):
            need = self.G.row_need(r)
            lbl  = self.row_lbls[r]
            lbl.setText(str(self.G.row_targets[r]))
            if need == 0:   lbl.setStyleSheet(f"color:{COL_GREEN};  font-weight:bold; font-size:13px;")
            elif need < 0:  lbl.setStyleSheet(f"color:{COL_RED};    font-weight:bold; font-size:13px;")
            else:           lbl.setStyleSheet(f"color:{COL_ORANGE}; font-weight:bold; font-size:13px;")

        # col hints
        for c in range(self.G.size):
            need = self.G.col_need(c)
            lbl  = self.col_lbls[c]
            lbl.setText(str(self.G.col_targets[c]))
            if need == 0:   lbl.setStyleSheet(f"color:{COL_GREEN};  font-weight:bold; font-size:13px;")
            elif need < 0:  lbl.setStyleSheet(f"color:{COL_RED};    font-weight:bold; font-size:13px;")
            else:           lbl.setStyleSheet(f"color:{COL_ORANGE}; font-weight:bold; font-size:13px;")

        self.score_lbl.setText(f"🤖  Score: {self.ai.score}")

    def _clear_cursor(self):
        self._cursor_cell = None
        self.update_board()

    # ════════════════════════════════════════════════════════════════════════
    # Step log
    # ════════════════════════════════════════════════════════════════════════

    def _log(self, text):
        """Append one line to the step log and auto-scroll."""
        if not text:
            return
        item = QListWidgetItem(f"  {text}")

        # colour-code by icon prefix
        if text.startswith("⚡"):
            item.setForeground(QColor(COL_GREEN))
        elif text.startswith("🎯"):
            item.setForeground(QColor(COL_CYAN))
        elif text.startswith("✂️") or text.startswith("✂"):
            item.setForeground(QColor(COL_ORANGE))
        elif text.startswith("⬅️") or text.startswith("⬅"):
            item.setForeground(QColor(COL_RED))
        elif text.startswith("🔍"):
            item.setForeground(QColor(COL_PURPLE))
        elif text.startswith("⚠️") or text.startswith("⚠"):
            item.setForeground(QColor(COL_ORANGE))
        elif text.startswith("✅"):
            item.setForeground(QColor(COL_GREEN))
        else:
            item.setForeground(QColor("#cdd6e0"))

        self.step_list.addItem(item)
        self.step_list.scrollToBottom()

    # ════════════════════════════════════════════════════════════════════════
    # Controls
    # ════════════════════════════════════════════════════════════════════════

    def _on_speed_change(self, val):
        self.speed_val_lbl.setText(str(val))
        # val 1 → 1000 ms, val 10 → 100 ms
        interval = int(1100 - val * 100)
        if self.timer.isActive():
            self.timer.setInterval(interval)

    def _interval(self):
        val = self.speed_slider.value()
        return int(1100 - val * 100)

    def start_solving(self):
        if self.started:
            return
        self.started = True
        self.start_btn.setEnabled(False)
        self.status_lbl.setText("🧠  AI is solving…")
        self._log("▶ Solving started.")
        self.timer.start(self._interval())

    # ════════════════════════════════════════════════════════════════════════
    # AI turn
    # ════════════════════════════════════════════════════════════════════════

    def ai_turn(self):
        if self.game_over_shown:
            return

        placed, desc = self.ai.ai_move()
        self._log(desc)

        if placed:
            # Highlight the newly placed cell briefly
            self._cursor_cell = self.ai.last_cell
            self.update_board()
            self._cursor_timer.start(350)          # clear amber after 350 ms

            # Update status with short summary
            if self.ai.last_cell:
                r, c = self.ai.last_cell
                remaining = sum(
                    1 for rr in range(self.G.size) for cc in range(self.G.size)
                    if self.G.board[rr][cc] == TREE and (rr, cc) not in self.G.tree_used
                )
                self.status_lbl.setText(
                    f"⛺ Placed tent at row {r}, col {c} — "
                    f"{remaining} tree(s) remaining"
                )
        else:
            # log-only or skip tick — still refresh board for hint colours
            self.update_board()
            if desc and not desc.startswith("✅"):
                self.status_lbl.setText(desc[:80])

        if self.G.is_game_over():
            self.show_game_over()

    # ════════════════════════════════════════════════════════════════════════
    # Game over
    # ════════════════════════════════════════════════════════════════════════

    def show_game_over(self):
        if self.game_over_shown:
            return
        self.game_over_shown = True
        self.timer.stop()
        total_steps = self.step_list.count()
        self.status_lbl.setText(f"✅  Puzzle solved!  Score: {self.ai.score}")
        self._log(f"✅ Puzzle complete! Final score: {self.ai.score}  |  Steps logged: {total_steps}")
        box = QMessageBox(self)
        box.setWindowTitle("Puzzle Solved")
        box.setText("<h2 style='color:#66bb6a;'>✅ AI Completed the Puzzle!</h2>")
        box.setInformativeText(
            f"Score: {self.ai.score}\n"
            f"Steps logged: {total_steps}\n\n"
            "See the step log on the right for the full solution trace."
        )
        box.exec_()

    # ════════════════════════════════════════════════════════════════════════
    # Restart
    # ════════════════════════════════════════════════════════════════════════

    def restart(self):
        self.timer.stop()
        self._cursor_timer.stop()
        self._cursor_cell = None

        self.G.generate_solvable_trees_and_targets()
        self.ai.reset()

        self.started          = False
        self.game_over_shown  = False

        self.step_list.clear()
        self.status_lbl.setText("Press  ▶ Start  to begin solving")
        self.start_btn.setEnabled(True)

        for r in range(self.G.size):
            self.row_lbls[r].setText(str(self.G.row_targets[r]))
        for c in range(self.G.size):
            self.col_lbls[c].setText(str(self.G.col_targets[c]))

        self.update_board()
