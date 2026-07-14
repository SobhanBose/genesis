import logging, io, os
from datetime import datetime
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from pathlib import Path

class Logger:
    def __init__(self, log_dir="logs", log_name=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if log_name is None:
            log_name = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.log_file = self.log_dir / log_name
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger(str(self.log_file))
        self.logger.setLevel(logging.INFO)
        # Remove old handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        # File handler
        fh = logging.FileHandler(self.log_file, mode='a')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def set_log_dir(self, log_dir, log_name=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if log_name is None:
            log_name = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.log_file = self.log_dir / log_name
        self._setup_logger()

    def log_model_summary(self, model: nn.Module, input_size=None):
        try:
            from torchinfo import summary
            stream = io.StringIO()
            if input_size is not None:
                # torchsummary expects input_size as tuple, e.g., (1, 28, 28)
                summary_str = summary(model, input_size, print_fn=lambda x: stream.write(x + "\n"))
                summary_str = stream.getvalue()
            else:
                summary_str = str(model)
            stream.close()
        except ImportError:
            summary_str = str(model)
        self.logger.info("MODEL SUMMARY:\n" + summary_str)

    def log_metrics(self, scores: dict, threshold: float, prefix: str):
        self.logger.info(f"{prefix} Metrics [t={threshold}]:\n")
        for key, val in scores.items():
            self.logger.info(f"{key}: {val}\n")

    def log_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray, threshold: float, prefix: str, labels: list = [0, 1]):
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        self.logger.info(f"{prefix} Confusion Matrix [t={threshold}]:")
        self.logger.info(f"\n{cm}\n")  

    def log_classification_report(self, y_true: np.ndarray, y_pred: np.ndarray, threshold: float, prefix: str, labels: list = [0, 1]):
        cr = classification_report(y_true, y_pred, labels=labels)
        self.logger.info(f"{prefix} Classification Report [t={threshold}]:")
        self.logger.info(f"\n{cr}\n")

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)
