import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                            QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                            QMessageBox, QInputDialog, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QFont
from collections import deque

class Process:
    def __init__(self, pid="", arrival=0, service=0, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.service = service
        self.priority = priority  # Lower number = higher priority
        self.remaining = service
        self.finish = 0
        self.waiting = 0
        self.tat = 0
        self.ntat = 0
        self.completed = False

class SchedulingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Scheduling Simulator")
        self.setGeometry(100, 100, 1000, 800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        self.create_control_panel()
        self.create_process_table()
        self.create_gantt_chart()
        self.create_results_display()
        
        # Initialize process list
        self.processes = []
        
    def create_control_panel(self):
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        # Algorithm selection
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems([
            "First-Come, First-Served (FCFS)",
            "Round Robin (RR)",
            "Shortest Process Next (SPN)",
            "Shortest Remaining Time (SRT)",
            "Highest Response Ratio Next (HRRN)",
            "Priority Scheduling (Non-Preemptive)",
            "Priority Scheduling (Preemptive)",
            "Deadlock Detection"
        ])
        
        # Quantum input (only for RR)
        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 100)
        self.quantum_spin.setValue(4)
        self.quantum_spin.setEnabled(False)
        
        # Buttons
        self.add_process_btn = QPushButton("Add Process")
        self.clear_btn = QPushButton("Clear All")
        self.run_btn = QPushButton("Run Simulation")
        
        # Layout
        control_layout.addWidget(QLabel("Algorithm:"))
        control_layout.addWidget(self.algorithm_combo)
        control_layout.addWidget(QLabel("Quantum:"))
        control_layout.addWidget(self.quantum_spin)
        control_layout.addWidget(self.add_process_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.run_btn)
        
        control_panel.setLayout(control_layout)
        self.main_layout.addWidget(control_panel)
        
        # Connect signals
        self.algorithm_combo.currentTextChanged.connect(self.toggle_quantum_visibility)
        self.add_process_btn.clicked.connect(self.add_process)
        self.clear_btn.clicked.connect(self.clear_all)
        self.run_btn.clicked.connect(self.run_simulation)
    
    def toggle_quantum_visibility(self, text):
        self.quantum_spin.setEnabled(text == "Round Robin (RR)")
    
    def create_process_table(self):
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Arrival Time", "Service Time", "Priority"])
        self.process_table.setColumnWidth(0, 100)
        self.process_table.setColumnWidth(1, 100)
        self.process_table.setColumnWidth(2, 100)
        self.process_table.setColumnWidth(3, 100)
        
        self.main_layout.addWidget(QLabel("Process List:"))
        self.main_layout.addWidget(self.process_table)
        
        # Add some default processes
        self.add_process("P1", 0, 5, 3)
        self.add_process("P2", 1, 3, 1)
        self.add_process("P3", 2, 8, 2)
    
    def create_gantt_chart(self):
        self.gantt_view = QGraphicsView()
        self.gantt_scene = QGraphicsScene()
        self.gantt_view.setScene(self.gantt_scene)
        self.gantt_view.setMinimumHeight(150)
        
        self.main_layout.addWidget(QLabel("Gantt Chart:"))
        self.main_layout.addWidget(self.gantt_view)
    
    def create_results_display(self):
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["PID", "Finish", "TAT", "WT", "NTAT"])
        
        self.avg_results_label = QLabel()
        self.avg_results_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.main_layout.addWidget(QLabel("Results:"))
        self.main_layout.addWidget(self.results_table)
        self.main_layout.addWidget(self.avg_results_label)
    
    def add_process(self, pid=None, arrival=None, service=None, priority=None):
        row = self.process_table.rowCount()
        self.process_table.insertRow(row)
        
        if pid is None:
            pid = f"P{row+1}"
            arrival = 0
            service = 1
            priority = 0
        
        self.process_table.setItem(row, 0, QTableWidgetItem(pid))
        self.process_table.setItem(row, 1, QTableWidgetItem(str(arrival)))
        self.process_table.setItem(row, 2, QTableWidgetItem(str(service)))
        self.process_table.setItem(row, 3, QTableWidgetItem(str(priority)))
    
    def clear_all(self):
        self.process_table.setRowCount(0)
        self.gantt_scene.clear()
        self.results_table.setRowCount(0)
        self.avg_results_label.clear()
        self.processes = []
    
    def validate_inputs(self):
        for row in range(self.process_table.rowCount()):
            # Check PID
            pid_item = self.process_table.item(row, 0)
            if not pid_item or not pid_item.text():
                QMessageBox.warning(self, "Input Error", f"Missing PID in row {row+1}")
                return False
            
            # Check arrival time
            arrival_item = self.process_table.item(row, 1)
            if not arrival_item or not arrival_item.text().isdigit() or int(arrival_item.text()) < 0:
                QMessageBox.warning(self, "Input Error", 
                                  f"Invalid arrival time in row {row+1}. Must be non-negative integer.")
                return False
            
            # Check service time
            service_item = self.process_table.item(row, 2)
            if not service_item or not service_item.text().isdigit() or int(service_item.text()) <= 0:
                QMessageBox.warning(self, "Input Error", 
                                  f"Invalid service time in row {row+1}. Must be positive integer.")
                return False
            
            # Check priority
            priority_item = self.process_table.item(row, 3)
            if not priority_item or not priority_item.text().isdigit():
                QMessageBox.warning(self, "Input Error", 
                                  f"Invalid priority in row {row+1}. Must be integer.")
                return False
        
        return True
    
    def collect_process_data(self):
        self.processes = []
        for row in range(self.process_table.rowCount()):
            pid = self.process_table.item(row, 0).text()
            arrival = int(self.process_table.item(row, 1).text())
            service = int(self.process_table.item(row, 2).text())
            priority = int(self.process_table.item(row, 3).text())
            self.processes.append(Process(pid, arrival, service, priority))
        
        return self.processes
    
    def run_simulation(self):
        if not self.validate_inputs():
            return
        
        self.collect_process_data()
        
        algorithm = self.algorithm_combo.currentText()
        
        if algorithm == "Deadlock Detection":
            self.run_deadlock_detection()
            return
        
        # Sort processes by arrival time
        self.processes.sort(key=lambda p: p.arrival)
        
        # Reset process states
        for p in self.processes:
            p.remaining = p.service
            p.completed = False
            p.finish = 0
        
        # Run selected algorithm
        if algorithm == "First-Come, First-Served (FCFS)":
            gantt = self.run_fcfs()
        elif algorithm == "Round Robin (RR)":
            quantum = self.quantum_spin.value()
            gantt = self.run_rr(quantum)
        elif algorithm == "Shortest Process Next (SPN)":
            gantt = self.run_spn()
        elif algorithm == "Shortest Remaining Time (SRT)":
            gantt = self.run_srt()
        elif algorithm == "Highest Response Ratio Next (HRRN)":
            gantt = self.run_hrrn()
        elif algorithm == "Priority Scheduling (Non-Preemptive)":
            gantt = self.run_priority_nonpreemptive()
        elif algorithm == "Priority Scheduling (Preemptive)":
            gantt = self.run_priority_preemptive()
        
        self.display_gantt_chart(gantt)
        self.display_results()
    
    def run_fcfs(self):
        gantt = []
        time = 0
        
        for p in self.processes:
            # Handle idle time
            while time < p.arrival:
                gantt.append(None)
                time += 1
            
            # Execute process
            for _ in range(p.service):
                gantt.append(p.pid)
                time += 1
            
            p.finish = time
            p.completed = True
        
        return gantt
    
    def run_rr(self, quantum):
        gantt = []
        time = 0
        ready_queue = deque()
        remaining_processes = [p for p in self.processes]
        
        while remaining_processes or ready_queue:
            # Add arriving processes to ready queue
            while remaining_processes and remaining_processes[0].arrival <= time:
                ready_queue.append(remaining_processes.pop(0))
            
            if ready_queue:
                current = ready_queue.popleft()
                exec_time = min(quantum, current.remaining)
                
                for _ in range(exec_time):
                    gantt.append(current.pid)
                    time += 1
                
                current.remaining -= exec_time
                
                # Add arriving processes during execution
                while remaining_processes and remaining_processes[0].arrival <= time:
                    ready_queue.append(remaining_processes.pop(0))
                
                if current.remaining > 0:
                    ready_queue.append(current)
                else:
                    current.finish = time
                    current.completed = True
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def run_spn(self):
        gantt = []
        time = 0
        remaining_processes = [p for p in self.processes]
        
        while remaining_processes:
            # Get ready processes
            ready = [p for p in remaining_processes if p.arrival <= time]
            
            if ready:
                # Find process with shortest service time
                ready.sort(key=lambda p: p.service)
                current = ready[0]
                
                # Execute process
                for _ in range(current.service):
                    gantt.append(current.pid)
                    time += 1
                
                current.finish = time
                current.completed = True
                remaining_processes.remove(current)
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def run_srt(self):
        gantt = []
        time = 0
        remaining_processes = [p for p in self.processes]
        
        while any(not p.completed for p in self.processes):
            # Get ready, uncompleted processes
            ready = [p for p in remaining_processes if p.arrival <= time and not p.completed]
            
            if ready:
                # Find process with shortest remaining time
                ready.sort(key=lambda p: p.remaining)
                current = ready[0]
                
                # Execute for 1 time unit
                gantt.append(current.pid)
                time += 1
                current.remaining -= 1
                
                if current.remaining == 0:
                    current.finish = time
                    current.completed = True
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def run_hrrn(self):
        gantt = []
        time = 0
        remaining_processes = [p for p in self.processes]
        
        while remaining_processes:
            # Get ready processes
            ready = [p for p in remaining_processes if p.arrival <= time]
            
            if ready:
                # Calculate response ratio for each process
                for p in ready:
                    waiting_time = time - p.arrival
                    p.response_ratio = (waiting_time + p.service) / p.service
                
                # Find process with highest response ratio
                ready.sort(key=lambda p: p.response_ratio, reverse=True)
                current = ready[0]
                
                # Execute process to completion (non-preemptive)
                for _ in range(current.service):
                    gantt.append(current.pid)
                    time += 1
                
                current.finish = time
                current.completed = True
                remaining_processes.remove(current)
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def run_priority_nonpreemptive(self):
        gantt = []
        time = 0
        remaining_processes = [p for p in self.processes]
        
        while remaining_processes:
            # Get ready processes
            ready = [p for p in remaining_processes if p.arrival <= time]
            
            if ready:
                # Find process with highest priority (lowest priority number)
                ready.sort(key=lambda p: p.priority)
                current = ready[0]
                
                # Execute process to completion
                for _ in range(current.service):
                    gantt.append(current.pid)
                    time += 1
                
                current.finish = time
                current.completed = True
                remaining_processes.remove(current)
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def run_priority_preemptive(self):
        gantt = []
        time = 0
        remaining_processes = [p for p in self.processes]
        
        while any(not p.completed for p in self.processes):
            # Get ready, uncompleted processes
            ready = [p for p in remaining_processes if p.arrival <= time and not p.completed]
            
            if ready:
                # Find process with highest priority (lowest priority number)
                ready.sort(key=lambda p: p.priority)
                current = ready[0]
                
                # Execute for 1 time unit
                gantt.append(current.pid)
                time += 1
                current.remaining -= 1
                
                if current.remaining == 0:
                    current.finish = time
                    current.completed = True
            else:
                gantt.append(None)
                time += 1
        
        return gantt
    
    def display_gantt_chart(self, gantt):
        self.gantt_scene.clear()
        
        if not gantt:
            return
        
        colors = {
            'P1': QColor(255, 0, 0),    # Red
            'P2': QColor(0, 255, 0),    # Green
            'P3': QColor(0, 0, 255),    # Blue
            'P4': QColor(255, 255, 0),  # Yellow
            'P5': QColor(255, 0, 255),  # Magenta
            'P6': QColor(0, 255, 255),  # Cyan
            'P7': QColor(128, 0, 0),    # Dark Red
            'P8': QColor(0, 128, 0),    # Dark Green
            'P9': QColor(0, 0, 128),    # Dark Blue
            'P10': QColor(128, 128, 0)  # Dark Yellow
        }
        
        x = 10
        y = 30
        width = 30
        height = 30
        
        # Draw time labels
        for i in range(len(gantt)+1):
            text = self.gantt_scene.addText(str(i))
            text.setPos(x + i*width - 5, y + height + 5)
        
        # Draw process blocks
        for i, pid in enumerate(gantt):
            if pid:
                color = colors.get(pid, QColor(200, 200, 200))  # Default to gray if unknown PID
                rect = self.gantt_scene.addRect(x + i*width, y, width, height, 
                                              brush=QBrush(color))
                text = self.gantt_scene.addText(pid)
                text.setPos(x + i*width + width/2 - 5, y + height/2 - 10)
            else:
                rect = self.gantt_scene.addRect(x + i*width, y, width, height, 
                                              brush=QBrush(Qt.lightGray))
    
    def display_results(self):
        self.results_table.setRowCount(len(self.processes))
        
        total_tat = 0
        total_waiting = 0
        total_ntat = 0
        
        for row, p in enumerate(self.processes):
            p.tat = p.finish - p.arrival
            p.waiting = p.tat - p.service
            p.ntat = p.tat / p.service if p.service > 0 else 0
            
            total_tat += p.tat
            total_waiting += p.waiting
            total_ntat += p.ntat
            
            self.results_table.setItem(row, 0, QTableWidgetItem(p.pid))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(p.finish)))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(p.tat)))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(p.waiting)))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{p.ntat:.2f}"))
        
        # Calculate averages
        count = len(self.processes)
        avg_tat = total_tat / count if count > 0 else 0
        avg_waiting = total_waiting / count if count > 0 else 0
        avg_ntat = total_ntat / count if count > 0 else 0
        
        self.avg_results_label.setText(
            f"Average TAT: {avg_tat:.2f} | "
            f"Average WT: {avg_waiting:.2f} | "
            f"Average NTAT: {avg_ntat:.2f}"
        )
    
    def run_deadlock_detection(self):
        # Get number of processes
        n, ok = QInputDialog.getInt(self, "Deadlock Detection", 
                                   "Enter number of processes:", 3, 1, 100, 1)
        if not ok:
            return
        
        # Get number of resource types
        m, ok = QInputDialog.getInt(self, "Deadlock Detection", 
                                   "Enter number of resource types:", 3, 1, 100, 1)
        if not ok:
            return
        
        # Initialize matrices
        allocation = [[0]*m for _ in range(n)]
        max_demand = [[0]*m for _ in range(n)]
        available = [0]*m
        
        # Input allocation matrix
        for i in range(n):
            for j in range(m):
                value, ok = QInputDialog.getInt(
                    self, "Allocation Matrix",
                    f"Allocation for Process {i}, Resource {j}:",
                    0, 0, 1000, 1
                )
                if not ok:
                    return
                allocation[i][j] = value
        
        # Input max matrix
        for i in range(n):
            for j in range(m):
                value, ok = QInputDialog.getInt(
                    self, "Max Demand Matrix",
                    f"Max demand for Process {i}, Resource {j}:",
                    1, 0, 1000, 1
                )
                if not ok:
                    return
                max_demand[i][j] = value
                
                # Validate that allocation <= max
                if allocation[i][j] > max_demand[i][j]:
                    QMessageBox.warning(
                        self, "Input Error",
                        f"Allocation cannot exceed max demand for Process {i}, Resource {j}"
                    )
                    return
        
        # Input available resources
        for j in range(m):
            value, ok = QInputDialog.getInt(
                self, "Available Resources",
                f"Available instances of Resource {j}:",
                1, 0, 1000, 1
            )
            if not ok:
                return
            available[j] = value
        
        # Calculate need matrix
        need = [[max_demand[i][j] - allocation[i][j] for j in range(m)] for i in range(n)]
        
        # Banker's algorithm
        work = available.copy()
        finish = [False]*n
        safe_sequence = []
        
        while True:
            found = False
            for i in range(n):
                if not finish[i] and all(need[i][j] <= work[j] for j in range(m)):
                    # Simulate process execution
                    for j in range(m):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(i)
                    found = True
            
            if not found:
                break
        
        if all(finish):
            QMessageBox.information(
                self, "Deadlock Detection Result",
                f"System is in a safe state.\nSafe sequence: {safe_sequence}"
            )
        else:
            QMessageBox.warning(
                self, "Deadlock Detection Result",
                "Deadlock detected! System is in an unsafe state."
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchedulingSimulator()
    window.show()
    sys.exit(app.exec_())