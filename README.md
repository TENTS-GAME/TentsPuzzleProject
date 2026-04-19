# TentsPuzzleProject
Tents Puzzle: Logic Meets Algorithms
# 🌳 Tents — Player vs AI (Greedy Algorithm)

A competitive **Player vs AI** implementation of the classic **Tents logic puzzle**, built with **Python** and **PyQt5**. This project also includes an in-depth analysis of the AI's greedy algorithm — comparing an old baseline approach to a new, smarter version.

---

## 📖 What is the Tents Game?

Tents is a classic logic puzzle played on an **8×8 grid** seeded with **10 trees**. Players take turns placing tents on the board, competing for the highest score.

### Rules

- Each tent must be **adjacent** (up/down/left/right only — no diagonals) to a tree.
- Tents **cannot touch each other**, not even diagonally — all 8 surrounding cells must be free.
- Each row and column has a **target count** — the total tents in that row/column must match exactly.
- Each tree must have **exactly one** adjacent tent.

### Scoring

| Condition | Points |
|---|---|
| Base placement (any valid tent) | +1 |
| Row need = 1 (fills the row exactly) | +3 bonus |
| Row need > 1 (partial row contribution) | +2 bonus |
| Column need = 1 (fills the column exactly) | +3 bonus |
| Column need > 1 (partial column contribution) | +2 bonus |
| Forced move (only valid option at that moment) | +7 flat |

**Maximum score per move:** 1 (base) + 3 (row exact) + 3 (col exact) = **7 points**

---

## 🤖 AI Algorithm Overview

The AI uses a **greedy algorithm** to decide where to place each tent. Two versions are documented and compared in this project.

### Old Algorithm

The old AI followed a simple 4-step process:

1. **Build Bipartite Graph** — Scan board for unmatched trees and collect valid tent candidate cells.
2. **Merge Sort Trees** — Sort trees by fewest candidate cells first, then by highest row+col need.
3. **Insertion Sort Candidates** — For each tree, sort candidate cells by row+col need score.
4. **Place First Valid** — Iterate sorted trees and candidates; place the first valid tent found.

**Limitations:**
- No forced-move detection — missed logically mandatory placements.
- No lookahead scoring — could block entire tree clusters.
- AI score was always hardcoded to `1`, making fair competition impossible.

---

### New Algorithm

The new AI adds intelligence in three phases:

**Phase 1 — Forced Move Detection (`find_forced_move()`)**

Checks for three mandatory placement rules before any heuristic search:
- A tree with **exactly 1 valid tent cell** → force it.
- A row that needs N tents and has **exactly N valid cells** → force first.
- A column that needs N tents and has **exactly N valid cells** → force first.

Forced moves award a **+7 bonus** — the highest possible — incentivising both the AI and player to spot them early.

**Phase 2 — Constrained-First Sort**

Merge sorts trees by fewest options. Filters out dead trees (no valid candidates) before sorting, cleaning up the search space. Candidate cells are then insertion-sorted by lookahead score.

**Phase 3 — Lookahead Scoring (`lookahead_score()`)**

```
score = base_score - 0.3 × future_blocked_neighbors
```

For each candidate cell `(r, c)`, the score is the base placement reward minus a penalty for each empty cell adjacent to a tree that this tent would block. This prefers moves that **keep the board open** for future placements.

---

## 🔄 Key Changes at a Glance

| Feature | Old | New | Impact |
|---|---|---|---|
| Forced Move Detection | ❌ None | ✅ `find_forced_move()` | Avoids suboptimal greedy choices |
| Lookahead Scoring | ❌ None | ✅ `lookahead_score()` | Penalises future-blocking moves |
| Empty-candidate filtering | ❌ Dead trees included | ✅ Filtered before sort | Cleaner search space |
| Score Tracking | ❌ AI score = 1 always | ✅ Points awarded each move | Fair competitive scoring |
| `is_game_over()` | ❌ Missing | ✅ Added | Proper game termination |
| `score_for_placement()` | ❌ Missing | ✅ Added | Reward shaping |

---

## ⏱️ Time Complexity Analysis

| Component | Old | New | Note |
|---|---|---|---|
| `build_bipartite_graph` | O(N²·4) | O(N²·4) | N=8, trivial |
| `merge_sort` (trees) | O(T log T) | O(T log T) | T = trees ≤ 10 |
| `insertion_sort` (candidates) | O(C²) | O(C²) | C = candidates ≤ 4 |
| `lookahead_score` | — | O(9) = O(1) | Fixed 3×3 scan |
| `find_forced_move` | — | O(T + N²) | Checks trees & lines |
| `evaluate_lines_priority` | O(N·log N) | O(N·log N) | Bucket + sort, same |
| **`ai_move()` total** | **O(T·C + N²)** | **O(T·C·9 + N²)** | Constant factor only |

Both versions are **O(N²) overall**. The new algorithm adds no asymptotic cost — the constant factor increase from lookahead (×9 per candidate) is negligible on an 8×8 board.

---

## ✅ Why the New Algorithm is Better

1. **Correctness Over Greed** — Forced-move detection ensures the AI never makes a logically wrong strategy choice.
2. **Future-Aware Placement** — Lookahead penalty prevents the AI from blocking entire tree clusters with a single tent.
3. **Competitive Scoring** — The old AI score was always `1`. The new AI accumulates real points for a proper win/draw/loss outcome.
4. **Stable Board Generation** — Backtracking in `_assign_tents()` guarantees non-overlapping, solvable boards every game.

---

## ⚠️ Drawbacks

### Old Algorithm
- No forced move detection → misses mandatory placements.
- No score tracking → AI score is always `1`.
- No lookahead → may abandon some trees entirely.

### New Algorithm
- **No global optimality guarantee** — the algorithm is still greedy and does not guarantee the maximum total score.
- **Single-step lookahead only** — only checks immediate 3×3 impact, not multi-step consequences.
- **Global constraints not fully modelled** — row and column targets create long-range dependencies that the heuristic approximates but does not model exactly (e.g., future competition for row slots, global quota balancing).
- **No undo/rollback** — a wrong placement is irreversible and permanently damages board state.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| GUI Framework | PyQt5 |
| AI Strategy | Greedy Algorithm (with lookahead) |
| Board Size | 8×8 |
| Trees | 10 per game |

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install PyQt5
```

### Run the Game

```bash
python main.py
```

---

## 📊 Summary

The new greedy AI improves on the old baseline across every dimension:

- 🔍 Forced moves detected — mandatory placements never missed
- 🔭 Lookahead scoring — blocks future-blocking moves proactively
- 📊 Real score tracking — proper competitive game now possible
- 🛡️ Bug-free priority sort — no crashes on full rows/columns
- ✅ Solvable board guarantee — backtracking placement generation
- ⚡ Same asymptotic complexity — O(N²), no performance cost
