import tkinter as tk
from functools import partial
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

from solver import CubeSolver, FACE_PIECES, STICKERS, STICKER_INDICES

COLORS = {
    "Yellow": "#FFD500",
    "Green": "#009B48",
    "Red": "#B71234",
    "Orange": "#FF5800",
    "Blue": "#0046AD",
    "White": "#FFFFFF",
    "Grey": "#888888",
}

FACE_COLORS = {
    "U": "Yellow",
    "R": "Orange",
    "F": "Green",
    "D": "White",
    "L": "Red",
    "B": "Blue",
}
COLOR_FACES = {color: face for face, color in FACE_COLORS.items()}

FACE_ORIGINS = {
    "U": (0, 3),
    "R": (3, 6),
    "F": (3, 3),
    "D": (6, 3),
    "L": (3, 0),
    "B": (3, 9),
}

CELL_SIZE = 40
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50

FIXED_CENTERS = {}
STICKER_COORDS = []
for face in FACE_PIECES:
    origin_row, origin_column = FACE_ORIGINS[face]
    FIXED_CENTERS[(origin_row + 1, origin_column + 1)] = FACE_COLORS[face]
    for row in range(3):
        for column in range(3):
            if row != 1 or column != 1:
                STICKER_COORDS.append((origin_row + row, origin_column + column))

# Group the visible stickers belonging to each corner or edge.
PIECE_SLOTS = {}
for index, (piece_faces, sticker_face) in enumerate(STICKERS):
    PIECE_SLOTS.setdefault(piece_faces, []).append(index)

class CubeGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rubik's Solver")
        self.selected_color = "Grey"
        self.grid_colors = {}
        self.rects = {}
        self._build_ui()
        self.solver = CubeSolver()

    def _build_ui(self):
        picker_frame = tk.Frame(self.root, pady=10)
        picker_frame.pack()

        for color_name, hex_value in COLORS.items():
            swatch = tk.Canvas(picker_frame, width=40, height=40, highlightthickness=0)
            swatch.pack(side=tk.LEFT, padx=5)
            swatch.create_oval(2, 2, 38, 38, fill=hex_value, outline="black")
            swatch.bind("<Button-1>", partial(self.select_color, color_name))

        self.canvas = tk.Canvas(self.root, width=600, height=450, bg="#f0f0f0")
        self.canvas.pack()
        self._draw_grid()

        controls = tk.Frame(self.root, pady=10)
        controls.pack()
        self.solve_button = tk.Button(
            controls, text="SOLVE", bg="#4CAF50", fg="white",
            font=("Helvetica", 12, "bold"), padx=20, pady=5, command=self.solve,
        )
        self.solve_button.pack(side=tk.LEFT, padx=20)
        self.reset_button = tk.Button(
            controls, text="RESET", bg="#f44336", fg="white",
            font=("Helvetica", 12, "bold"), padx=20, pady=5, command=self.reset_grid,
        )
        self.reset_button.pack(side=tk.LEFT, padx=20)

        self.output_text = ScrolledText(
            self.root, height=6, width=60, font=("Consolas", 12), wrap=tk.WORD,
        )
        self.output_text.pack(pady=20)

    def _draw_grid(self):
        for row, column in STICKER_COORDS + list(FIXED_CENTERS):
            left = GRID_OFFSET_X + column * CELL_SIZE
            top = GRID_OFFSET_Y + row * CELL_SIZE
            color = FIXED_CENTERS.get((row, column), "Grey")
            rectangle = self.canvas.create_rectangle(
                left, top, left + CELL_SIZE, top + CELL_SIZE,
                fill=COLORS[color], outline="black",
            )
            self.rects[(row, column)] = rectangle
            self.grid_colors[(row, column)] = color
            if (row, column) not in FIXED_CENTERS:
                self.canvas.tag_bind(
                    rectangle, "<Button-1>", partial(self.paint_cell, row, column),
                )

    def select_color(self, name, event):
        self.selected_color = name

    def paint_cell(self, row, column, event):
        self.grid_colors[(row, column)] = self.selected_color
        self.canvas.itemconfig(self.rects[(row, column)], fill=COLORS[self.selected_color])
        self.output_text.delete("1.0", tk.END)

    def reset_grid(self):
        for coordinates, rectangle in self.rects.items():
            color = FIXED_CENTERS.get(coordinates, "Grey")
            self.grid_colors[coordinates] = color
            self.canvas.itemconfig(rectangle, fill=COLORS[color])
        self.output_text.delete("1.0", tk.END)

    def _read_permutation(self):
        counts = dict.fromkeys(COLOR_FACES, 0)
        for coordinates in STICKER_COORDS + list(FIXED_CENTERS):
            color = self.grid_colors.get(coordinates)
            if color not in counts:
                raise ValueError("Please paint all stickers with one of the six face colors.")
            counts[color] += 1

        for color, count in counts.items():
            if count != 9:
                raise ValueError(f"Found {count} {color.lower()} stickers; there must be 9.")

        for coordinates, color in FIXED_CENTERS.items():
            if self.grid_colors[coordinates] != color:
                raise ValueError("The center colors must match the fixed cube orientation.")

        permutation = [-1] * len(STICKERS)
        seen_pieces = set()
        for position_faces, slots in PIECE_SLOTS.items():
            colors = []
            for slot in slots:
                colors.append(self.grid_colors[STICKER_COORDS[slot]])
            piece_faces = frozenset(COLOR_FACES[color] for color in colors)
            position_name = "".join(sorted(position_faces))

            if len(piece_faces) != len(slots) or piece_faces not in PIECE_SLOTS:
                raise ValueError(f"Invalid piece at {position_name}: {', '.join(colors)}.")
            if piece_faces in seen_pieces:
                raise ValueError(f"Duplicate piece with colors {', '.join(colors)}.")
            seen_pieces.add(piece_faces)

            # Identify each sticker by its piece and color, preserving orientation.
            for slot, color in zip(slots, colors):
                permutation[slot] = STICKER_INDICES[(piece_faces, COLOR_FACES[color])]

        return tuple(permutation)

    def _show_status(self, message):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, message)
        self.root.update_idletasks()

    def solve(self):
        self.output_text.delete("1.0", tk.END)
        try:
            permutation = self._read_permutation()
        except ValueError as error:
            messagebox.showerror("Invalid cube", str(error))
            return

        try:
            solution = self.solver.solve(permutation, on_status=self._show_status)
        except ValueError:
            self.output_text.delete("1.0", tk.END)
            messagebox.showerror(
                "Unsolvable cube",
                "This arrangement cannot be reached with legal face turns. Check the sticker colors.",
            )
            return
        except OSError as error:
            self.output_text.delete("1.0", tk.END)
            messagebox.showerror("Solver error", str(error))
            return

        self.output_text.delete("1.0", tk.END)
        if solution:
            self.output_text.insert(tk.END, " ".join(solution))
        else:
            self.output_text.insert(tk.END, "Already solved.")

    def run(self):
        self.root.mainloop()
        
