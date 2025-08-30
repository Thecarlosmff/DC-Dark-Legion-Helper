

import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import funcs

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QLineEdit, QCheckBox,
    QComboBox, QTabWidget, QFileDialog, QTextEdit, QFormLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,QListWidget,QListWidgetItem,QDialog
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, width=6, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)

    def clear(self):
        self.fig.clear()
        self.draw()

    def plot_line(self, xs, ys, label=None):
        ax = self.fig.add_subplot(111)
        ax.plot(xs, ys, marker="o", label=label or "")
        if label:
            ax.legend()
        self.draw()

    def plot_scatter(self, xs, ys, label=None):
        ax = self.fig.add_subplot(111)
        ax.scatter(xs, ys, s=10, alpha=0.5, label=label or "")
        if label:
            ax.legend()
        self.draw()

    def set_labels(self, title=None, xlabel=None, ylabel=None):
        ax = self.fig.axes[0] if self.fig.axes else self.fig.add_subplot(111)
        if title:
            ax.set_title(title)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        self.draw()

    def add_hlines(self, lines):
        ax = self.fig.axes[0] if self.fig.axes else self.fig.add_subplot(111)
        for y, style, label in lines:
            ax.axhline(y=y, linestyle=style, label=label)
        ax.legend()
        self.draw()
class LogPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def log(self, msg: str):
        self.append(msg)

# ---------- Background Worker Thread ----------
class Worker(QThread):
    done = pyqtSignal(object)      # emits the result when finished
    error = pyqtSignal(str)        # emits error messages
    cancelled = pyqtSignal()       # emits if cancelled

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self._running = True  # cancellation flag

        # Always provide stop_flag function to the worker function
        self.kwargs["stop_flag"] = self.stop_flag

    def stop_flag(self):
        """Return True if still running, False if cancelled."""
        return self._running

    def stop(self):
        """Signal the worker to stop."""
        self._running = False

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            if self._running:
                self.done.emit(result)
            else:
                self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))

# ---------- Parameter Panel ----------
class ParametersPanel(QWidget):
    def __init__(self):
        super().__init__()
        # Pity / Non-limited spin boxes
        self.m_pity = QSpinBox()
        self.m_pity.setRange(0, funcs.MAX_MYTHIC_PITY)
        self.m_pity.setValue(0)

        self.l_pity = QSpinBox()
        self.l_pity.setRange(0, funcs.MAX_LEGENDARY_PITY)
        self.l_pity.setValue(0)

        self.pity_banner = QSpinBox()
        self.pity_banner.setRange(0, funcs.MAX_BANNER_PITY)
        self.pity_banner.setValue(0)

        self.non_limited = QSpinBox()
        self.non_limited.setRange(0, 100000)
        self.non_limited.setValue(0)

        # Banner info
        self.boosted_label = QLabel(f"Boosted Champs: {', '.join(funcs.boosted_Mythic_champs)}") 
        # Banner selection combo
        self.banner_combo = QComboBox()
        self.banner_combo.addItems(funcs.banner_Mythic_champions)
        # Set current banner
        idx = self.banner_combo.findText(funcs.banner_Mythic_champ)
        if idx >= 0:
            self.banner_combo.setCurrentIndex(idx)
        self.banner_combo.currentIndexChanged.connect(self.banner_changed)

        # Form layout
        form = QFormLayout()
        form.addRow("Mythic Pity:", self.m_pity)
        form.addRow("Legendary Pity:", self.l_pity)
        form.addRow("Non-banner Mythics since last:", self.pity_banner)
        form.addRow("Non-limited Mythics pulled (this banner):", self.non_limited)
        form.addRow("Select Banner:", self.banner_combo)

        # Layout
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.boosted_label)
        self.setLayout(layout)

        # Connect spin boxes to auto-apply
        self.m_pity.valueChanged.connect(self.auto_apply)
        self.l_pity.valueChanged.connect(self.auto_apply)
        self.pity_banner.valueChanged.connect(self.auto_apply)
        self.non_limited.valueChanged.connect(self.auto_apply)

        # Apply initial values
        self.auto_apply()

    def values(self):
        return (
            self.m_pity.value(),
            self.l_pity.value(),
            self.pity_banner.value(),
            self.non_limited.value()
        )

    def auto_apply(self):
        funcs.session_params = self.values()
        self.refresh_info()

    def banner_changed(self):
        selected = self.banner_combo.currentText()
        funcs.set_banner(selected)
        self.refresh_info()

    def refresh_info(self):
        self.boosted_label.setText(f"Boosted Champs: {', '.join(funcs.boosted_Mythic_champs)}")


# ---------- Tabs ----------

class TabDraw(QWidget): #OK 
    def __init__(self, log_panel):
        super().__init__()
        self.log_panel = log_panel
        self.first_draw = True
        # --- UI Setup ---
        layout = QVBoxLayout()

        self.title_label = QLabel("Draw Simulator")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- buttons ---
        self.draw_button = QPushButton("Draw (Single)")
        self.draw10_button = QPushButton("Draw (10)")
        self.draw_custom_button = QPushButton("Draw (X)")

        self.reset_button = QPushButton("Reset")
        self.pie_button1 = QPushButton("Mythic")
        self.pie_button2 = QPushButton("Legendary")
        self.pie_button3 = QPushButton("Epic")
        self.pie_button4 = QPushButton("Overall")

        # --- log + breakdown split ---
        split_layout = QHBoxLayout()
        self.local_log = QTextEdit()
        self.local_log.setReadOnly(True)
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        split_layout.addWidget(self.local_log, 2)
        split_layout.addWidget(self.results_display, 1)

        # --- group buttons into rows ---
        draw_buttons_layout = QHBoxLayout()
        draw_buttons_layout.addWidget(self.draw_button)
        draw_buttons_layout.addWidget(self.draw10_button)
        draw_buttons_layout.addWidget(self.draw_custom_button)

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.reset_button, 1)

        pie_buttons_layout = QHBoxLayout()
        pie_buttons_layout.addWidget(self.pie_button1, 1)
        pie_buttons_layout.addWidget(self.pie_button4, 1)
        
        pie_buttons_container = QWidget()
        pie_buttons_container.setLayout(pie_buttons_layout)
        
        bottom_buttons_layout.addWidget(pie_buttons_container, 1)
        # --- main layout ---
        layout.addWidget(self.title_label)
        layout.addLayout(split_layout)
        layout.addLayout(draw_buttons_layout)   # row with 3 draw buttons
        layout.addLayout(bottom_buttons_layout) # row with reset + stats

        self.setLayout(layout)

        # --- Connect Buttons ---
        self.reset_button.clicked.connect(self.reset)

        self.draw_button.clicked.connect(lambda: self.do_draw(1))
        self.draw10_button.clicked.connect(lambda: self.do_draw(10))
        self.draw_custom_button.clicked.connect(self.draw_custom)
        self.pie_button1.clicked.connect(lambda: self.finish(1))
        self.pie_button2.clicked.connect(lambda: self.finish(2))
        self.pie_button3.clicked.connect(lambda: self.finish(3))
        self.pie_button4.clicked.connect(lambda: self.finish(4))


    def log(self, msg: str):
        if self.log_panel:
            self.log_panel.log(msg)
        else:
            print(msg)

    def do_draw(self, count=1):  # default = 1 pull
        color_map = {
            "Mythic": "red",
            "Legendary": "gold",
            "Epic": "purple",
        }

        for _ in range(count):
            if self.first_draw:
                pulled = funcs.draw(True, self.first_draw)
                self.first_draw = False
            else:
                pulled = funcs.draw(True, self.first_draw)

            # choose color based on rarity
            rarity = pulled[1]
            color = color_map.get(rarity, "black")

            if pulled[2] == 0:
                entry = f'🎲 Pulled: <span style="color:{color}">{pulled[0]}</span>'
            else:
                entry = f'🎲 Pulled: <span style="color:{color}">{pulled[0]} + {pulled[2]} {funcs.banner_Mythic_champ} shards</span>'

            # append as HTML instead of plain text
            self.local_log.append(entry)

        self.update_breakdown()
    def draw_custom(self):
        from PyQt6.QtWidgets import QInputDialog
        num, ok = QInputDialog.getInt(self, "Custom Draw", "Enter number of pulls:", 1, 1, 100000, 1)
        if ok:
            self.do_draw(num)
    def finish(self,btn):
        chart_choice = btn
        funcs.draw_heros_pie_chart(funcs.results, chart_choice)
    def show_results_in_new_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Session Results")
        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Add the session stats
        text_edit.append("📊 Session Results")
        for value in [funcs.mythic_pity, funcs.legendary_pity, 
                    funcs.non_banner_Mythics_since_last, funcs.numbers_of_non_banner_mysthic_pulls]:
            text_edit.append(str(value))
        
        # Add the breakdown
        breakdown_text = funcs.get_breakdown_text()
        text_edit.append("\n" + breakdown_text)
        
        layout.addWidget(text_edit)

        # Optional close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
    def update_breakdown(self):
        """Update right-side breakdown live"""
        self.results_display.clear()
        self.results_display.append("📊 Session Results")
        self.results_display.append("Pulls: " + str(len(funcs.history)))
        self.results_display.append("Mythic pity at: " + str(funcs.mythic_pity))
        self.results_display.append("Legendary pity at: " + str(funcs.legendary_pity))
        self.results_display.append("Mythics since last limited: " + str(funcs.non_banner_Mythics_since_last))
        self.results_display.append("Non limited in current banner: " + str(funcs.numbers_of_non_banner_mysthic_pulls))
        self.results_display.append("Forced Mythics: " + str(funcs.forced_Mythic_count))
        self.results_display.append("Forced Banner: " + str(funcs.forced_banner_Mythic_count))

        # --- Prepare breakdown text (like get_breakdown_text) ---
        breakdown_text = funcs.get_breakdown_text()
        self.results_display.append("\n" + breakdown_text)
    def reset(self):
        """Reset simulation + reload params panel"""
        # 1. Reset simulation values
        funcs.results.clear()
        funcs.history.clear()
        funcs.mythic_pity = funcs.session_params[0]
        funcs.legendary_pity = funcs.session_params[1]
        funcs.non_banner_Mythics_since_last = funcs.session_params[2]
        funcs.numbers_of_non_banner_mysthic_pulls = funcs.session_params[3]
        self.first_draw = True

        # 3. Clear UI
        self.local_log.clear()
        self.results_display.clear()
        self.log("✅ Simulation reset")
class TabDrawSimulations(QWidget):#OK
    def __init__(self, params_panel, log_widget):
        super().__init__()
        self.params = params_panel
        self.log = log_widget
        self.running = False  # track if a simulation is running

        # --- Inputs for sessions / pulls ---
        self.sessions_input = QSpinBox()
        self.sessions_input.setRange(1, 100000)
        self.sessions_input.setValue(10000)
        self.pulls_input = QSpinBox()
        self.pulls_input.setRange(1, 100000)
        self.pulls_input.setValue(200)

        # --- Labels ---
        sessions_label = QLabel("Num Sessions:")
        pulls_label = QLabel("Pulls per Session:")

        input_layout = QHBoxLayout()
        input_layout.addWidget(sessions_label)
        input_layout.addWidget(self.sessions_input)
        input_layout.addWidget(pulls_label)
        input_layout.addWidget(self.pulls_input)

        # --- Run button ---
        self.btn_run = QPushButton("Run Draw Simulations")
        self.btn_run.clicked.connect(self.toggle_run)

        # --- Pie chart buttons ---
        self.pie_button1 = QPushButton("Mythic")
        self.pie_button2 = QPushButton("Legendary")
        self.pie_button3 = QPushButton("Epic")
        self.pie_button4 = QPushButton("Overall")

        pie_buttons_layout = QHBoxLayout()
        pie_buttons_layout.addWidget(self.pie_button1)
        pie_buttons_layout.addWidget(self.pie_button2)
        pie_buttons_layout.addWidget(self.pie_button3)
        pie_buttons_layout.addWidget(self.pie_button4)

        # --- QTextEdit to display statistics ---
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addWidget(self.btn_run)
        layout.addLayout(pie_buttons_layout)
        layout.addWidget(self.stats_display)
        self.setLayout(layout)

        # --- Connect pie chart buttons ---
        self.pie_button1.clicked.connect(lambda: self.show_pie_chart(1))
        self.pie_button2.clicked.connect(lambda: self.show_pie_chart(2))
        self.pie_button3.clicked.connect(lambda: self.show_pie_chart(3))
        self.pie_button4.clicked.connect(lambda: self.show_pie_chart(4))

        # Store last results for pie charts
        self.last_results = None
        self.worker = None

    def toggle_run(self):
        if self.running:
            # Cancel the running simulation
            if self.worker:
                self.worker.stop()
                self.log.append("Simulation cancellation requested...")
        else:
            self.run_multi_draw()

    def run_multi_draw(self):
        self.stats_display.clear()
        self.stats_display.append("Running simulation. Please wait!")
        self.log.append("Running multi draw...")

        num_sessions = self.sessions_input.value()
        pulls_per_session = self.pulls_input.value()

        # Disable pie buttons while running
        for btn in [self.pie_button1, self.pie_button2, self.pie_button3, self.pie_button4]:
            btn.setEnabled(False)

        self.btn_run.setText("Cancel Simulation")
        self.running = True

        # Create worker
        self.worker = Worker(
            funcs.simulate_multiple_sessions,
            num_sessions,
            pulls_per_session,
            show_output=True
        )
        self.worker.done.connect(self.on_simulation_done)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.cancelled.connect(self.on_simulation_cancelled)

        self.worker.start()

    def on_simulation_done(self, result):
        self.running = False
        self.btn_run.setText("Run Draw Simulations")
        for btn in [self.pie_button1, self.pie_button2, self.pie_button3, self.pie_button4]:
            btn.setEnabled(True)

        self.last_results, _,_,_, all_history,_,stats_text = result
        num_sessions = self.sessions_input.value()
        pulls_per_session = self.pulls_input.value()

        self.stats_display.clear()
        self.stats_display.append(f"📊 Multi Draw Results: {num_sessions} sessions of {pulls_per_session} pulls")
        self.stats_display.append(stats_text)
        self.stats_display.append(funcs.shard_tracking(all_history,num_sessions))
        self.log.append(f"Multi draw complete: {num_sessions} sessions x {pulls_per_session} pulls")

    def on_simulation_error(self, error_msg):
        self.running = False
        self.btn_run.setText("Run Draw Simulations")
        for btn in [self.pie_button1, self.pie_button2, self.pie_button3, self.pie_button4]:
            btn.setEnabled(True)

        self.stats_display.append(f"❌ Error: {error_msg}")
        self.log.append(f"Simulation error: {error_msg}")

    def on_simulation_cancelled(self):
        self.running = False
        self.btn_run.setText("Run Draw Simulations")
        for btn in [self.pie_button1, self.pie_button2, self.pie_button3, self.pie_button4]:
            btn.setEnabled(True)

        self.stats_display.append("⚠️ Simulation cancelled by user.")
        self.log.append("Simulation cancelled.")

    def show_pie_chart(self, chart_number):
        if not self.last_results:
            self.log.append("Run a multi draw first to generate data!")
            return
        funcs.draw_heros_pie_chart(self.last_results, chart_number)
class TabShardProbBanner(QWidget):#OK
    def __init__(self, params_panel, log_widget):
        super().__init__()
        self.params = params_panel
        self.log = log_widget
        self.running = False

        # --- Result storage ---
        self.pull_results = []
        self.all_arrays = []
        self.all_titles = []
        self.starting_shards_list = []
        self.results = []
        self.pull_index = 0

        # --- Inputs ---
        self.pulls_input = QLineEdit("100,200")
        pulls_label = QLabel("Pull Lengths (comma-separated):")
        input_layout = QHBoxLayout()
        input_layout.addWidget(pulls_label)
        input_layout.addWidget(self.pulls_input)

        self.current_shards_input = QSpinBox()
        self.current_shards_input.setRange(0, 1040)
        self.current_shards_input.setValue(0)
        shards_label = QLabel("Current Shards:")
        shards_layout = QHBoxLayout()
        shards_layout.addWidget(shards_label)
        shards_layout.addWidget(self.current_shards_input)

        self.repeats_input = QSpinBox()
        self.repeats_input.setRange(1, 100000)
        self.repeats_input.setValue(5000)
        repeats_label = QLabel("Simulations per Pull Length:")
        repeats_layout = QHBoxLayout()
        repeats_layout.addWidget(repeats_label)
        repeats_layout.addWidget(self.repeats_input)

        # --- Run button ---
        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.clicked.connect(self.run_simulation)

        # --- Navigation buttons ---
        self.btn_left = QPushButton("←")
        self.btn_right = QPushButton("→")
        self.btn_left.clicked.connect(self.prev_result)
        self.btn_right.clicked.connect(self.next_result)
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_left)
        nav_layout.addWidget(self.btn_right)

        # --- Stats display ---
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)

        # --- Chart buttons ---
        self.btn_pie1 = QPushButton("Mythic")
        self.btn_pie2 = QPushButton("Legendary")
        self.btn_pie3 = QPushButton("Epic")
        self.btn_pie4 = QPushButton("Overall")
        self.btn_bar = QPushButton("Bar Chart")
        self.btn_pie1.clicked.connect(lambda: self.show_chart(1))
        self.btn_pie2.clicked.connect(lambda: self.show_chart(2))
        self.btn_pie3.clicked.connect(lambda: self.show_chart(3))
        self.btn_pie4.clicked.connect(lambda: self.show_chart(4))
        self.btn_bar.clicked.connect(lambda: self.show_chart(5))
        chart_buttons_layout = QHBoxLayout()
        for btn in [self.btn_pie1, self.btn_pie2, self.btn_pie3, self.btn_pie4, self.btn_bar]:
            chart_buttons_layout.addWidget(btn)

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(shards_layout)
        layout.addLayout(repeats_layout)
        layout.addWidget(self.btn_run)
        layout.addLayout(nav_layout)
        layout.addWidget(self.stats_display)
        layout.addLayout(chart_buttons_layout)
        self.setLayout(layout)

    def run_simulation(self):
        pulls_text = self.pulls_input.text()
        pulls_list = [int(x.strip()) for x in pulls_text.split(",") if x.strip().isdigit()]
        current_shards = self.current_shards_input.value()
        repeats = self.repeats_input.value()
        # Run simulation
        self.pull_results, self.all_arrays, self.all_titles, self.starting_shards_list, self.results, _ = funcs.shard_probability_multiple_pull_lengths(
            pulls_list=pulls_list,
            simulations=repeats,
            current_shards=current_shards
        )
        self.pull_index = 0
        self.show_current_result()

    def show_current_result(self):
        if not self.pull_results:
            return
        self.stats_display.clear()
        self.stats_display.append(self.pull_results[self.pull_index])

    def prev_result(self):
        if self.pull_index > 0:
            self.pull_index -= 1
            self.show_current_result()

    def next_result(self):
        if self.pull_index < len(self.pull_results) - 1:
            self.pull_index += 1
            self.show_current_result()

    def show_chart(self, chart_number):
        """Display chart based on the current pull_index and chosen chart type"""
        if not self.all_arrays or not self.results:
            self.log.append("Run a simulation first!")
            return

        current_array = self.all_arrays[self.pull_index]
        current_title = self.all_titles[self.pull_index]
        current_starting_shards = self.starting_shards_list[self.pull_index]
        current_results =self.results[self.pull_index]

        if chart_number == 5:  # Bar chart
            funcs.plot_multiple_shard_distributions_banner(
                shard_arrays=[current_array],
                titles=[current_title],
                starting_shards_list=[current_starting_shards]
            )
        else:  # Pie chart 1-4
            funcs.draw_heros_pie_chart(
                current_results,
                chart_number  # pass 1-4 for specific pie chart
            )
class TabShardProbMythic(QWidget):#OK
    def __init__(self, params_panel, log_widget):
        super().__init__()
        self.params = params_panel
        self.log = log_widget
        self.running = False

        # --- Result storage ---
        self.pull_results = []  # printed text per pull length
        self.all_arrays = []    # arrays for plotting
        self.pull_limits = []   # list of pull lengths
        self.pull_index = 0

        # --- Inputs ---
        self.pulls_input = QLineEdit("100,200")
        pulls_label = QLabel("Pull Lengths (comma-separated):")
        input_layout = QHBoxLayout()
        input_layout.addWidget(pulls_label)
        input_layout.addWidget(self.pulls_input)

        self.repeats_input = QSpinBox()
        self.repeats_input.setRange(1, 100000)  # set sensible limits
        self.repeats_input.setValue(5000)
        repeats_label = QLabel("Simulations per Pull Length:")
        repeats_layout = QHBoxLayout()
        repeats_layout.addWidget(repeats_label)
        repeats_layout.addWidget(self.repeats_input)

        # --- Run button ---
        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.clicked.connect(self.run_simulation)
        

        # --- Navigation buttons ---
        self.btn_left = QPushButton("←")
        self.btn_right = QPushButton("→")
        self.btn_left.clicked.connect(self.prev_result)
        self.btn_right.clicked.connect(self.next_result)
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_left)
        nav_layout.addWidget(self.btn_right)

        # --- Stats display ---
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)

        # --- Chart button ---
        self.btn_both = QPushButton("Both Charts")
        self.btn_both.clicked.connect(lambda: self.show_chart(chart_type=3))
        
        self.btn_nonbanner = QPushButton("Non-Banner Chart")
        self.btn_nonbanner.clicked.connect(lambda: self.show_chart(chart_type=1))

        self.btn_banner = QPushButton("Banner Chart")
        self.btn_banner.clicked.connect(lambda: self.show_chart(chart_type=2))

        # --- Main layout ---
        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        #layout.addLayout(shards_layout)
        layout.addLayout(repeats_layout)
        layout.addWidget(self.btn_run)
        layout.addLayout(nav_layout)
        layout.addWidget(self.stats_display)
        layout.addWidget(self.btn_nonbanner)
        layout.addWidget(self.btn_banner)
        layout.addWidget(self.btn_both)
        self.setLayout(layout)

    def run_simulation(self):
        pulls_text = self.pulls_input.text()
        self.pull_limits = [int(x.strip()) for x in pulls_text.split(",") if x.strip().isdigit()]
        repeats = self.repeats_input.value() 
        # Run simulation for all pull lengths

        self.pull_results, self.all_arrays,self.pull_limits = funcs.shard_probability_multiple_Mythic_pulls(
            pulls_list=self.pull_limits,
            simulations=repeats
        )
        self.pull_index = 0
        self.show_current_result()

    def show_current_result(self):
        if not self.pull_results:
            return
        self.stats_display.clear()
        self.stats_display.append(self.pull_results[self.pull_index])

    def prev_result(self):
        if self.pull_index > 0:
            self.pull_index -= 1
            self.show_current_result()

    def next_result(self):
        if self.pull_index < len(self.pull_results) - 1:
            self.pull_index += 1
            self.show_current_result()

    def show_chart(self, chart_type=3):
        if not self.all_arrays:
            self.log.append("Run a simulation first!")
            return

        current_array = self.all_arrays[self.pull_index]
        current_pull_limit = self.pull_limits[self.pull_index]
        funcs.plot_multiple_Mythic_distributions(
            arrays=[current_array],
            pull_limits=[current_pull_limit],
            chart_type=chart_type
        )
class TabShardSims(QWidget):#OK
    def __init__(self, params_panel: ParametersPanel, log_widget: QTextEdit):
        super().__init__()
        self.params = params_panel
        self.log = log_widget

        self.simulations = QSpinBox()
        self.simulations.setRange(1, 500000)
        self.simulations.setValue(10000)

        self.targets_input = QLineEdit("80,120,200")
        self.success_input = QLineEdit("")  # optional: thresholds like "100,200,300"

        self.btn_run = QPushButton("Run Shard Goal Simulations")
        self.btn_run.clicked.connect(self.run_sims)

        # Stats display for simulation results
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)

        # Combo + button for target-specific charts
        self.target_combo = QComboBox()
        self.btn_show = QPushButton("Show Distribution")
        self.btn_show.clicked.connect(self.show_distribution)

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Select Target:"))
        combo_layout.addWidget(self.target_combo)
        combo_layout.addWidget(self.btn_show)

        form = QFormLayout()
        form.addRow("Simulations:", self.simulations)
        form.addRow("Shard targets (comma):", self.targets_input)
        form.addRow("Success thresholds (pulls, comma, optional):", self.success_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.btn_run)
        layout.addWidget(self.stats_display)
        layout.addLayout(combo_layout)
        self.setLayout(layout)

        # Data placeholders
        self.worker = None
        self.sim_values = None
        self.sim_targets = None
        self.success_thresholds = []

    def parse_int_list(self, text):
        out = []
        for part in text.split(","):
            part = part.strip()
            if part.isdigit():
                val = int(part)
                if val > 0:
                    out.append(val)
        return out

    def run_sims(self):
        sims = self.simulations.value()
        targets = self.parse_int_list(self.targets_input.text())
        if not targets:
            QMessageBox.warning(self, "Input", "Please enter at least one valid shard target.")
            return

        self.success_thresholds = self.parse_int_list(self.success_input.text())

        self.log.append(f"Running shard simulations for {targets}...")
        self.worker = Worker(
            funcs.run_shard_simulations,
            simulations=sims,
            shard_targets=targets,
            output=False,
        )
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_done(self, result):
        """
        result is a tuple: (text_output, values, shard_targets)
        """
        text_output, values, shard_targets = result
        self.log.append("Simulation complete!")
        self.stats_display.clear()
        self.stats_display.append(text_output)
        lines = funcs.prob_tbl_txt(values,self.success_thresholds)
        self.stats_display.append("\n".join(lines))

        # Store results for later use
        self.sim_values = values
        self.sim_targets = shard_targets

        # Populate combo with targets
        self.target_combo.clear()
        for t in shard_targets:
            self.target_combo.addItem(str(t))

    def show_distribution(self):
        """Run show_pulls_for_shards for the selected target."""
        if not self.sim_values or not self.sim_targets:
            QMessageBox.warning(self, "No Data", "Please run simulations first.")
            return

        idx = self.target_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "No Target", "Please select a shard target.")
            return

        target = self.sim_targets[idx]
        # Call your existing plotting function
        funcs.show_pulls_for_shards([self.sim_values[idx]])

    @pyqtSlot(str)
    def on_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.log.append(f"Error: {msg}")

class TabLoadResults(QWidget):
    def __init__(self, log_widget: QTextEdit):
        super().__init__()
        self.log = log_widget
        self.canvas = MatplotlibCanvas()

        self.btn_load = QPushButton("Load Draws From File...")
        self.btn_load.clicked.connect(self.load_file)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_load, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Draws File", "", "Text Files (*.txt);;All Files (*.*)")
        if not path:
            return
        try:
            results, history, totals, meta = funcs.set_draws(path)
            self.log.append(f"Loaded {len(history)} draws from {path}")
            # Optionally draw a pie/chart from results:
            # draw_heros_pie_chart(results, "1")
            # For demo, plot total per key:
            xs = list(range(len(results)))
            ys = list(results.values())
            self.canvas.clear()
            self.canvas.plot_scatter(xs, ys, label="Counts (placeholder)")
            self.canvas.set_labels(title="Loaded Results", xlabel="Index", ylabel="Count")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.log.append(f"Error loading file: {e}")

# ---------- Main Window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DC Dark Legion Bleed @ Thecarlosmff")
        self.resize(1100, 720)

        # Shared log and parameters panel
        self.log = LogPanel()
        self.params_panel = ParametersPanel()
        
        # Tabs corresponding to your CLI menu options
        tabs = QTabWidget()
        tabs.addTab(TabDraw(self.log), "Draw") # 1 & 2
        tabs.addTab(TabDrawSimulations(self.params_panel, self.log), "Simulate Draws") # 3 & 4
        tabs.addTab(TabShardSims(self.params_panel, self.log), "Shards Goal") #7
        tabs.addTab(TabShardProbBanner(self.params_panel, self.log), "Probability (Banner)") # 5
        tabs.addTab(TabShardProbMythic(self.params_panel, self.log), "Probability (Mythics)") # 6
        #tabs.addTab(TabLoadResults(self.log), "Load Draws") #TODO NOT WORKING PROPERLY draw_heros_pie_chart

        # Layout
        central = QWidget()
        layout = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Session Parameters"))
        left.addWidget(self.params_panel)
        left.addWidget(QLabel("Log"))
        left.addWidget(self.log)
        left.setStretch(2, 1)

        layout.addLayout(left, stretch=2)
        layout.addWidget(tabs, stretch=7)
        central.setLayout(layout)
        self.setCentralWidget(central)


def main():
    app = QApplication(sys.argv)
    funcs.set_pull_list_to_default()
    funcs.set_banner(funcs.banner_Mythic_champions[0])
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
