import tkinter as tk
from queue import Queue, PriorityQueue
import random
import time

ROWS = 20
SIZE = 30
CANVAS_SIZE = ROWS * SIZE

# Colors
WHITE = "white"
BLACK = "#111111"
GREEN = "#2ecc71"
RED = "#ff5c5c"
BLUE = "#4da3ff"
YELLOW = "#ffd166"
PURPLE = "#c77dff"
ORANGE = "#ff9f1c"
TEAL = "#00c2a8"
BG = "#121826"
PANEL = "#1b2333"
CARD = "#263247"
TEXT = "#f3f4f6"
MUTED = "#b8c1cc"

speed = 0.02
steps = 0
start_time = 0
mouse_down = False

ALGORITHM_INFO = {
    "BFS": "Breadth-First Search explores level by level and guarantees the shortest path on this grid.",
    "DFS": "Depth-First Search dives deeply into one branch first. It is fast to visualize but may not find the shortest path.",
    "A*": "A* combines path cost and heuristic distance, usually finding efficient shortest paths quickly.",
    "Hill Climbing": "Hill Climbing always moves to the neighbor that looks closest to the goal. It can get stuck in local optima.",
    "Minimax": "This minimax-style heuristic picks the move with the best worst-case next step. It is a simplified demo, not full game-tree minimax.",
}


class Node:
    def __init__(self, row, col, canvas):
        self.row = row
        self.col = col
        self.canvas = canvas
        self.color = WHITE
        self.rect = canvas.create_rectangle(
            col * SIZE,
            row * SIZE,
            col * SIZE + SIZE,
            row * SIZE + SIZE,
            fill=WHITE,
            outline="#d9dce2",
        )
        self.neighbors = []

    def set_color(self, color):
        self.color = color
        self.canvas.itemconfig(self.rect, fill=color)

    def is_barrier(self):
        return self.color == BLACK


def heuristic(a, b):
    return abs(a.row - b.row) + abs(a.col - b.col)


def set_status(message):
    status_var.set(message)


def update_neighbors(grid_data):
    for row in grid_data:
        for node in row:
            node.neighbors = []
            r, c = node.row, node.col
            if r > 0 and not grid_data[r - 1][c].is_barrier():
                node.neighbors.append(grid_data[r - 1][c])
            if r < ROWS - 1 and not grid_data[r + 1][c].is_barrier():
                node.neighbors.append(grid_data[r + 1][c])
            if c > 0 and not grid_data[r][c - 1].is_barrier():
                node.neighbors.append(grid_data[r][c - 1])
            if c < ROWS - 1 and not grid_data[r][c + 1].is_barrier():
                node.neighbors.append(grid_data[r][c + 1])


def refresh_stats():
    step_label.config(text=f"Steps: {steps}")


def visualize():
    global steps
    steps += 1
    refresh_stats()
    root.update_idletasks()
    root.update()
    time.sleep(speed)


def show_result(name, found=True, extra=""):
    end_time = time.time()
    elapsed = round(end_time - start_time, 4)
    if found:
        summary = f"{name}: {elapsed}s | {steps} steps"
        if extra:
            summary = f"{summary} | {extra}"
        result_label.config(text=summary)
        set_status(f"{name} completed successfully.")
    else:
        message = f"{name}: no path found"
        if extra:
            message = f"{message} | {extra}"
        result_label.config(text=message)
        set_status(f"{name} could not reach the target.")


def clear_search_colors():
    for row in grid:
        for node in row:
            if node.color not in (GREEN, RED, BLACK):
                node.set_color(WHITE)


def reconstruct_path(parent, path_color):
    cur = end
    if cur != start and cur not in parent:
        return False

    while cur in parent:
        cur = parent[cur]
        if cur != start:
            cur.set_color(path_color)
            visualize()
    return True


def prepare_run(name):
    global steps, start_time
    if not start or not end:
        set_status("Place both a start node and an end node before running an algorithm.")
        result_label.config(text="Missing start/end")
        return False

    clear_search_colors()
    update_neighbors(grid)
    steps = 0
    start_time = time.time()
    refresh_stats()
    result_label.config(text="")
    set_status(f"Running {name}...")
    return True


def mark_visited(node, color=YELLOW):
    if node not in (start, end) and node.color != color:
        node.set_color(color)


def bfs():
    if not prepare_run("BFS"):
        return

    q = Queue()
    q.put(start)
    visited = {start}
    parent = {}
    found = False

    while not q.empty():
        current = q.get()
        if current == end:
            found = True
            break

        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                q.put(neighbor)
                mark_visited(neighbor)
                visualize()

    if not found:
        show_result("BFS", found=False)
        return

    reconstruct_path(parent, BLUE)
    show_result("BFS")


def dfs():
    if not prepare_run("DFS"):
        return

    stack = [start]
    visited = {start}
    parent = {}
    found = False

    while stack:
        current = stack.pop()
        if current == end:
            found = True
            break

        for neighbor in reversed(current.neighbors):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
                mark_visited(neighbor, ORANGE)
                visualize()

    if not found:
        show_result("DFS", found=False)
        return

    reconstruct_path(parent, PURPLE)
    show_result("DFS")


def astar():
    if not prepare_run("A*"):
        return

    count = 0
    pq = PriorityQueue()
    pq.put((0, count, start))
    parent = {}
    g_score = {n: float("inf") for row in grid for n in row}
    g_score[start] = 0
    found = False

    while not pq.empty():
        _, _, current = pq.get()
        if current == end:
            found = True
            break

        for neighbor in current.neighbors:
            temp_score = g_score[current] + 1
            if temp_score < g_score[neighbor]:
                parent[neighbor] = current
                g_score[neighbor] = temp_score
                f_score = temp_score + heuristic(neighbor, end)
                count += 1
                pq.put((f_score, count, neighbor))
                mark_visited(neighbor)
                visualize()

    if not found:
        show_result("A*", found=False)
        return

    reconstruct_path(parent, BLUE)
    show_result("A*")


def hill_climbing():
    if not prepare_run("Hill Climbing"):
        return

    current = start
    visited = {start}
    parent = {}
    found = False

    while True:
        if current == end:
            found = True
            break

        choices = [n for n in current.neighbors if n not in visited]
        if not choices:
            break

        next_node = min(choices, key=lambda node: (heuristic(node, end), node.row, node.col))
        parent[next_node] = current
        visited.add(next_node)
        current = next_node
        mark_visited(current, TEAL)
        visualize()

    if not found:
        show_result("Hill Climbing", found=False, extra="stuck at a local optimum")
        return

    reconstruct_path(parent, BLUE)
    show_result("Hill Climbing")


def minimax_search():
    if not prepare_run("Minimax"):
        return

    current = start
    visited = {start}
    parent = {}
    found = False

    while True:
        if current == end:
            found = True
            break

        choices = [n for n in current.neighbors if n not in visited]
        if not choices:
            break

        def minimax_score(node):
            onward = [next_node for next_node in node.neighbors if next_node not in visited or next_node == end]
            if not onward:
                return heuristic(node, end) + ROWS
            worst_reply = max(heuristic(next_node, end) for next_node in onward)
            return worst_reply

        next_node = min(
            choices,
            key=lambda node: (minimax_score(node), heuristic(node, end), node.row, node.col),
        )
        parent[next_node] = current
        visited.add(next_node)
        current = next_node
        mark_visited(current, YELLOW)
        visualize()

    if not found:
        show_result("Minimax", found=False, extra="heuristic branch ended")
        return

    reconstruct_path(parent, PURPLE)
    show_result("Minimax")


def generate_maze():
    reset()
    set_status("Generating maze...")
    for row in grid:
        for node in row:
            node.set_color(BLACK)

    def carve(r, c):
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < ROWS and grid[nr][nc].color == BLACK:
                grid[nr][nc].set_color(WHITE)
                grid[r + dr // 2][c + dc // 2].set_color(WHITE)
                root.update_idletasks()
                root.update()
                time.sleep(speed)
                carve(nr, nc)

    grid[0][0].set_color(WHITE)
    carve(0, 0)
    set_status("Maze generated. Place start and end nodes to test an algorithm.")


def compare_all():
    if not start or not end:
        set_status("Place both start and end nodes before comparing algorithms.")
        result_label.config(text="Missing start/end")
        return

    results = {}
    original_speed = speed_slider.get()
    speed_slider.set(0.001)
    change_speed(speed_slider.get())

    algorithms = [
        ("BFS", bfs),
        ("DFS", dfs),
        ("A*", astar),
        ("Hill Climbing", hill_climbing),
        ("Minimax", minimax_search),
    ]

    for name, func in algorithms:
        clear_search_colors()
        func()
        results[name] = result_label.cget("text")

    speed_slider.set(original_speed)
    change_speed(speed_slider.get())
    set_status("Comparison finished.")
    result_label.config(text=" | ".join(results.values()))


def get_node_from_event(event):
    row = event.y // SIZE
    col = event.x // SIZE
    if 0 <= row < ROWS and 0 <= col < ROWS:
        return grid[row][col]
    return None


def apply_draw_mode(node):
    global start, end
    if node is None:
        return

    if draw_mode.get() == "start":
        if start and start != end:
            start.set_color(WHITE)
        if node == end:
            end = None
        start = node
        start.set_color(GREEN)
        set_status("Start node placed.")
    elif draw_mode.get() == "end":
        if end and end != start:
            end.set_color(WHITE)
        if node == start:
            start = None
        end = node
        end.set_color(RED)
        set_status("Target node placed.")
    elif draw_mode.get() == "wall":
        if node not in (start, end):
            node.set_color(BLACK)
            set_status("Drawing walls. Drag mouse to draw more.")
    elif draw_mode.get() == "erase":
        erase_node(node)


def erase_node(node):
    global start, end
    if node == start:
        start = None
    if node == end:
        end = None
    node.set_color(WHITE)
    set_status("Cell erased.")


def click(event):
    global mouse_down
    mouse_down = True
    node = get_node_from_event(event)
    apply_draw_mode(node)


def drag(event):
    if not mouse_down:
        return
    node = get_node_from_event(event)
    if draw_mode.get() in ("wall", "erase"):
        apply_draw_mode(node)


def release(_event):
    global mouse_down
    mouse_down = False


def right_click(event):
    node = get_node_from_event(event)
    if node:
        erase_node(node)


def on_hover(event):
    node = get_node_from_event(event)
    if node:
        position_var.set(f"Pointer: row {node.row}, col {node.col}")


def change_speed(val):
    global speed
    speed = float(val)
    speed_value_label.config(text=f"{speed:.3f}s")


def reset():
    global grid, start, end, steps
    canvas.delete("all")
    grid = [[Node(i, j, canvas) for j in range(ROWS)] for i in range(ROWS)]
    start = None
    end = None
    steps = 0
    refresh_stats()
    result_label.config(text="Ready to run")
    set_status("Canvas cleared. Choose a draw mode and build a pathfinding scene.")


def run_selected():
    algorithm = algo_var.get()
    if algorithm == "BFS":
        bfs()
    elif algorithm == "DFS":
        dfs()
    elif algorithm == "A*":
        astar()
    elif algorithm == "Hill Climbing":
        hill_climbing()
    elif algorithm == "Minimax":
        minimax_search()


def update_algorithm_hint(*_args):
    hint_var.set(ALGORITHM_INFO[algo_var.get()])


def set_draw_mode(mode):
    draw_mode.set(mode)
    names = {
        "start": "Click a cell to place the start node.",
        "end": "Click a cell to place the target node.",
        "wall": "Click or drag on the grid to draw walls.",
        "erase": "Click or drag on the grid to erase cells.",
    }
    set_status(names[mode])


def legend(parent, color, text):
    frame = tk.Frame(parent, bg=PANEL)
    frame.pack(anchor="w", pady=2)
    tk.Label(frame, bg=color, width=2, height=1).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(frame, text=text, fg=TEXT, bg=PANEL, font=("Segoe UI", 10)).pack(side=tk.LEFT)


root = tk.Tk()
root.title("Interactive Pathfinding Visualizer")
root.geometry("1080x760")
root.configure(bg=BG)
root.resizable(False, False)

status_var = tk.StringVar(value="Choose a draw mode and build a pathfinding scene.")
hint_var = tk.StringVar(value=ALGORITHM_INFO["BFS"])
position_var = tk.StringVar(value="Pointer: row -, col -")
algo_var = tk.StringVar(value="BFS")
draw_mode = tk.StringVar(value="wall")

top_frame = tk.Frame(root, bg=PANEL, padx=20, pady=14)
top_frame.pack(fill="x")

tk.Label(
    top_frame,
    text="Pathfinding Visualizer Studio",
    fg=TEXT,
    bg=PANEL,
    font=("Segoe UI", 18, "bold"),
).pack(anchor="w")

tk.Label(
    top_frame,
    text="Interactive grid editing, live stats, maze generation, and multiple search strategies.",
    fg=MUTED,
    bg=PANEL,
    font=("Segoe UI", 10),
).pack(anchor="w", pady=(4, 0))

main_frame = tk.Frame(root, bg=BG, padx=18, pady=16)
main_frame.pack(fill="both", expand=True)

canvas_card = tk.Frame(main_frame, bg=PANEL, padx=14, pady=14)
canvas_card.grid(row=0, column=0, sticky="n")

canvas = tk.Canvas(
    canvas_card,
    width=CANVAS_SIZE,
    height=CANVAS_SIZE,
    bg="white",
    highlightthickness=0,
)
canvas.pack()

footer_bar = tk.Frame(canvas_card, bg=PANEL)
footer_bar.pack(fill="x", pady=(10, 0))

tk.Label(
    footer_bar,
    textvariable=status_var,
    fg=TEXT,
    bg=PANEL,
    font=("Segoe UI", 10),
    wraplength=500,
    justify="left",
).pack(anchor="w")

tk.Label(
    footer_bar,
    textvariable=position_var,
    fg=MUTED,
    bg=PANEL,
    font=("Segoe UI", 9),
).pack(anchor="w", pady=(6, 0))

side_panel = tk.Frame(main_frame, bg=BG)
side_panel.grid(row=0, column=1, sticky="ns", padx=(18, 0))

controls_card = tk.Frame(side_panel, bg=PANEL, padx=16, pady=16)
controls_card.pack(fill="x")

tk.Label(controls_card, text="Algorithm", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w")
algo_menu = tk.OptionMenu(controls_card, algo_var, *ALGORITHM_INFO.keys())
algo_menu.config(bg=CARD, fg=TEXT, activebackground=CARD, activeforeground=TEXT, width=18, highlightthickness=0)
algo_menu["menu"].config(bg=CARD, fg=TEXT)
algo_menu.pack(fill="x", pady=(8, 8))
algo_var.trace_add("write", update_algorithm_hint)

tk.Label(
    controls_card,
    textvariable=hint_var,
    fg=MUTED,
    bg=PANEL,
    wraplength=280,
    justify="left",
    font=("Segoe UI", 9),
).pack(anchor="w", pady=(0, 12))

tk.Label(controls_card, text="Edit Grid", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w")

for mode, label in (
    ("start", "Place Start"),
    ("end", "Place End"),
    ("wall", "Draw Walls"),
    ("erase", "Erase"),
):
    tk.Radiobutton(
        controls_card,
        text=label,
        variable=draw_mode,
        value=mode,
        command=lambda selected=mode: set_draw_mode(selected),
        fg=TEXT,
        bg=PANEL,
        activebackground=PANEL,
        activeforeground=TEXT,
        selectcolor=CARD,
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=2)

btn_style = {
    "bg": CARD,
    "fg": TEXT,
    "activebackground": "#33415c",
    "activeforeground": TEXT,
    "width": 18,
    "font": ("Segoe UI", 10, "bold"),
    "relief": "flat",
    "padx": 8,
    "pady": 8,
}

tk.Button(controls_card, text="Run Selected", command=run_selected, **btn_style).pack(fill="x", pady=(14, 6))
tk.Button(controls_card, text="Generate Maze", command=generate_maze, **btn_style).pack(fill="x", pady=6)
tk.Button(controls_card, text="Compare All", command=compare_all, **btn_style).pack(fill="x", pady=6)
tk.Button(controls_card, text="Clear Grid", command=reset, **btn_style).pack(fill="x", pady=6)

tk.Label(controls_card, text="Animation Speed", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(16, 6))
speed_slider = tk.Scale(
    controls_card,
    from_=0.001,
    to=0.1,
    resolution=0.001,
    orient="horizontal",
    command=change_speed,
    bg=PANEL,
    fg=TEXT,
    highlightthickness=0,
    troughcolor=CARD,
    activebackground=TEXT,
)
speed_slider.set(speed)
speed_slider.pack(fill="x")

speed_value_label = tk.Label(controls_card, text=f"{speed:.3f}s", fg=MUTED, bg=PANEL, font=("Segoe UI", 9))
speed_value_label.pack(anchor="e")

stats_card = tk.Frame(side_panel, bg=PANEL, padx=16, pady=16)
stats_card.pack(fill="x", pady=(16, 0))

tk.Label(stats_card, text="Run Stats", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w")
step_label = tk.Label(stats_card, text="Steps: 0", fg=TEXT, bg=PANEL, font=("Segoe UI", 10))
step_label.pack(anchor="w", pady=(10, 4))
result_label = tk.Label(
    stats_card,
    text="Ready to run",
    fg=MUTED,
    bg=PANEL,
    wraplength=280,
    justify="left",
    font=("Segoe UI", 10),
)
result_label.pack(anchor="w")

legend_card = tk.Frame(side_panel, bg=PANEL, padx=16, pady=16)
legend_card.pack(fill="x", pady=(16, 0))

tk.Label(legend_card, text="Legend", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w")
legend(legend_card, GREEN, "Start")
legend(legend_card, RED, "End")
legend(legend_card, YELLOW, "Visited")
legend(legend_card, TEAL, "Hill Climbing Trail")
legend(legend_card, BLUE, "Final Path")
legend(legend_card, BLACK, "Wall")

tips_card = tk.Frame(side_panel, bg=PANEL, padx=16, pady=16)
tips_card.pack(fill="x", pady=(16, 0))

tk.Label(tips_card, text="Quick Tips", fg=TEXT, bg=PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w")
tk.Label(
    tips_card,
    text=(
        "1. Choose a draw mode.\n"
        "2. Place start and end nodes.\n"
        "3. Draw or erase walls by dragging.\n"
        "4. Run one algorithm or compare them all.\n"
        "5. Right-click any cell to erase it quickly."
    ),
    fg=MUTED,
    bg=PANEL,
    justify="left",
    font=("Segoe UI", 9),
).pack(anchor="w", pady=(8, 0))

grid = [[Node(i, j, canvas) for j in range(ROWS)] for i in range(ROWS)]
start = None
end = None

canvas.bind("<Button-1>", click)
canvas.bind("<B1-Motion>", drag)
canvas.bind("<ButtonRelease-1>", release)
canvas.bind("<Button-3>", right_click)
canvas.bind("<Motion>", on_hover)

set_draw_mode("wall")
root.mainloop()