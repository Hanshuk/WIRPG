import time
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QProgressBar, QGridLayout, QFrame, QListWidget, 
                               QListWidgetItem)
from PySide6.QtCore import Qt, QTimer
from db.database import db
from core.queue_manager import QueueManager
from logging_engine.logger import app_logger

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.queue_manager = QueueManager()
        self.start_time = None
        self.completed_at_start = 0
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 1. Header
        header_layout = QHBoxLayout()
        title = QLabel("Dashboard Analytics")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.lbl_status_badge = QLabel("System Idle")
        self.lbl_status_badge.setStyleSheet("""
            background-color: #555555; color: white; border-radius: 4px; 
            padding: 3px 8px; font-size: 11px; font-weight: bold;
        """)
        header_layout.addWidget(title)
        header_layout.addWidget(self.lbl_status_badge)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 2. Main Metrics Grid (3x4 Layout)
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(10)
        
        self.cards = {}
        self.metrics_def = [
            ("total", "TOTAL RECORDS", "0", "#0078D4"),
            ("completed", "COMPLETED PDFs", "0", "#107C41"),
            ("pending", "PENDING QUEUE", "0", "#F7A821"),
            ("processing", "CURRENT ACTIVE", "0", "#A4373F"),
            ("failed", "FAILED GENERATIONS", "0", "#D83B01"),
            ("flagged", "FLAGGED RECORDS", "0", "#E81123"),
            ("recovered", "RECOVERED FAILURES", "0", "#008272"),
            ("retried", "RETRY ATTEMPTS", "0", "#8764B8"),
            ("missing_imgs", "MISSING IMAGES", "0", "#C86400"),
            ("validation_fails", "VALIDATION FAILS", "0", "#5C2D91")
        ]
        
        for idx, (key, title_str, val, color) in enumerate(self.metrics_def):
            card = self._create_metric_card(title_str, val, color)
            self.cards[key] = card
            row = idx // 4
            col = idx % 4
            self.cards_layout.addWidget(card, row, col)
            
        layout.addLayout(self.cards_layout)
        
        # 3. Middle Section: Progress, Speed & ETA Gauge
        gauge_frame = QFrame()
        gauge_frame.setFrameShape(QFrame.StyledPanel)
        gauge_frame.setStyleSheet("background-color: palette(alternate-base); border-radius: 6px; padding: 10px;")
        lyt_gauge = QVBoxLayout(gauge_frame)
        
        lbl_prog_title = QLabel("Active Batch Progress Tracker")
        lbl_prog_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        lyt_gauge.addWidget(lbl_prog_title)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        lyt_gauge.addWidget(self.progress_bar)
        
        lyt_speed_eta = QHBoxLayout()
        self.lbl_speed = QLabel("Processing Speed: 0.00 records/sec")
        self.lbl_speed.setStyleSheet("font-size: 11px; color: #888888;")
        self.lbl_eta = QLabel("Estimated Time Remaining (ETA): N/A")
        self.lbl_eta.setStyleSheet("font-size: 11px; color: #888888;")
        
        lyt_speed_eta.addWidget(self.lbl_speed)
        lyt_speed_eta.addStretch()
        lyt_speed_eta.addWidget(self.lbl_eta)
        lyt_gauge.addLayout(lyt_speed_eta)
        
        layout.addWidget(gauge_frame)
        
        # 4. Bottom Section: Thread Activity Monitor & Recovery Events
        bot_layout = QHBoxLayout()
        
        # Left: Worker Thread Monitor
        frame_threads = QFrame()
        frame_threads.setFrameShape(QFrame.StyledPanel)
        lyt_threads = QVBoxLayout(frame_threads)
        lbl_thr = QLabel("Worker Thread Activity Monitor")
        lbl_thr.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.list_workers = QListWidget()
        self.list_workers.setStyleSheet("border: none; background: transparent;")
        lyt_threads.addWidget(lbl_thr)
        lyt_threads.addWidget(self.list_workers)
        
        # Right: Recovery Log Monitor
        frame_recovery = QFrame()
        frame_recovery.setFrameShape(QFrame.StyledPanel)
        lyt_rec = QVBoxLayout(frame_recovery)
        lbl_rec = QLabel("Recent System Checks & Recovery Log")
        lbl_rec.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.list_recovery = QListWidget()
        self.list_recovery.setStyleSheet("border: none; background: transparent;")
        lyt_rec.addWidget(lbl_rec)
        lyt_rec.addWidget(self.list_recovery)
        
        bot_layout.addWidget(frame_threads, 1)
        bot_layout.addWidget(frame_recovery, 1)
        layout.addLayout(bot_layout)
        
        # Update Timer (1 second interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_analytics)
        self.timer.start(1000)
        
    def _create_metric_card(self, title: str, val: str, border_color: str) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: palette(alternate-base);
                border-left: 4px solid {border_color};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        lyt = QVBoxLayout(card)
        lyt.setSpacing(4)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #888888;")
        
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet("font-size: 18px; font-weight: bold;")
        lbl_val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        lyt.addWidget(lbl_title)
        lyt.addWidget(lbl_val)
        
        # Store label reference for updates
        card.lbl_value = lbl_val
        return card

    def refresh_analytics(self):
        try:
            stats = {}
            with db.connection() as conn:
                # 1. Total Records
                cur = conn.execute("SELECT COUNT(*) FROM processing_queue")
                stats["total"] = cur.fetchone()[0]
                
                # 2. Status counts
                cur = conn.execute("SELECT status, COUNT(*) FROM processing_queue GROUP BY status")
                status_map = {row[0]: row[1] for row in cur.fetchall()}
                
                stats["completed"] = status_map.get("COMPLETED", 0)
                stats["pending"] = status_map.get("PENDING", 0)
                stats["processing"] = status_map.get("PROCESSING", 0)
                stats["failed"] = status_map.get("FAILED", 0)
                stats["skipped"] = status_map.get("SKIPPED", 0)
                stats["flagged"] = status_map.get("FLAGGED", 0)
                
                # 3. Recovered (completed after at least 1 retry)
                cur = conn.execute("SELECT COUNT(*) FROM processing_queue WHERE status = 'COMPLETED' AND retry_count > 0")
                stats["recovered"] = cur.fetchone()[0]
                
                # 4. Retried
                cur = conn.execute("SELECT SUM(retry_count) FROM processing_queue")
                stats["retried"] = cur.fetchone()[0] or 0
                
                # 5. Missing images
                cur = conn.execute("SELECT COUNT(*) FROM processing_queue WHERE error_type = 'MISSING_IMAGES' OR missing_images != ''")
                stats["missing_imgs"] = cur.fetchone()[0]
                
                # 6. Validation Failures
                cur = conn.execute("SELECT COUNT(*) FROM processing_queue WHERE error_message LIKE '%Validation%'")
                stats["validation_fails"] = cur.fetchone()[0]

            # Update Stat Values Natively
            for key, val in stats.items():
                if key in self.cards:
                    self.cards[key].lbl_value.setText(str(val))
                    
            # Update Progress Bar
            total = stats["total"]
            processed = stats["completed"] + stats["failed"] + stats["skipped"]
            if total > 0:
                percent = int((processed / total) * 100)
                self.progress_bar.setValue(percent)
            else:
                self.progress_bar.setValue(0)
                
            # Live ETA & Throughput Estimations
            if stats["processing"] > 0 or stats["pending"] > 0:
                self.lbl_status_badge.setText("Processing Batch")
                self.lbl_status_badge.setStyleSheet("""
                    background-color: #107C41; color: white; border-radius: 4px; 
                    padding: 3px 8px; font-size: 11px; font-weight: bold;
                """)
                
                if self.start_time is None:
                    self.start_time = time.time()
                    self.completed_at_start = processed
                
                elapsed = time.time() - self.start_time
                new_completed = processed - self.completed_at_start
                
                if elapsed > 1 and new_completed > 0:
                    speed = new_completed / elapsed
                    self.lbl_speed.setText(f"Processing Speed: {speed:.2f} records/sec")
                    
                    remaining = total - processed
                    eta_sec = remaining / speed
                    eta_str = str(timedelta(seconds=int(eta_sec)))
                    self.lbl_eta.setText(f"Estimated Time Remaining (ETA): {eta_str}")
                else:
                    self.lbl_speed.setText("Processing Speed: Calculating...")
                    self.lbl_eta.setText("Estimated Time Remaining (ETA): Calculating...")
            else:
                self.lbl_status_badge.setText("System Idle")
                self.lbl_status_badge.setStyleSheet("""
                    background-color: #555555; color: white; border-radius: 4px; 
                    padding: 3px 8px; font-size: 11px; font-weight: bold;
                """)
                self.lbl_speed.setText("Processing Speed: 0.00 records/sec")
                self.lbl_eta.setText("Estimated Time Remaining (ETA): N/A")
                self.start_time = None
                
            # Refresh Worker thread heartbeats list
            self._update_worker_threads()
            self._update_recovery_logs()
            
        except Exception as e:
            app_logger.error(f"Dashboard analytics update failed: {e}")

    def _update_worker_threads(self):
        self.list_workers.clear()
        # Query processing queue to see what is active
        with db.connection() as conn:
            cur = conn.execute("SELECT ias_no, name, updated_at FROM processing_queue WHERE status = 'PROCESSING'")
            rows = cur.fetchall()
            
        if rows:
            for r in rows:
                item = QListWidgetItem(f"Worker Core Active -> Processing: {r['name']} (IAS No: {r['ias_no']})")
                item.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
                self.list_workers.addItem(item)
        else:
            item = QListWidgetItem("All worker cores standby - waiting for queue payload...")
            self.list_workers.addItem(item)

    def _update_recovery_logs(self):
        self.list_recovery.clear()
        # Fetch last 5 logs from SQL
        with db.connection() as conn:
            cur = conn.execute("SELECT level, message, timestamp FROM logs ORDER BY id DESC LIMIT 5")
            rows = cur.fetchall()
            
        for r in rows:
            time_part = r['timestamp'].split('T')[-1][:8] if 'T' in r['timestamp'] else r['timestamp'][:8]
            item = QListWidgetItem(f"[{time_part}] {r['level']}: {r['message']}")
            self.list_recovery.addItem(item)
            
        if not rows:
            self.list_recovery.addItem(QListWidgetItem("No recent recovery events logged."))
