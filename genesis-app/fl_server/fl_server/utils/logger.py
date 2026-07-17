import logging, io, os
from datetime import datetime
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
from pathlib import Path

class Logger:
    def __init__(self, log_dir="logs", log_name=None, run_id=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        
        if log_name is None:
            if run_id:
                # Use run_id for consistent naming when available
                log_name = "fl_server.log"
            else:
                # Fallback to timestamp for system-level logs
                log_name = f"system_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.log_file = self.log_dir / log_name
        self._setup_logger()

    def _setup_logger(self):
        # Create unique logger name to avoid conflicts
        # logger_name = f"fl_server.{self.run_id}" if self.run_id else f"fl_server.system"
        logger_name = (
            f"fl_server.{self.run_id}"
            if self.run_id
            else str(self.log_file)
        )
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Remove old handlers to avoid duplicates
        # if self.logger.hasHandlers():
        #     self.logger.handlers.clear()

        # Satirtha
        # IMPORTANT: properly close old handlers
        if self.logger.hasHandlers():
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False
        # Satirtha


        # Create formatter with UTC timestamps and run_id context
        if self.run_id:
            formatter = logging.Formatter(
                f'%(asctime)s UTC - %(levelname)s - [RUN:{self.run_id}] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s UTC - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Configure formatter to use UTC
        formatter.converter = lambda *args: datetime.utcnow().timetuple()
        
        # File handler
        fh = logging.FileHandler(self.log_file, mode='a')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console handler (optional, can be disabled for cleaner output)
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
    
    def log_debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def log_strategy_metrics(self, metrics: dict, prefix: str = ""):
        """Log strategy-specific metrics in a structured format."""
        if prefix:
            prefix = f"{prefix}_"
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                self.logger.info(f"{prefix}{key}: {value:.6f}")
            else:
                self.logger.info(f"{prefix}{key}: {value}")
    
    def log_strategy_info(self, strategy_name: str, config: dict):
        """Log strategy initialization information."""
        self.logger.info(f"=== {strategy_name} Strategy Initialized ===")
        for key, value in config.items():
            if isinstance(value, (int, float)):
                self.logger.info(f"  {key}: {value}")
            else:
                self.logger.info(f"  {key}: {value}")
        self.logger.info("=" * (len(strategy_name) + 30))
    
    def log_convergence_metrics(self, round_num: int, metrics: dict):
        """Log convergence-related metrics for training progress tracking - DISABLED for clean output."""
        # Detailed convergence metrics logging disabled to reduce output verbosity
        pass
    
    def log_fedadam_state(self, round_num: int, momentum_stats: dict, variance_stats: dict, 
                         bias_corrections: dict, numerical_stability: dict):
        """Log FedAdam-specific state information - DISABLED for clean output."""
        # Detailed FedAdam state logging disabled to reduce output verbosity
        # Only log critical numerical stability issues
        if numerical_stability:
            has_issues = (numerical_stability.get('has_nan_momentum', False) or 
                         numerical_stability.get('has_inf_momentum', False) or
                         numerical_stability.get('has_nan_variance', False) or 
                         numerical_stability.get('has_inf_variance', False))
            if has_issues:
                self.logger.warning(f"Round {round_num}: FedAdam numerical stability issues detected")
        # All other detailed state logging is suppressed
