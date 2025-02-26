import math
import random
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog

class SpirographApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spirograph Generator")

        # === Variables ===
        self.spiro_type_var = tk.StringVar(value="Hypotrochoid")  # or "Epitrochoid"
        self.R_var = tk.DoubleVar(value=125.0)  # large circle radius
        self.r_var = tk.DoubleVar(value=75.0)   # small circle radius
        self.l_var = tk.DoubleVar(value=55.0)   # offset
        self.cycles_var = tk.IntVar(value=3)    # how many times small circle rotates
        self.thickness_var = tk.DoubleVar(value=2.0)  # line thickness

        # Show circles?
        self.show_circles_var = tk.BooleanVar(value=False)

        # Color mode
        #   "Single Color"       => the user’s chosen color
        #   "Random Cycle Colors" => each cycle in a spirograph gets a random color
        self.color_mode_var = tk.StringVar(value="Random Cycle Colors")
        self.single_color_var = tk.StringVar(value="#FF0000")  # default if single color

        # Nested spirographs
        self.nested_count_var = tk.IntVar(value=1)  # how many spirographs to draw in sequence

        # Animation state
        self.animation_running = False
        self.timer_id = None

        # Data for drawing
        # Each element in self.all_spiros = (R, r, points, color_list)
        #   R, r: radii used
        #   points: scaled coordinate list
        #   color_list: random color for each cycle (or a single color).
        self.all_spiros = []
        self.current_spiro_index = 0   # which spiro in the nested sequence
        self.current_point_index = 0   # which point in the current spiro

        # Create the UI
        self.create_widgets()

    def create_widgets(self):
        # ------------------ Control Panel ------------------
        control_frame = ttk.Frame(self.root, padding="5 5 5 5")
        control_frame.grid(row=0, column=0, sticky="ns")

        row_idx = 0

        # Spiro type
        ttk.Label(control_frame, text="Spiro Type:").grid(row=row_idx, column=0, sticky="e")
        spiro_type_menu = ttk.OptionMenu(
            control_frame, 
            self.spiro_type_var, 
            self.spiro_type_var.get(), 
            "Hypotrochoid", 
            "Epitrochoid"
        )
        spiro_type_menu.grid(row=row_idx, column=1, padx=5, pady=5)
        row_idx += 1

        # R, r, l
        ttk.Label(control_frame, text="R (Big Circle):").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.R_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        ttk.Label(control_frame, text="r (Small Circle):").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.r_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        ttk.Label(control_frame, text="l (Offset):").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.l_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        # Cycles
        ttk.Label(control_frame, text="# of Cycles:").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.cycles_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        # Nested spirographs
        ttk.Label(control_frame, text="Nested Count:").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.nested_count_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        # Show circles
        ttk.Checkbutton(control_frame, text="Show Circles", variable=self.show_circles_var)\
            .grid(row=row_idx, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        row_idx += 1

        # Color mode
        ttk.Label(control_frame, text="Color Mode:").grid(row=row_idx, column=0, sticky="e")
        color_mode_menu = ttk.OptionMenu(
            control_frame,
            self.color_mode_var,
            self.color_mode_var.get(),
            "Single Color",
            "Random Cycle Colors"
        )
        color_mode_menu.grid(row=row_idx, column=1, padx=5, pady=5)
        row_idx += 1

        # Single color button
        ttk.Label(control_frame, text="Single Color:").grid(row=row_idx, column=0, sticky="e")
        choose_col_btn = ttk.Button(control_frame, text="Pick Color", command=self.choose_color)
        choose_col_btn.grid(row=row_idx, column=1, padx=5, pady=5)
        row_idx += 1

        # Thickness
        ttk.Label(control_frame, text="Line Thickness:").grid(row=row_idx, column=0, sticky="e")
        ttk.Entry(control_frame, textvariable=self.thickness_var, width=8).grid(row=row_idx, column=1, padx=5, pady=2)
        row_idx += 1

        # Randomize Params button
        random_btn = ttk.Button(control_frame, text="Randomize Params", command=self.randomize_params)
        random_btn.grid(row=row_idx, column=0, padx=5, pady=5, sticky="ew")

        # Play/Stop
        self.play_button = ttk.Button(control_frame, text="Play", command=self.toggle_animation)
        self.play_button.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Save
        save_button = ttk.Button(control_frame, text="Save Image", command=self.save_image)
        save_button.grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # ------------------ Drawing Canvas ------------------
        self.canvas = tk.Canvas(self.root, bg="white", width=700, height=700)
        self.canvas.grid(row=0, column=1, sticky="nsew")

        # Let the canvas expand
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

    def choose_color(self):
        """Pick a color for 'Single Color' mode."""
        color_code = colorchooser.askcolor(title="Choose a color", initialcolor=self.single_color_var.get())
        if color_code[1] is not None:
            self.single_color_var.set(color_code[1])

    def randomize_params(self):
        """Fill in the parameter fields with random values in a reasonable range."""
        spiro_type = random.choice(["Hypotrochoid", "Epitrochoid"])
        R = random.uniform(50, 150)
        # Ensure r < R for Hypotrochoid to stay interesting (though Epitrochoid can have many combos)
        # We'll just do a simpler approach:
        r = random.uniform(10, max(10, R - 5))
        l = random.uniform(5, r)
        cycles = random.randint(2, 10)
        nested_count = random.randint(1, 4)

        self.spiro_type_var.set(spiro_type)
        self.R_var.set(round(R, 2))
        self.r_var.set(round(r, 2))
        self.l_var.set(round(l, 2))
        self.cycles_var.set(cycles)
        self.nested_count_var.set(nested_count)

    def toggle_animation(self):
        if not self.animation_running:
            self.play_button.config(text="Stop")
            self.start_animation()
        else:
            self.play_button.config(text="Play")
            self.stop_animation()

    def start_animation(self):
        self.animation_running = True
        self.canvas.delete("all")

        # Generate spirographs (up to nested_count)
        self.all_spiros = []
        for i in range(self.nested_count_var.get()):
            points = self.generate_spiro_points(
                spiro_type=self.spiro_type_var.get(),
                R=self.R_var.get(),
                r=self.r_var.get(),
                l=self.l_var.get(),
                cycles=self.cycles_var.get()
            )
            # Build a list of colors for each cycle if we are in "Random Cycle Colors" mode
            if self.color_mode_var.get() == "Random Cycle Colors":
                color_list = []
                for c in range(self.cycles_var.get()):
                    # Random color
                    color = "#%06x" % random.randint(0, 0xFFFFFF)
                    color_list.append(color)
            else:
                # Single color mode
                color_list = [self.single_color_var.get()]

            self.all_spiros.append((self.R_var.get(), self.r_var.get(), points, color_list))

        self.current_spiro_index = 0
        self.current_point_index = 0

        self.draw_next_segment()

    def stop_animation(self):
        self.animation_running = False
        if self.timer_id is not None:
            self.canvas.after_cancel(self.timer_id)
            self.timer_id = None

    def generate_spiro_points(self, spiro_type, R, r, l, cycles):
        """
        Generate points for a spirograph.

        Hypotrochoid (circle rolling *inside*):
            x(θ) = (R - r)*cos(θ) + l*cos(((R - r)/r)*θ)
            y(θ) = (R - r)*sin(θ) - l*sin(((R - r)/r)*θ)

        Epitrochoid (circle rolling *outside*):
            x(θ) = (R + r)*cos(θ) - l*cos(((R + r)/r)*θ)
            y(θ) = (R + r)*sin(θ) - l*sin(((R + r)/r)*θ)

        We iterate from θ=0 up to the # of cycles * 2π.
        """
        points = []
        steps_per_circle = 1000
        total_steps = cycles * steps_per_circle

        for i in range(total_steps + 1):
            theta = 2.0 * math.pi * i / steps_per_circle
            if spiro_type == "Hypotrochoid":
                x = (R - r) * math.cos(theta) + l * math.cos(((R - r)/r)*theta)
                y = (R - r) * math.sin(theta) - l * math.sin(((R - r)/r)*theta)
            else:
                # Epitrochoid
                x = (R + r) * math.cos(theta) - l * math.cos(((R + r)/r)*theta)
                y = (R + r) * math.sin(theta) - l * math.sin(((R + r)/r)*theta)

            points.append((x, y))

        # Scale to fit on canvas
        scaled_points = self.scale_points_to_canvas(points)
        return scaled_points

    def scale_points_to_canvas(self, points):
        if not points:
            return []
        xs, ys = zip(*points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Avoid divide-by-zero
        if max_x == min_x:
            max_x += 1e-9
        if max_y == min_y:
            max_y += 1e-9

        range_x = max_x - min_x
        range_y = max_y - min_y
        scale_factor = min(width / range_x, height / range_y) * 0.8  # 0.8 margin

        center_x = (max_x + min_x) / 2.0
        center_y = (max_y + min_y) / 2.0

        scaled_points = []
        for (x, y) in points:
            sx = (x - center_x) * scale_factor + width / 2
            sy = (y - center_y) * scale_factor + height / 2
            scaled_points.append((sx, sy))
        return scaled_points

    def draw_next_segment(self):
        """Draw the spiro(s) point by point to animate."""
        if not self.animation_running:
            return

        if self.current_spiro_index >= len(self.all_spiros):
            # Finished drawing all nested spiros
            self.stop_animation()
            self.play_button.config(text="Play")
            return

        R, r, points, color_list = self.all_spiros[self.current_spiro_index]
        total_points = len(points)
        if self.current_point_index < total_points - 1:
            x1, y1 = points[self.current_point_index]
            x2, y2 = points[self.current_point_index + 1]

            # Decide color
            if self.color_mode_var.get() == "Random Cycle Colors":
                # cycle_index depends on how many points per cycle
                points_per_cycle = total_points / max(self.cycles_var.get(), 1)
                cycle_index = int(self.current_point_index // points_per_cycle)
                cycle_index = min(cycle_index, len(color_list)-1)  # clamp in range
                color = color_list[cycle_index]
            else:
                # Single color
                color = color_list[0]

            # Draw line
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color,
                width=self.thickness_var.get()
            )

            if self.show_circles_var.get():
                self.draw_current_circles(R, r, points, self.current_point_index)

            self.current_point_index += 1
            self.timer_id = self.canvas.after(1, self.draw_next_segment)
        else:
            # Done with this spiro, go to next
            self.current_spiro_index += 1
            self.current_point_index = 0
            self.canvas.after(50, self.draw_next_segment)

    def draw_current_circles(self, R, r, points, idx):
        """
        Approximate the large circle and rolling small circle.
        (For illustration only—this is not a perfect geometric overlay.)
        """
        self.canvas.delete("circles_tag")

        # Center is roughly the middle of the canvas
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2

        # Approximate big circle radius from first point
        if points:
            x0, y0 = points[0]
            big_r_approx = math.dist((cx, cy), (x0, y0))
        else:
            big_r_approx = 100

        # Draw big circle
        self.canvas.create_oval(
            cx - big_r_approx, cy - big_r_approx,
            cx + big_r_approx, cy + big_r_approx,
            outline="gray", dash=(3, 5), tag="circles_tag"
        )

        # Approximate small circle radius
        if R != 0:
            small_r_approx = (r / R) * big_r_approx
        else:
            small_r_approx = 1

        # The current spiro point:
        if 0 <= idx < len(points):
            px, py = points[idx]
        else:
            px, py = (cx, cy)

        dx = px - cx
        dy = py - cy
        dist = math.sqrt(dx*dx + dy*dy)
        if dist != 0:
            ratio = (dist - small_r_approx)/dist
        else:
            ratio = 0

        scx = cx + dx*ratio
        scy = cy + dy*ratio

        self.canvas.create_oval(
            scx - small_r_approx, scy - small_r_approx,
            scx + small_r_approx, scy + small_r_approx,
            outline="gray", dash=(3, 5), tag="circles_tag"
        )

    def save_image(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ps",
            filetypes=[("PostScript files", "*.ps"), ("All files", "*.*")]
        )
        if file_path:
            self.canvas.postscript(file=file_path)
            print("Saved:", file_path)

def main():
    root = tk.Tk()
    app = SpirographApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
