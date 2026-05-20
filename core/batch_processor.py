import json
import csv
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer
from core.excel_parser import ExcelParser
from core.image_matcher import ImageMatcher
from core.pdf_engine import PDFEngine
from core.template_engine import TemplateEngine
from core.queue_manager import QueueManager
from core.worker_supervisor import WorkerSupervisor
from core.recovery_manager import RecoveryManager
from core.validation_engine import ValidationEngine
from logging_engine.logger import app_logger
from utils.file_utils import ensure_dir

class BatchProcessor(QObject):
    batch_completed = Signal(str)
    batch_progress = Signal(int, int)
    batch_error = Signal(str)

    def __init__(self, num_workers: int):
        super().__init__()
        self.num_workers = num_workers
        self.queue_manager = QueueManager()
        self.recovery_manager = RecoveryManager()
        self.template_engine = TemplateEngine()
        self.image_matcher = ImageMatcher()
        self.supervisor = None
        self.session_id = None
        self.total_rows = 0
        
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._check_progress)

    def start_batch(self, excel_path: str, images_folder: str, output_folder: str, template_path: str = None):
        try:
            val_excel = ValidationEngine.validate_excel(excel_path)
            if not val_excel.is_valid:
                raise Exception(f"Excel validation failed: {', '.join(val_excel.errors)}")
                
            val_images = ValidationEngine.validate_images_folder(images_folder)
            if not val_images.is_valid:
                raise Exception(f"Images folder validation failed: {', '.join(val_images.errors)}")
            for w in val_images.warnings:
                app_logger.warning(w)

            parser = ExcelParser(excel_path)
            records = parser.parse()
            if not records:
                raise Exception("No valid records found in Excel file.")
            self.total_rows = len(records)
            
            record_dict = {r.ias_no: r for r in records}

            self.session_id = self.recovery_manager.start_session(excel_path, images_folder, output_folder, template_path or "", self.total_rows)

            self.image_matcher.build_index(images_folder)
            self.queue_manager.enqueue(records)

            self.template_engine.load(template_path)
            pdf_engine = PDFEngine(self.template_engine)
            ensure_dir(output_folder)

            self.supervisor = WorkerSupervisor(
                self.num_workers, self.queue_manager, record_dict, 
                self.image_matcher, pdf_engine, output_folder
            )
            self.supervisor.start()
            
            self.progress_timer.start(2000)
            app_logger.info(f"Batch started. Session: {self.session_id}, Rows: {self.total_rows}")

        except Exception as e:
            app_logger.error(f"Batch start failed: {str(e)}")
            self.batch_error.emit(str(e))

    def _check_progress(self):
        stats = self.queue_manager.get_queue_stats()
        processed = stats.completed + stats.failed + stats.skipped
        self.batch_progress.emit(processed, stats.total)
        
        if self.session_id and (processed % 10 == 0 or processed == stats.total):
            self.recovery_manager.update_checkpoint(self.session_id, stats.completed, stats.failed)
            
        if processed == stats.total and stats.total > 0:
            self.progress_timer.stop()
            if self.supervisor:
                self.supervisor.shutdown()
            
            if self.session_id:
                self.recovery_manager.mark_completed(self.session_id)
                
            self._write_reports(stats)

    def _write_reports(self, stats):
        out_folder = Path("logs")
        ensure_dir(str(out_folder))
        
        rep_path = out_folder / "batch_summary.json"
        with open(rep_path, 'w') as f:
            json.dump({
                "total": stats.total,
                "completed": stats.completed,
                "failed": stats.failed,
                "skipped": stats.skipped
            }, f, indent=4)
            
        self.batch_completed.emit(str(rep_path))

    def cancel_batch(self):
        self.progress_timer.stop()
        if self.supervisor:
            self.supervisor.shutdown()
        if self.session_id:
            self.recovery_manager.mark_interrupted(self.session_id)
        app_logger.info("Batch cancelled by user.")
