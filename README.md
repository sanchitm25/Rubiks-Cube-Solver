# Rubik's Cube Solver

A Python program for solving a 3x3 Rubik's cube using noncommutative Gaussian elimination (NCGE).

## Algorithm

The algorithm is implemented from Dror Bar-Natan's CUMC paper [Non-Commutative Gaussian Elimination and Rubik's Cube](https://www.math.utoronto.ca/drorbn/Talks/CUMC-0807/index.html).

Each face turn of the cube is a permutation of its 48 movable stickers (54 total stickers with 6 fixed centers). Combining these turns represents the cube as an algebraic permutation group. The solved cube is the identity permutation where every sticker is in its original position.

The algorithm builds a table of move sequences one sticker position at a time. At each step, it finds moves that can place a sticker correctly while leaving all previously fixed positions unchanged. Repeating this process gives the solver a systematic way to reduce any scrambled cube back to the solved state. The idea is similar to Gaussian elimination, where variables are handled one at a time without undoing earlier work, and is closely related to the Schreier-Sims algorithm for permutation groups.

Consecutive turns of the same face are simplified but the algorithm does not find shortest solutions and so the move sequences generated can grow very large in length.

## Running the program

Install **Python 3.9 or newer** with **Tkinter** available.

From the project directory run:

```bash
python main.py
```

## Entering your cube

Hold the cube with the **green center facing you** and the **yellow center facing up**. Select a colour at the top of the window, then click the grey squares to match the stickers on your cube, then click **SOLVE**.

The cube is displayed using the following net:

```text
          Yellow (U)
Red (L)   Green (F)   Orange (R)   Blue (B)
          White (D)
```

The center stickers are fixed and do not need to be entered. The app validates the entered cube before attempting to solve it.

## Reading the solution

Solutions use standard Rubik's cube notation. `U`, `D`, `L`, `R`, `F`, and `B` denote clockwise turns of the corresponding face, while an apostrophe denotes a counterclockwise turn (for example, `R'`).

Keep the cube oriented with **green facing you** and **yellow facing up** while following the solution.

## Table caching

The NCGE table is generated the first time the solver is used and cached in `ncge_cache.json`. Subsequent solves reuse the cached table. If the cache is missing or invalid, it is regenerated automatically.
