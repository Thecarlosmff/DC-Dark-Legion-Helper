

import os
import sys
from PyQt6.QtGui import QColor, QFont, QIcon
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import funcs
from collections import Counter

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QLineEdit, QCheckBox,
    QComboBox, QTabWidget, QFileDialog, QTextEdit, QFormLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,QListWidget,QListWidgetItem,
    QDialog, QGroupBox, QSpacerItem, QSizePolicy,QProgressBar
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
    done = pyqtSignal(object)
    error = pyqtSignal(str)
    cancelled = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self._running = True

        # Only set stop_flag if not already provided
        if "stop_flag" not in self.kwargs:
            self.kwargs["stop_flag"] = self.stop_flag

        # Progress callback should emit signal
        if "progress_callback" not in self.kwargs:
            self.kwargs["progress_callback"] = self.progress.emit

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

        # --- Text ---
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
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)   # 0,0 = infinite spinner
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

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
        self.progress_bar.setVisible(True)
        self.running = True

        # Create worker
        self.worker = Worker(
            funcs.simulate_multiple_sessions,
            num_sessions,
            pulls_per_session,
            show_output=True,
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.progress_bar.setRange(0, 100)   # switch to percentage
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.worker.done.connect(self.on_simulation_done)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.cancelled.connect(self.on_simulation_cancelled)

        self.worker.start()

    def on_simulation_done(self, result):
        self.progress_bar.setVisible(False)
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
        self.progress_bar.setVisible(False)
        self.running = False
        self.btn_run.setText("Run Draw Simulations")
        for btn in [self.pie_button1, self.pie_button2, self.pie_button3, self.pie_button4]:
            btn.setEnabled(True)

        self.stats_display.append(f"❌ Error: {error_msg}")
        self.log.append(f"Simulation error: {error_msg}")

    def on_simulation_cancelled(self):
        self.progress_bar.setVisible(False)
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
class TabProbBanner(QWidget):#OK
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
        self.btn_run = QPushButton("Run")
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
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)   # 0,0 = infinite spinner
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    def set_buttons_enabled(self, enabled: bool):
        # Pie / Bar buttons
        for btn in [self.btn_pie1, self.btn_pie2, self.btn_pie3, self.btn_pie4, self.btn_bar]:
            btn.setEnabled(enabled)
        # Navigation buttons
        for btn in [self.btn_left, self.btn_right]:
            btn.setEnabled(enabled)
    def run_simulation(self):
        if self.running:
            if hasattr(self, 'worker'):
                self.worker.stop()
                self.log.append("Simulation cancellation requested...")
            return  # don't start a new run

        pulls_text = self.pulls_input.text()
        pulls_list = [int(x.strip()) for x in pulls_text.split(",") if x.strip().isdigit()]
        current_shards = self.current_shards_input.value()
        repeats = self.repeats_input.value()

        self.stats_display.clear()
        self.stats_display.append("Running shard probability simulation...")
        self.log.append(f"Running shard probability for pulls {pulls_list} with {repeats} repeats")

        self.set_buttons_enabled(False)
        self.btn_run.setText("Cancel Simulation")
        self.progress_bar.setVisible(True)
        self.running = True

        self.worker = Worker(
            funcs.prob_banner_pull,
            pulls_list=pulls_list,
            simulations=repeats,
            current_shards=current_shards
        )
        self.worker.progress.connect(lambda val: self.progress_bar.setValue(val) if hasattr(self, 'progress_bar') else None)
        self.worker.done.connect(self.on_simulation_done)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.cancelled.connect(self.on_simulation_cancelled)

        self.worker.start()

    def on_simulation_done(self, result):
        self.pull_results, self.all_arrays, self.all_titles, self.starting_shards_list, self.results, _ = result
        self.pull_index = 0
        self.show_current_result()

        self.stats_display.append("✅ Simulation complete!")
        self.btn_run.setText("Run")
        self.set_buttons_enabled(True)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)

    def on_simulation_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.running = False
        self.btn_run.setText("Run")
        self.set_buttons_enabled(True)

        self.stats_display.append(f"❌ Error: {error_msg}")
        self.log.append(f"Simulation error: {error_msg}")

    def on_simulation_cancelled(self):
        self.progress_bar.setVisible(False)
        self.running = False
        self.btn_run.setText("Run")
        self.set_buttons_enabled(True)

        self.stats_display.append("⚠️ Simulation cancelled by user.")
        self.log.append("Simulation cancelled.")
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
                chart_number
            )
class TabProbMythic(QWidget):#OK
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
        self.btn_both = QPushButton("Extra Shards")
        self.btn_both.clicked.connect(lambda: self.show_chart(chart_type=3))
        
        self.btn_nonbanner = QPushButton("Mythic")
        self.btn_nonbanner.clicked.connect(lambda: self.show_chart(chart_type=1))

        self.btn_banner = QPushButton("Banner")
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
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)   # 0,0 = infinite spinner
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    def run_simulation(self):
        # Cancel running simulation
        if self.running:
            if hasattr(self, 'worker'):
                self.worker.stop()
                self.log.append("Simulation cancellation requested...")
            return

        # --- Gather inputs ---
        pulls_text = self.pulls_input.text()
        self.pull_limits = [int(x.strip()) for x in pulls_text.split(",") if x.strip().isdigit()]
        repeats = self.repeats_input.value() 

        # Clear previous results
        self.stats_display.clear()
        self.stats_display.append("Running Mythic probability simulation...")
        self.log.append(f"Running Mythic probability for pulls {self.pull_limits} with {repeats} repeats")

        # --- Disable UI while running ---
        self.set_buttons_enabled(False)  # helper method like before
        self.btn_run.setText("Cancel Simulation")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.running = True

        # --- Worker thread ---
        self.worker = Worker(
            funcs.prob_mythic_shards,
            pulls_list=self.pull_limits,
            simulations=repeats
        )
        self.worker.progress.connect(lambda val: self.progress_bar.setValue(val))
        self.worker.done.connect(self.on_simulation_done)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.cancelled.connect(self.on_simulation_cancelled)

        self.worker.start()

    def on_simulation_done(self, result):
        self.pull_results, self.all_arrays, self.pull_limits = result
        self.pull_index = 0
        self.show_current_result()
        self.stats_display.append("✅ Simulation complete!")
        self.running = False
        self.btn_run.setText("Run Simulation")
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

    def on_simulation_error(self, error_msg):
        self.stats_display.append(f"❌ Error: {error_msg}")
        self.log.append(f"Simulation error: {error_msg}")
        self.running = False
        self.btn_run.setText("Run Simulation")
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

    def on_simulation_cancelled(self):
        self.stats_display.append("⚠️ Simulation cancelled by user.")
        self.log.append("Simulation cancelled.")
        self.running = False
        self.btn_run.setText("Run Simulation")
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)

    # --- Helper to enable/disable buttons ---
    def set_buttons_enabled(self, enabled: bool):
        for btn in [self.btn_nonbanner, self.btn_banner, self.btn_both, self.btn_left, self.btn_right]:
            btn.setEnabled(enabled)


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

    def show_chart(self, chart_type=1):
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
class TabShardSims(QWidget):
    def __init__(self, params_panel: ParametersPanel, log_widget: QTextEdit):
        super().__init__()
        self.params = params_panel
        self.log = log_widget

        self.simulations = QSpinBox()
        self.simulations.setRange(1, 500000)
        self.simulations.setValue(10000)

        self.targets_input = QLineEdit("80,120,200")
        self.success_input = QLineEdit("")  # optional thresholds

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

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # Data placeholders
        self.worker = None
        self.sim_values = None
        self.sim_targets = None
        self.success_thresholds = []
        self.running = False

    def parse_int_list(self, text):
        return [int(x.strip()) for x in text.split(",") if x.strip().isdigit() and int(x.strip()) > 0]

    def run_sims(self):
        if self.running:
            # Cancel running simulation
            if self.worker:
                self.worker.stop()
                self.log.append("Simulation cancellation requested...")
            return

        sims = self.simulations.value()
        targets = self.parse_int_list(self.targets_input.text())
        if not targets:
            QMessageBox.warning(self, "Input", "Please enter at least one valid shard target.")
            return

        self.success_thresholds = self.parse_int_list(self.success_input.text())

        self.stats_display.clear()
        self.stats_display.append(f"Running shard simulations for {targets}...")

        self.log.append(f"Running shard simulations for {targets} with {sims} repeats")
        self.btn_run.setText("Cancel Simulation")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Start worker thread
        self.running = True
        self.worker = Worker(
        funcs.run_shard_simulations,
            simulations=sims,
            shard_targets=targets
            )
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.start()

    def on_done(self, result):
        self.running = False
        self.btn_run.setText("Run Shard Goal Simulations")
        self.progress_bar.setVisible(False)

        text_output, values, shard_targets = result
        self.log.append("Simulation complete!")
        self.stats_display.clear()
        self.stats_display.append(text_output)

        # Add success table
        lines = funcs.prob_tbl_txt(values, self.success_thresholds)
        self.stats_display.append("\n".join(lines))

        # Store results
        self.sim_values = values
        self.sim_targets = shard_targets

        # Populate combo
        self.target_combo.clear()
        for t in shard_targets:
            self.target_combo.addItem(str(t))

    def on_cancelled(self):
        self.running = False
        self.btn_run.setText("Run Shard Goal Simulations")
        self.progress_bar.setVisible(False)
        self.stats_display.append("⚠️ Simulation cancelled by user.")
        self.log.append("Simulation cancelled.")

    def show_distribution(self):
        if not self.sim_values or not self.sim_targets:
            QMessageBox.warning(self, "No Data", "Please run simulations first.")
            return

        idx = self.target_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "No Target", "Please select a shard target.")
            return

        target = self.sim_targets[idx]
        funcs.show_pulls_for_shards([self.sim_values[idx]])

    @pyqtSlot(str)
    def on_error(self, msg):
        self.running = False
        self.btn_run.setText("Run Shard Goal Simulations")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", msg)
        self.log.append(f"Error: {msg}")
class TabLoadResults(QWidget):
    def __init__(self, log_widget: QTextEdit):
        super().__init__()
        self.log = log_widget

        # UI Elements
        self.btn_load = QPushButton("Load Draws From File...")
        self.btn_load.clicked.connect(self.load_file)

        self.btn_chart = QPushButton("Show Rarity Chart")
        self.btn_chart.setEnabled(False)  # disabled until data is loaded
        self.btn_chart.clicked.connect(self.show_chart)

        # Stats displays
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.details_display = QTextEdit()
        self.details_display.setReadOnly(True)

        # Table setup
        self.table = QTableWidget()
        self.table.setRowCount(6)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Epic Champ.", "Epic Legacy",
            "Leg. Champ.", "Leg. Legacy",
            "Mythic Champ.", "Mythic Legacy", "Mythic+ Champ."
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)


       # Layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.btn_load)
        left_layout.addWidget(self.btn_chart)
        left_layout.addWidget(self.stats_display)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.details_display)

        top_layout = QHBoxLayout()
        top_layout.addLayout(left_layout, 1)
        top_layout.addLayout(right_layout, 1)
        
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.table)



        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout,2)
        main_layout.addLayout(bottom_layout,1)  # Table goes below details display

        self.setLayout(main_layout)
        # placeholders
        self.results = None
        self.history = None
        self.meta = None

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Draws File", "", "Text Files (*.txt);;All Files (*.*)"
        )
        if not path:
            return

        try:
            results, history, totals, meta = funcs.set_draws(path)

            # Store so other methods can use
            self.results = results
            self.history = history
            self.meta = meta
            self.totals = totals

            self.log.append(f"Loaded {len(history)} draws from {path}")

            self.left_panel()
            self.right_panel()
            
            # enable chart button now that we have data
            self.btn_chart.setEnabled(True)
            self.build_tbl()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.log.append(f"Error loading file: {e}")
    def right_panel(self):
        # --- Right panel: Counts per item ---
            groups = {
                "Banner": [],
                "Mythic": [],
                "Legendary": [],
                "Epic": [],
            }
            mythic_pool = self.meta.get("Pulls Count Mythic", [])
            legendary_pool = self.meta.get("Pulls Count Legendary", [])
            epic_pool = self.meta.get("Pulls Count Epic", [])

            for champ, count in self.results.items():
                if champ in epic_pool:
                    groups["Epic"].append((champ, count))
                elif champ in legendary_pool:
                    groups["Legendary"].append((champ, count))
                elif champ in mythic_pool:
                    groups["Mythic"].append((champ, count))
                else:
                    groups["Banner"].append((champ, count))

            colors = {
                "Banner": "darkred",
                "Mythic": "red",
                "Legendary": "#FFBF00",
                "Epic": "purple",
            }

            html_lines = []
            for group_name, items in groups.items():
                if not items:
                    continue
                html_lines.append(f"<b>{group_name}</b><br>")
                for champ, count in sorted(items, key=lambda x: -x[1]):
                    color = colors.get(group_name, "black")
                    html_lines.append(f"<span style='color:{color}'>{champ}</span>: {count}<br>")
                html_lines.append("<br>")

            self.details_display.setHtml("\n".join(html_lines))

    def left_panel(self):
        avg_banner = self.meta.get("Average pulls per banner")
        avg_mythic = self.meta.get("Average pulls per mythic")

        # --- Left panel: General stats ---
        general_lines = []
        general_lines.append("=== Loaded Draw Statistics ===\n")
        general_lines.append(f"Total draws: {len(self.history)}")
        general_lines.append(f"Mythic pity counter: {self.meta.get('Mythic pity reset at', 'Unknown')}")
        general_lines.append(f"Legendary pity counter: {self.meta.get('Legendary pity reset at', 'Unknown')}")
        general_lines.append(f"Forced Mythics: {self.meta.get('Forced Mythics', 0)}")
        general_lines.append(f"Forced Banner Mythics: {self.meta.get('Forced Banner', 0)}")
        general_lines.append(f"Normal Banner pulls: {self.meta.get('Normal Banner', 0)}")
        general_lines.append(f"Forced Legendary: {self.meta.get('Forced Legendary', 0)}")
        general_lines.append(
            f"Average pulls per banner: {avg_banner:.2f}" if isinstance(avg_banner, (int, float)) 
            else "Average pulls per banner: N/A"
        )
        general_lines.append(
            f"Average pulls per mythic: {avg_mythic:.2f}" if isinstance(avg_mythic, (int, float)) 
            else "Average pulls per mythic: N/A"
        )

        # Quality of Life
        total = len(self.history)
        if total > 0:
            mythic_count = self.totals["Mythic"]
            legendary_count = self.totals["Legendary"]
            epic_count = self.totals["Epic"]

            general_lines.append("\n=== Quality of Life Stats ===\n")
            general_lines.append(f"Mythic: {mythic_count / total * 100:.2f}%")
            general_lines.append(f"Legendary: {legendary_count / total * 100:.2f}%")
            general_lines.append(f"Epic: {epic_count / total * 100:.2f}%")

            # Longest streaks
            longest_no_mythic = self.longest_streak(self.history, "Mythic")
            longest_no_banner = self.longest_streak(self.history, "Banner")
            general_lines.append(f"Longest streak without a Mythic: {longest_no_mythic}")
            general_lines.append(f"Longest streak without a Banner: {longest_no_banner}")

        self.stats_display.setPlainText("\n".join(general_lines))


    def build_tbl(self):
        epic_piece_count = self.meta.get('Epic Piece Count', 0)
        epic_champ_count = self.meta.get('Epic Champion Count', 0)
        epic_total = epic_piece_count + epic_champ_count

        legendaries_piece_count = self.meta.get('Legendary Piece Count', 0)
        legendaries_champ_count = self.meta.get('Legendary Champion Count', 0)
        legendary_total = legendaries_piece_count + legendaries_champ_count

        mythics_piece_count = self.meta.get('Mythic Piece Count', 0)
        mythics_champ_count = self.meta.get('Mythic Champion Count', 0)
        banner_only_count = self.meta.get('Banner Champion Count', 0)

        mythic_total = mythics_piece_count + mythics_champ_count + banner_only_count
        total = epic_total + legendary_total + mythic_total

        # Define colors per rarity
        colors = {
            "Epic": "purple",
            "Legendary": "#FFBF00",
            "Orange": "#D18726",
            "DarkerRed": "#850A0A",
            "Red1" :"#B94528",
            "Red2":"#5A1717",
            "Mythic": "red",
            "Banner": "darkred"
        }

        def set_cell(row, col, value, rarity=None):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set white bold text
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QColor("white"))

            # Set background color based on rarity
            if rarity and rarity in colors:
                item.setBackground(QColor(colors[rarity]))

            self.table.setItem(row, col, item)

        # --- Apply merged cells (spans) ---
        self.table.setSpan(1, 0, 1, 2)
        self.table.setSpan(1, 2, 1, 2)
        self.table.setSpan(1, 6, 2, 1)
        self.table.setSpan(2, 0, 2, 4)
        self.table.setSpan(3, 4, 1, 3)
        self.table.setSpan(4, 0, 1, 4)
        self.table.setSpan(5, 0, 1, 4)
        self.table.setSpan(4, 5, 2, 2)

        # --- Row 1 ---
        set_cell(0, 0, f"{(epic_champ_count / total)*100:.2f}%", "Epic")
        set_cell(0, 1, f"{(epic_piece_count / total)*100:.2f}%", "Epic")
        set_cell(0, 2, f"{(legendaries_champ_count / total)*100:.2f}%", "Legendary")
        set_cell(0, 3, f"{(legendaries_piece_count / total)*100:.2f}%", "Legendary")
        set_cell(0, 4, f"{(mythics_champ_count / total)*100:.2f}%", "Mythic")
        set_cell(0, 5, f"{(mythics_piece_count / total)*100:.2f}%", "Mythic")
        set_cell(0, 6, f"{(banner_only_count / total)*100:.2f}%", "Banner")

        # --- Row 2 ---
        set_cell(1, 0, f"{((epic_champ_count+epic_piece_count)/total)*100:.2f}%", "Epic")
        set_cell(1, 2, f"{((legendaries_champ_count+legendaries_piece_count)/total)*100:.2f}%", "Legendary")
        set_cell(1, 4, f"{(mythics_champ_count/mythic_total)*100:.2f}%", "Mythic")
        set_cell(1, 5, f"{(mythics_piece_count/mythic_total)*100:.2f}%", "Mythic")
        set_cell(1, 6, f"{(banner_only_count/mythic_total)*100:.2f}%", "Banner")

        # --- Row 3 ---
        set_cell(2, 0, f"{((epic_total+legendary_total)/total)*100:.2f}%","Orange")
        set_cell(2, 4, f"{(mythics_champ_count/(mythics_champ_count+mythics_piece_count))*100:.2f}%", "Red2")
        set_cell(2, 5, f"{(mythics_piece_count/(mythics_champ_count+mythics_piece_count))*100:.2f}%", "Red2")

        # --- Row 4 ---
        set_cell(3, 4, f"{(mythic_total/total)*100:.2f}%", "DarkerRed")

        # --- Row 5 ---
        set_cell(4, 0, "Average number of Pulls per Mythic:","Red1")
        set_cell(4, 4, f"{(len(self.history)/mythic_total):.2f}","Red1")

        # --- Row 6 ---
        set_cell(5, 0, "Average number of Pulls per Mythic+:","Red2")
        set_cell(5, 4, f"{(len(self.history)/banner_only_count):.2f}","Red2")


     
        

    def longest_streak(self, history, rarity_type):
            """Compute longest streak without pulling a given rarity."""
            streak = longest = 0
            for rarity, champ, _ in history:
                if rarity_type == "Banner":
                    # Banner = must be in meta["Banner Pulls"]
                    if champ in self.meta.get("Banner Pulls", []):
                        streak = 0
                    else:
                        streak += 1
                else:
                    if rarity == rarity_type:
                        streak = 0
                    else:
                        streak += 1
                longest = max(longest, streak)
            return longest

    def show_chart(self):
        """Show rarity distribution chart."""
        if not self.history:
            return
        funcs.draw_heros_pie_chart(self.results,"1",True)
        funcs.draw_heros_pie_chart(self.results,"4",True)

# ---------- Main Window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DC Dark Legion Bleed @ Thecarlosmff")
        self.resize(1200, 720)
        
        def resource_path(relative_path):
            """ Get absolute path to resource (works for dev and for PyInstaller) """
            if hasattr(sys, '_MEIPASS'):  # PyInstaller creates a temp folder
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)

        self.setWindowIcon(QIcon(resource_path("icon.png")))

        # Shared log and parameters panel
        self.log = LogPanel()
        self.params_panel = ParametersPanel()
        
        # Tabs corresponding to your CLI menu options
        tabs = QTabWidget()
        tabs.addTab(TabDraw(self.log), "Draw") # 1 & 2
        tabs.addTab(TabDrawSimulations(self.params_panel, self.log), "Simulate Draws") # 3 & 4
        tabs.addTab(TabShardSims(self.params_panel, self.log), "Shards Goal") #7
        tabs.addTab(TabProbBanner(self.params_panel, self.log), "Probability (Banner)") # 5
        tabs.addTab(TabProbMythic(self.params_panel, self.log), "Probability (Mythics)") # 6
        tabs.addTab(TabLoadResults(self.log), "Load Draws") #TODO NOT WORKING PROPERLY draw_heros_pie_chart

        # --- Left Column Layout ---
        left = QVBoxLayout()

        # Parameters section
        params_group = QGroupBox("Session Parameters")
        params_layout = QVBoxLayout()
        params_layout.addWidget(self.params_panel)
        params_group.setLayout(params_layout)

        # Log section
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log)

        # Add buttons under the log
        btn_row = QHBoxLayout()
        btn_clear = QPushButton("🗑 Clear Log")
        btn_clear.clicked.connect(lambda: self.log.clear()) 
        btn_row.addWidget(btn_clear)
        log_layout.addLayout(btn_row)

        log_group.setLayout(log_layout)

        # Add everything to left column
        left.addWidget(params_group)
        left.addWidget(log_group)

        # Add a stretchable spacer (pushes status to the bottom)
        left.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Apply to central layout
        layout = QHBoxLayout()
        central = QWidget()

        central.setLayout(layout)

        left.setStretch(2, 1)
        layout.addLayout(left, stretch=2)
        layout.addWidget(tabs, stretch=7)
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
