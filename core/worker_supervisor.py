from PySide6.QtCore import QThread, Signal, QObject, QTimer, QMutex, QMutexLocker
from datetime import datetime
from typing import Dict, List, Any
import time
from logging_engine.logger import app_logger
from core.pdf_engine import PDFEngine
from core.pdf_validator import PDFValidator
from core.image_matcher import ImageMatcher
from core.queue_manager import QueueManager
from db.models import BeneficiaryRecord

class PDFWorker(QThread):
    progress_updated = Signal(str, int, int)
    entry_completed = Signal(str, str)
    entry_failed = Signal(str, str)
    log_message = Signal(str, str)

    def __init__(self, worker_id: str, queue_manager: QueueManager, records: Dict[str, BeneficiaryRecord], image_matcher: ImageMatcher, pdf_engine: PDFEngine, output_folder: str, heartbeat_dict: dict, heartbeat_mutex: QMutex):
        super().__init__()
        self.worker_id = worker_id
        self.queue = queue_manager
        self.records = records
        self.matcher = image_matcher
        self.pdf_engine = pdf_engine
        self.output_folder = output_folder
        self.heartbeat_dict = heartbeat_dict
        self.heartbeat_mutex = heartbeat_mutex
        self.current_queue_id = None

    def run(self):
        self._update_heartbeat()
        while not self.isInterruptionRequested():
            entry = self.queue.dequeue_next()
            if not entry:
                time.sleep(1)
                self._update_heartbeat()
                continue

            q_id = entry['queue_id']
            self.current_queue_id = q_id
            ias_no = entry['ias_no']
            name = entry['name']
            
            try:
                record = self.records.get(ias_no)
                if not record:
                    raise Exception(f"Record {ias_no} not found in memory.")

                matched_path, score, stage = self.matcher.match(name)
                image_paths = self.matcher.get_image_paths(matched_path) if matched_path else {}
                
                self._update_heartbeat()
                
                pdf_path = self.pdf_engine.generate(record, image_paths, self.output_folder)
                
                self._update_heartbeat()
                
                val_res = PDFValidator.validate(pdf_path)
                if not val_res.is_valid:
                    raise Exception(f"PDF Validation failed: {', '.join(val_res.errors)}")
                    
                self.queue.mark_completed(q_id, pdf_path)
                self.entry_completed.emit(q_id, pdf_path)
                
            except Exception as e:
                self.queue.mark_failed(q_id, str(e))
                self.entry_failed.emit(q_id, str(e))
            finally:
                self.current_queue_id = None
                self._update_heartbeat()

    def _update_heartbeat(self):
        with QMutexLocker(self.heartbeat_mutex):
            self.heartbeat_dict[self.worker_id] = datetime.now()


class WorkerSupervisor(QObject):
    worker_frozen_detected = Signal(str, str)
    worker_restarted = Signal(str)

    def __init__(self, num_workers: int, queue_manager, records, image_matcher, pdf_engine, output_folder):
        super().__init__()
        self.num_workers = num_workers
        self.queue_manager = queue_manager
        self.records = records
        self.image_matcher = image_matcher
        self.pdf_engine = pdf_engine
        self.output_folder = output_folder
        
        self.workers: Dict[str, PDFWorker] = {}
        self.heartbeat_dict = {}
        self.heartbeat_mutex = QMutex()
        self.shutdown_requested = False
        
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._check_heartbeats)

    def start(self):
        self.shutdown_requested = False
        for i in range(self.num_workers):
            self._spawn_worker(f"worker_{i}")
        self.monitor_timer.start(5000)

    def _spawn_worker(self, worker_id: str):
        worker = PDFWorker(
            worker_id, self.queue_manager, self.records, 
            self.image_matcher, self.pdf_engine, self.output_folder,
            self.heartbeat_dict, self.heartbeat_mutex
        )
        self.workers[worker_id] = worker
        with QMutexLocker(self.heartbeat_mutex):
            self.heartbeat_dict[worker_id] = datetime.now()
        worker.start()

    def _check_heartbeats(self):
        if self.shutdown_requested: return
        now = datetime.now()
        frozen_workers = []
        with QMutexLocker(self.heartbeat_mutex):
            for wid, last_beat in self.heartbeat_dict.items():
                if (now - last_beat).total_seconds() > 30:
                    frozen_workers.append(wid)
                    
        for wid in frozen_workers:
            worker = self.workers.get(wid)
            if worker:
                q_id = worker.current_queue_id
                self.worker_frozen_detected.emit(wid, q_id or "NONE")
                app_logger.error(f"Worker {wid} frozen (Queue ID: {q_id}). Attempting restart.")
                worker.requestInterruption()
                worker.wait(5000)
                if worker.isRunning():
                    worker.terminate()
                    worker.wait()
                if q_id:
                    self.queue_manager.mark_failed(q_id, "WORKER_TIMEOUT")
                self._spawn_worker(wid)
                self.worker_restarted.emit(wid)

    def shutdown(self):
        self.shutdown_requested = True
        self.monitor_timer.stop()
        for worker in self.workers.values():
            worker.requestInterruption()
            
        for worker in self.workers.values():
            if not worker.wait(10000):
                worker.terminate()
                worker.wait()
                
        self.workers.clear()
        self.queue_manager.restore_interrupted()
