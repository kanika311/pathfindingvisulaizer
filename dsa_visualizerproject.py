import tkinter as tk
from tkinter import ttk
from queue import PriorityQueue
import time
from collections import deque
import random
import operator

BG = "#0f172a"
PANEL = "#111c33"
CARD = "#18264a"
TEXT = "#eef2ff"
MUTED = "#b6c2e2"
ACCENT = "#60a5fa"
SUCCESS = "#34d399"
WARNING = "#fbbf24"
DANGER = "#fb7185"


def setup_theme(root_window: tk.Tk):
    style = ttk.Style(root_window)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=PANEL)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 18, "bold"))
    style.configure("Section.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 11, "bold"))

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=(12, 8), font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", TEXT)])

    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#0b1220",
        padding=(12, 8),
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
    )
    style.map("Primary.TButton", background=[("active", "#7bb6ff")])

    style.configure(
        "Ghost.TButton",
        background=PANEL,
        foreground=TEXT,
        padding=(12, 8),
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
    )
    style.map("Ghost.TButton", background=[("active", CARD)])

    style.configure("TEntry", padding=6, fieldbackground="#ffffff", foreground="#0b1220")
    style.configure("TCombobox", padding=6)
    style.configure("TRadiobutton", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
    style.map("TRadiobutton", background=[("active", PANEL)], foreground=[("active", TEXT)])


def make_card(parent, padx=14, pady=14):
    frame = ttk.Frame(parent, style="Card.TFrame", padding=(padx, pady))
    return frame


# ---------------- MAIN ----------------
root = tk.Tk()
root.title("DSA Visualizer Pro")
root.geometry("1200x750")
root.configure(bg=BG)
root.minsize(1100, 700)

setup_theme(root)

app = ttk.Frame(root)
app.pack(fill="both", expand=True, padx=16, pady=16)

header = ttk.Frame(app)
header.pack(fill="x", pady=(0, 12))

ttk.Label(header, text="DSA Visualizer Pro", style="Title.TLabel").pack(anchor="w")
ttk.Label(
    header,
    text="Interactive visual learning for Expressions, Pathfinding, and Graph Traversals.",
    style="Muted.TLabel",
).pack(anchor="w", pady=(4, 0))

notebook = ttk.Notebook(app)
notebook.pack(fill="both", expand=True)

# =====================================================
# 🧮 EXPRESSION TAB
# =====================================================
expr_frame = ttk.Frame(notebook)
notebook.add(expr_frame, text="Expression")

expr_layout = ttk.Frame(expr_frame)
expr_layout.pack(fill="both", expand=True, padx=14, pady=14)

expr_left = make_card(expr_layout)
expr_left.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 12))

expr_right = make_card(expr_layout)
expr_right.pack(side=tk.RIGHT, fill="y")

ttk.Label(expr_left, text="Expression Evaluator", style="Section.TLabel").pack(anchor="w")
ttk.Label(
    expr_left,
    text="Enter an infix expression. Supports multi-digit numbers, parentheses, and +  -  *  / operators.",
    style="Muted.TLabel",
).pack(anchor="w", pady=(6, 12))

expr_entry = ttk.Entry(expr_left)
expr_entry.pack(fill="x")
expr_entry.insert(0, "12 + (7 * 3) - 4 / 2")

output_frame = ttk.Frame(expr_left, style="Card.TFrame")
output_frame.pack(fill="both", expand=True, pady=(12, 0))

output_box = tk.Text(
    output_frame,
    height=18,
    wrap="word",
    bg="#0b1220",
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    padx=12,
    pady=12,
)
output_box.pack(side=tk.LEFT, fill="both", expand=True)
scroll = ttk.Scrollbar(output_frame, command=output_box.yview)
scroll.pack(side=tk.RIGHT, fill="y")
output_box.configure(yscrollcommand=scroll.set)

expr_status = tk.StringVar(value="Tip: Press Enter to evaluate.")
ttk.Label(expr_left, textvariable=expr_status, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

expr_history = []


def tokenize_expression(expr: str):
    tokens = []
    number = ""
    for ch in expr.replace(" ", ""):
        if ch.isdigit() or ch == ".":
            number += ch
            continue
        if number:
            tokens.append(number)
            number = ""
        if ch in "+-*/()":
            tokens.append(ch)
        else:
            raise ValueError(f"Invalid character: {ch!r}")
    if number:
        tokens.append(number)
    return tokens


def precedence(op):
    return {"+": 1, "-": 1, "*": 2, "/": 2}.get(op, 0)


def infix_to_postfix(expr: str):
    stack, output = [], []
    tokens = tokenize_expression(expr)

    for tok in tokens:
        if tok.replace(".", "", 1).isdigit():
            output.append(tok)
        elif tok == "(":
            stack.append(tok)
        elif tok == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()
        else:
            while stack and precedence(stack[-1]) >= precedence(tok):
                output.append(stack.pop())
            stack.append(tok)

    while stack:
        if stack[-1] in "()":
            raise ValueError("Mismatched parentheses")
        output.append(stack.pop())
    return output


OPS = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}


def safe_eval_postfix(postfix):
    stack = []
    for tok in postfix:
        if tok.replace(".", "", 1).isdigit():
            stack.append(float(tok) if "." in tok else int(tok))
        else:
            if len(stack) < 2:
                raise ValueError("Invalid expression")
            b, a = stack.pop(), stack.pop()
            stack.append(OPS[tok](a, b))
    if len(stack) != 1:
        raise ValueError("Invalid expression")
    return stack[0]


def show_expression_output(text: str):
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)


def evaluate():
    expr = expr_entry.get().strip()
    if not expr:
        expr_status.set("Please enter an expression.")
        show_expression_output("")
        return
    try:
        postfix = infix_to_postfix(expr)
        result = safe_eval_postfix(postfix)
        expr_status.set("Evaluated successfully.")
        show_expression_output(f"Infix:  {expr}\nPostfix: {' '.join(postfix)}\n\nResult: {result}")
        if not expr_history or expr_history[-1] != expr:
            expr_history.append(expr)
            del expr_history[:-15]
            refresh_expr_history()
    except Exception as exc:
        expr_status.set("Could not evaluate expression.")
        show_expression_output(f"Error: {exc}")


def clear_expression():
    expr_entry.delete(0, tk.END)
    show_expression_output("")
    expr_status.set("Cleared. Enter a new expression.")


def copy_output():
    root.clipboard_clear()
    root.clipboard_append(output_box.get("1.0", tk.END).strip())
    expr_status.set("Copied output to clipboard.")


def refresh_expr_history():
    expr_history_box.config(state="normal")
    expr_history_box.delete(0, tk.END)
    for item in reversed(expr_history):
        expr_history_box.insert(tk.END, item)
    expr_history_box.config(state="disabled")


def load_history(_event=None):
    selection = expr_history_box.curselection()
    if not selection:
        return
    value = expr_history_box.get(selection[0])
    expr_entry.delete(0, tk.END)
    expr_entry.insert(0, value)
    evaluate()


expr_entry.bind("<Return>", lambda _e: evaluate())
expr_entry.bind("<Control-l>", lambda _e: clear_expression())
expr_entry.bind("<Control-L>", lambda _e: clear_expression())
expr_entry.bind("<Control-c>", lambda _e: copy_output())
expr_entry.bind("<Control-C>", lambda _e: copy_output())

ttk.Label(expr_right, text="Actions", style="Section.TLabel").pack(anchor="w")
ttk.Button(expr_right, text="Evaluate (Enter)", style="Primary.TButton", command=evaluate).pack(fill="x", pady=(10, 8))
ttk.Button(expr_right, text="Copy Output", style="Ghost.TButton", command=copy_output).pack(fill="x", pady=6)
ttk.Button(expr_right, text="Clear", style="Ghost.TButton", command=clear_expression).pack(fill="x", pady=6)

ttk.Label(expr_right, text="Examples", style="Section.TLabel").pack(anchor="w", pady=(16, 8))
for sample in ("3+4*2", "12+(7*3)-4/2", "(10-3)*(2+5)", "100/4+6*3"):
    ttk.Button(
        expr_right,
        text=sample,
        style="Ghost.TButton",
        command=lambda s=sample: (expr_entry.delete(0, tk.END), expr_entry.insert(0, s), evaluate()),
    ).pack(fill="x", pady=4)

ttk.Label(expr_right, text="History (double-click)", style="Section.TLabel").pack(anchor="w", pady=(16, 8))
expr_history_box = tk.Listbox(
    expr_right,
    height=8,
    bg="#0b1220",
    fg=TEXT,
    selectbackground=CARD,
    selectforeground=TEXT,
    relief="flat",
    highlightthickness=0,
)
expr_history_box.pack(fill="x")
expr_history_box.config(state="disabled")
expr_history_box.bind("<Double-Button-1>", load_history)

# =====================================================
# 🧭 PATHFINDING TAB
# =====================================================
path_frame = ttk.Frame(notebook)
notebook.add(path_frame, text="Pathfinding")

path_layout = ttk.Frame(path_frame)
path_layout.pack(fill="both", expand=True, padx=14, pady=14)

path_left = make_card(path_layout)
path_left.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 12))

path_right = make_card(path_layout)
path_right.pack(side=tk.RIGHT, fill="y")

ttk.Label(path_left, text="Grid Pathfinding", style="Section.TLabel").pack(anchor="w")
ttk.Label(
    path_left,
    text="Use modes to place Start/End, draw walls, erase, then run an algorithm. Drag to draw/erase quickly.",
    style="Muted.TLabel",
).pack(anchor="w", pady=(6, 12))

ROWS, SIZE = 20, 25
CANVAS_SIZE = ROWS * SIZE

path_canvas = tk.Canvas(
    path_left,
    width=CANVAS_SIZE,
    height=CANVAS_SIZE,
    bg="white",
    highlightthickness=0,
)
path_canvas.pack()

path_status = tk.StringVar(value="Choose a mode, then click/drag on the grid.")
ttk.Label(path_left, textvariable=path_status, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

WHITE, BLACK, GREEN, RED, BLUE, YELLOW = "white", "#111111", "#22c55e", "#ef4444", "#3b82f6", "#fbbf24"
TRAIL = "#38bdf8"

path_speed = tk.DoubleVar(value=0.01)
path_steps = tk.IntVar(value=0)
path_draw_mode = tk.StringVar(value="wall")
path_mouse_down = False
path_algo = tk.StringVar(value="Dijkstra")


class Node:
    def __init__(self, r, c):
        self.r, self.c = r, c
        self.rect = path_canvas.create_rectangle(
            c * SIZE,
            r * SIZE,
            c * SIZE + SIZE,
            r * SIZE + SIZE,
            fill=WHITE,
            outline="#d9dce2",
        )
        self.color = WHITE
        self.neigh = []

    def set(self, color):
        self.color = color
        path_canvas.itemconfig(self.rect, fill=color)

    def is_wall(self):
        return self.color == BLACK


grid = [[Node(i, j) for j in range(ROWS)] for i in range(ROWS)]
start = None
end = None


def path_refresh_stats():
    step_label_pf.config(text=f"Steps: {path_steps.get()}")


def path_visualize():
    path_steps.set(path_steps.get() + 1)
    path_refresh_stats()
    root.update_idletasks()
    root.update()
    time.sleep(path_speed.get())


def get_cell(event):
    r, c = event.y // SIZE, event.x // SIZE
    if 0 <= r < ROWS and 0 <= c < ROWS:
        return grid[r][c]
    return None


def set_mode(mode):
    path_draw_mode.set(mode)
    info = {
        "start": "Click a cell to set the Start node.",
        "end": "Click a cell to set the End node.",
        "wall": "Click/drag to draw walls.",
        "erase": "Click/drag to erase cells.",
    }
    path_status.set(info[mode])


def erase_node(node):
    global start, end
    if node == start:
        start = None
    if node == end:
        end = None
    node.set(WHITE)


def apply_mode(node):
    global start, end
    if node is None:
        return

    mode = path_draw_mode.get()
    if mode == "start":
        if start and start != end:
            start.set(WHITE)
        if node == end:
            end = None
        start = node
        start.set(GREEN)
        path_status.set("Start set. Now place End or draw walls.")
    elif mode == "end":
        if end and end != start:
            end.set(WHITE)
        if node == start:
            start = None
        end = node
        end.set(RED)
        path_status.set("End set. Draw walls or run an algorithm.")
    elif mode == "wall":
        if node not in (start, end):
            node.set(BLACK)
    elif mode == "erase":
        erase_node(node)


def path_click(event):
    global path_mouse_down
    path_mouse_down = True
    apply_mode(get_cell(event))


def path_drag(event):
    if not path_mouse_down:
        return
    if path_draw_mode.get() in ("wall", "erase"):
        apply_mode(get_cell(event))


def path_release(_event):
    global path_mouse_down
    path_mouse_down = False


def path_right_click(event):
    node = get_cell(event)
    if node:
        erase_node(node)


def update_neighbors():
    for row in grid:
        for n in row:
            n.neigh = []
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = n.r + dr, n.c + dc
                if 0 <= nr < ROWS and 0 <= nc < ROWS and not grid[nr][nc].is_wall():
                    n.neigh.append(grid[nr][nc])


def clear_search():
    for row in grid:
        for n in row:
            if n.color not in (GREEN, RED, BLACK):
                n.set(WHITE)


def reset_grid():
    global grid, start, end
    path_canvas.delete("all")
    grid = [[Node(i, j) for j in range(ROWS)] for i in range(ROWS)]
    start = end = None
    path_steps.set(0)
    path_refresh_stats()
    path_status.set("Grid cleared.")


def clear_walls():
    for row in grid:
        for n in row:
            if n.color == BLACK:
                n.set(WHITE)
    path_status.set("Walls cleared.")


def random_walls(density=0.28):
    for row in grid:
        for n in row:
            if n in (start, end):
                continue
            if n.color == BLACK:
                n.set(WHITE)
            if random.random() < density:
                n.set(BLACK)
    path_status.set("Random walls generated. Adjust and run an algorithm.")


def reconstruct(parent):
    cur = end
    while cur in parent:
        cur = parent[cur]
        if cur != start:
            cur.set(BLUE)
            path_visualize()


def run_guard(name):
    if not start or not end:
        path_status.set("Place both Start and End before running.")
        return False
    clear_search()
    update_neighbors()
    path_steps.set(0)
    path_refresh_stats()
    path_status.set(f"Running {name}...")
    return True


def dijkstra():
    if not run_guard("Dijkstra"):
        return

    dist = {n: float("inf") for row in grid for n in row}
    dist[start] = 0
    pq = PriorityQueue()
    pq.put((0, 0, start))
    parent = {}
    count = 0

    while not pq.empty():
        _, _, cur = pq.get()
        if cur == end:
            break
        for n in cur.neigh:
            nd = dist[cur] + 1
            if nd < dist[n]:
                dist[n] = nd
                parent[n] = cur
                count += 1
                pq.put((nd, count, n))
                if n not in (start, end):
                    n.set(YELLOW)
                path_visualize()

    reconstruct(parent)
    path_status.set("Dijkstra finished.")


def bellman_ford():
    if not run_guard("Bellman-Ford"):
        return

    nodes = [n for row in grid for n in row]
    dist = {n: float("inf") for n in nodes}
    dist[start] = 0
    parent = {}

    for _ in range(len(nodes) - 1):
        changed = False
        for n in nodes:
            if dist[n] == float("inf"):
                continue
            for nei in n.neigh:
                if dist[n] + 1 < dist[nei]:
                    dist[nei] = dist[n] + 1
                    parent[nei] = n
                    changed = True
                    if nei not in (start, end):
                        nei.set(YELLOW)
        path_visualize()
        if not changed:
            break

    reconstruct(parent)
    path_status.set("Bellman-Ford finished.")


def floyd_warshall():
    path_status.set("Floyd-Warshall is not visualized here (matrix-based). Add visualization if needed.")


def run_pathfinding():
    choice = path_algo.get()
    if choice == "Dijkstra":
        dijkstra()
    elif choice == "Bellman-Ford":
        bellman_ford()
    elif choice == "Floyd-Warshall (info)":
        floyd_warshall()


path_canvas.bind("<Button-1>", path_click)
path_canvas.bind("<B1-Motion>", path_drag)
path_canvas.bind("<ButtonRelease-1>", path_release)
path_canvas.bind("<Button-3>", path_right_click)

ttk.Label(path_right, text="Controls", style="Section.TLabel").pack(anchor="w")

mode_box = ttk.Frame(path_right, style="Card.TFrame")
mode_box.pack(fill="x", pady=(10, 10))
for mode, label in (("start", "Place Start"), ("end", "Place End"), ("wall", "Draw Walls"), ("erase", "Erase")):
    ttk.Radiobutton(mode_box, text=label, value=mode, variable=path_draw_mode, command=lambda m=mode: set_mode(m)).pack(
        anchor="w", pady=2
    )

ttk.Label(path_right, text="Algorithm", style="Section.TLabel").pack(anchor="w", pady=(10, 6))
algo_combo = ttk.Combobox(
    path_right,
    state="readonly",
    textvariable=path_algo,
    values=("Dijkstra", "Bellman-Ford", "Floyd-Warshall (info)"),
)
algo_combo.pack(fill="x")

ttk.Label(path_right, text="Speed", style="Section.TLabel").pack(anchor="w", pady=(6, 6))
speed_scale = ttk.Scale(path_right, from_=0.001, to=0.05, variable=path_speed)
speed_scale.pack(fill="x")

step_label_pf = ttk.Label(path_right, text="Steps: 0")
step_label_pf.pack(anchor="w", pady=(10, 2))

ttk.Button(path_right, text="Run (Enter)", style="Primary.TButton", command=run_pathfinding).pack(fill="x", pady=(12, 8))
ttk.Button(path_right, text="Random Walls (R)", style="Ghost.TButton", command=random_walls).pack(fill="x", pady=6)
ttk.Button(path_right, text="Clear Walls", style="Ghost.TButton", command=clear_walls).pack(fill="x", pady=6)
ttk.Button(path_right, text="Clear Grid (C)", style="Ghost.TButton", command=reset_grid).pack(fill="x", pady=6)

ttk.Label(path_right, text="Legend", style="Section.TLabel").pack(anchor="w", pady=(16, 8))
legend_pf = ttk.Frame(path_right, style="Card.TFrame")
legend_pf.pack(fill="x")
for color, label in ((GREEN, "Start"), (RED, "End"), (BLACK, "Wall"), (YELLOW, "Visited"), (BLUE, "Path")):
    row = ttk.Frame(legend_pf, style="Card.TFrame")
    row.pack(anchor="w", pady=2)
    swatch = tk.Label(row, bg=color, width=2)
    swatch.pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(row, text=label).pack(side=tk.LEFT)

set_mode("wall")

# Pathfinding shortcuts
root.bind("<Return>", lambda _e: run_pathfinding())
root.bind("<KeyPress-s>", lambda _e: set_mode("start"))
root.bind("<KeyPress-e>", lambda _e: set_mode("end"))
root.bind("<KeyPress-w>", lambda _e: set_mode("wall"))
root.bind("<KeyPress-x>", lambda _e: set_mode("erase"))
root.bind("<KeyPress-c>", lambda _e: reset_grid())
root.bind("<KeyPress-r>", lambda _e: random_walls())

# =====================================================
# 🕸️ GRAPH PRO TAB
# =====================================================
graph_frame = ttk.Frame(notebook)
notebook.add(graph_frame, text="Graph Pro")

graph_layout = ttk.Frame(graph_frame)
graph_layout.pack(fill="both", expand=True, padx=14, pady=14)

graph_left = make_card(graph_layout)
graph_left.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 12))

graph_right = make_card(graph_layout)
graph_right.pack(side=tk.RIGHT, fill="y")

ttk.Label(graph_left, text="Graph Builder + Traversal", style="Section.TLabel").pack(anchor="w")
ttk.Label(
    graph_left,
    text="Add nodes, connect edges, move nodes, then visualize BFS/DFS. In Connect mode, click two nodes to add an edge.",
    style="Muted.TLabel",
).pack(anchor="w", pady=(6, 12))

g_canvas = tk.Canvas(graph_left, bg="white", width=820, height=560, highlightthickness=0)
g_canvas.pack()

graph_status = tk.StringVar(value="Mode: Add Node. Click empty space to add a node.")
ttk.Label(graph_left, textvariable=graph_status, style="Muted.TLabel").pack(anchor="w", pady=(10, 0))

nodes = []
adj = {}
selected = None
dragging = None
mode = tk.StringVar(value="add")
node_radius = 18
edge_lines = {}
graph_speed = tk.DoubleVar(value=0.25)
graph_start = tk.StringVar(value="")


def set_graph_mode(m):
    global selected, dragging
    mode.set(m)
    selected = None
    dragging = None
    reset_colors()
    if m == "add":
        graph_status.set("Mode: Add Node. Click empty space to add a node.")
    elif m == "connect":
        graph_status.set("Mode: Connect. Click a node then click another node to connect them.")
    else:
        graph_status.set("Mode: Move. Drag a node to reposition it.")


def add_node(e):
    label = chr(65 + len(nodes))
    node = g_canvas.create_oval(
        e.x - node_radius,
        e.y - node_radius,
        e.x + node_radius,
        e.y + node_radius,
        fill="#7dd3fc",
        outline="#0ea5e9",
        width=2,
    )
    text = g_canvas.create_text(e.x, e.y, text=label, fill="#0b1220", font=("Segoe UI", 10, "bold"))
    nodes.append((node, text, e.x, e.y, label))
    adj[label] = []
    if not graph_start.get():
        graph_start.set(label)
    refresh_adjacency()


def get_node(x, y):
    for node, text, nx, ny, label in nodes:
        if abs(nx - x) < node_radius and abs(ny - y) < node_radius:
            return (node, text, nx, ny, label)
    return None


def draw_edge(a, b):
    key = tuple(sorted((a, b)))
    if key in edge_lines:
        return
    ax, ay = next((x, y) for _, _, x, y, l in nodes if l == a)
    bx, by = next((x, y) for _, _, x, y, l in nodes if l == b)
    line = g_canvas.create_line(ax, ay, bx, by, fill="#94a3b8", width=2)
    edge_lines[key] = line


def redraw_edges():
    for (a, b), line in edge_lines.items():
        ax, ay = next((x, y) for _, _, x, y, l in nodes if l == a)
        bx, by = next((x, y) for _, _, x, y, l in nodes if l == b)
        g_canvas.coords(line, ax, ay, bx, by)


def refresh_adjacency():
    rows = []
    for k in sorted(adj.keys()):
        rows.append(f"{k}: {', '.join(sorted(adj[k])) if adj[k] else '-'}")
    graph_adj_box.config(state="normal")
    graph_adj_box.delete("1.0", tk.END)
    graph_adj_box.insert(tk.END, "\n".join(rows) if rows else "No nodes yet.")
    graph_adj_box.config(state="disabled")
    starts = sorted(adj.keys())
    graph_start_combo.config(values=starts)
    if graph_start.get() and graph_start.get() not in starts:
        graph_start.set(starts[0] if starts else "")
    if not graph_start.get() and starts:
        graph_start.set(starts[0])


def canvas_click(e):
    global selected, dragging
    node = get_node(e.x, e.y)

    if mode.get() == "add":
        if not node:
            add_node(e)
        return

    if mode.get() == "connect":
        if not node:
            return
        if not selected:
            selected = node
            g_canvas.itemconfig(node[0], fill=WARNING)
            graph_status.set(f"Selected {node[4]}. Now click another node to connect.")
        else:
            if selected[4] != node[4]:
                a, b = selected[4], node[4]
                adj[a].append(b)
                adj[b].append(a)
                draw_edge(a, b)
                graph_status.set(f"Connected {a} ↔ {b}.")
                refresh_adjacency()
            reset_colors()
            selected = None
        return

    if mode.get() == "move":
        dragging = node


def drag(e):
    global dragging
    if mode.get() != "move" or not dragging:
        return
    node_id, text_id, _, _, label = dragging
    g_canvas.coords(node_id, e.x - node_radius, e.y - node_radius, e.x + node_radius, e.y + node_radius)
    g_canvas.coords(text_id, e.x, e.y)
    for i, n in enumerate(nodes):
        if n[4] == label:
            nodes[i] = (node_id, text_id, e.x, e.y, label)
            break
    redraw_edges()


def stop_drag(_e):
    global dragging
    dragging = None


def delete_node(label):
    global selected, dragging
    for node_id, text_id, x, y, l in list(nodes):
        if l == label:
            g_canvas.delete(node_id)
            g_canvas.delete(text_id)
            nodes.remove((node_id, text_id, x, y, l))
            break

    for other in list(adj.get(label, [])):
        if other in adj:
            adj[other] = [x for x in adj[other] if x != label]
        key = tuple(sorted((label, other)))
        if key in edge_lines:
            g_canvas.delete(edge_lines[key])
            del edge_lines[key]

    if label in adj:
        del adj[label]

    for key in list(edge_lines.keys()):
        if label in key:
            g_canvas.delete(edge_lines[key])
            del edge_lines[key]

    selected = None
    dragging = None
    reset_colors()
    refresh_adjacency()
    graph_status.set(f"Deleted node {label}.")


def graph_right_click(e):
    node = get_node(e.x, e.y)
    if node:
        delete_node(node[4])


def highlight(label, color):
    for node_id, _text, _x, _y, l in nodes:
        if l == label:
            g_canvas.itemconfig(node_id, fill=color)


def reset_colors():
    for node_id, _text, _x, _y, _l in nodes:
        g_canvas.itemconfig(node_id, fill="#7dd3fc")


def bfs():
    if not nodes:
        graph_status.set("Add at least one node to run BFS.")
        return
    graph_status.set("Running BFS...")
    visited = set()
    start_label = graph_start.get() or nodes[0][4]
    q = deque([start_label])
    visited.add(start_label)

    while q:
        cur = q.popleft()
        highlight(cur, YELLOW)
        root.update()
        time.sleep(graph_speed.get())
        for nei in adj[cur]:
            if nei not in visited:
                visited.add(nei)
                q.append(nei)

    reset_colors()
    graph_status.set("BFS finished.")


def dfs():
    if not nodes:
        graph_status.set("Add at least one node to run DFS.")
        return
    graph_status.set("Running DFS...")
    visited = set()
    start_label = graph_start.get() or nodes[0][4]
    stack = [start_label]

    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        highlight(cur, SUCCESS)
        root.update()
        time.sleep(graph_speed.get())
        for nei in adj[cur]:
            if nei not in visited:
                stack.append(nei)

    reset_colors()
    graph_status.set("DFS finished.")


def clear_graph():
    global selected, dragging
    g_canvas.delete("all")
    nodes.clear()
    adj.clear()
    edge_lines.clear()
    selected = None
    dragging = None
    refresh_adjacency()
    graph_status.set("Cleared. Mode: Add Node.")


g_canvas.bind("<Button-1>", canvas_click)
g_canvas.bind("<B1-Motion>", drag)
g_canvas.bind("<ButtonRelease-1>", stop_drag)
g_canvas.bind("<Button-3>", graph_right_click)

ttk.Label(graph_right, text="Mode", style="Section.TLabel").pack(anchor="w")
mode_box = ttk.Frame(graph_right, style="Card.TFrame")
mode_box.pack(fill="x", pady=(10, 10))
for m, label in (("add", "Add Node"), ("connect", "Connect"), ("move", "Move")):
    ttk.Radiobutton(mode_box, text=label, value=m, variable=mode, command=lambda mm=m: set_graph_mode(mm)).pack(
        anchor="w", pady=2
    )

ttk.Label(graph_right, text="Traversal", style="Section.TLabel").pack(anchor="w", pady=(6, 6))
ttk.Label(graph_right, text="Start Node", style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
graph_start_combo = ttk.Combobox(graph_right, state="readonly", textvariable=graph_start, values=())
graph_start_combo.pack(fill="x", pady=(0, 8))
ttk.Label(graph_right, text="Speed", style="Muted.TLabel").pack(anchor="w", pady=(2, 4))
ttk.Scale(graph_right, from_=0.05, to=0.6, variable=graph_speed).pack(fill="x", pady=(0, 10))
ttk.Button(graph_right, text="Run BFS", style="Primary.TButton", command=bfs).pack(fill="x", pady=(6, 8))
ttk.Button(graph_right, text="Run DFS", style="Ghost.TButton", command=dfs).pack(fill="x", pady=6)
ttk.Button(graph_right, text="Clear Graph", style="Ghost.TButton", command=clear_graph).pack(fill="x", pady=6)

ttk.Label(graph_right, text="Adjacency List", style="Section.TLabel").pack(anchor="w", pady=(16, 8))
graph_adj_box = tk.Text(
    graph_right,
    height=16,
    width=28,
    wrap="none",
    bg="#0b1220",
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    padx=10,
    pady=10,
)
graph_adj_box.pack(fill="both", expand=True)
graph_adj_box.config(state="disabled")
refresh_adjacency()
set_graph_mode("add")

# =====================================================
root.mainloop()