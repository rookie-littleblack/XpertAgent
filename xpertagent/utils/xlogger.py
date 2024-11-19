"""
Custom JSON Logger with MongoDB Support

This module provides a comprehensive logging solution with the following features:
1. JSON-formatted log output
2. MongoDB integration for log storage
3. Colored console output
4. Daily log rotation
5. Asynchronous MongoDB writing
6. Multi-level logging support
7. Caller information tracking
"""

import os
import json
import logging
import inspect
import time

from queue import Queue, Empty
from pymongo import MongoClient
from datetime import datetime
from threading import Thread, Lock
from logging.handlers import TimedRotatingFileHandler
from xpertagent.config.settings import settings

class Colors:
    """ANSI color codes for console output"""
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels in console output"""
    COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA
    }

    def format(self, record):
        """Format log record with appropriate color"""
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, Colors.WHITE)}{log_message}{Colors.RESET}"

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Custom implementation of TimedRotatingFileHandler that supports:
    1. Custom directory structure for rotated logs
    2. Daily log file organization
    3. Automatic directory creation
    4. Custom file naming convention
    """

    def __init__(self, log_dir, log_filename, when='midnight', interval=1, backupCount=7, encoding='utf-8'):
        """
        Initialize the handler with custom directory support.
        
        Args:
            log_dir (str): Base directory for log files
            log_filename (str): Name of the log file
            when (str): Rotation timing specification
            interval (int): Interval for rotation
            backupCount (int): Number of backup files to keep
            encoding (str): Character encoding for log files
        """
        self.log_dir = log_dir
        self.log_filename = log_filename
        super().__init__(os.path.join(log_dir, log_filename), 
                        when=when, interval=interval, 
                        backupCount=backupCount, encoding=encoding)

    def doRollover(self):
        """
        Perform log rotation with custom directory structure.
        Creates a daily subdirectory and moves the log file there.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Calculate rotation timestamp
        t = self.rolloverAt - self.interval
        time_tuple = time.localtime(t)

        # Create daily directory and generate new filename
        daily_log_path = os.path.join(self.log_dir, "daily")
        os.makedirs(daily_log_path, exist_ok=True)
        dfn = os.path.join(daily_log_path, 
                          f"{time.strftime('%Y%m%d', time_tuple)}_{self.log_filename}")

        # Rotate the log file
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)

        # Open new log file
        if not self.delay:
            self.stream = self._open()

        # Calculate next rollover time
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        self.rolloverAt = newRolloverAt

    def emit(self, record):
        """
        Emit a log record with rollover support.
        
        Args:
            record: Log record to emit
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            TimedRotatingFileHandler.emit(self, record)
        except Exception:
            self.handleError(record)

class LogMongoDBClient:
    """
    MongoDB client specifically for log management.
    Provides methods for log insertion and querying with various filters.
    """
    def __init__(self):
        """
        Initialize MongoDB client with configuration from settings.
        Establishes connection to specified database and collection.
        """
        mongo_config = settings.XLOGGER_LOG_MONGODB_CONFIG
        uri = f"mongodb://{mongo_config['user']}:{mongo_config['pass']}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['dbnm']}"
        self.client = MongoClient(uri)
        self.db = self.client[mongo_config['clnm']]
        self.collection = self.db[mongo_config['tbnm']]

    def check_connection(self):
        """
        Check if MongoDB connection is alive.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.client.server_info()
            return True
        except Exception as e:
            return False

    def insert_many(self, documents):
        """
        Bulk insert multiple log documents.
        
        Args:
            documents (list): List of log documents to insert
            
        Returns:
            InsertManyResult: Result of the bulk insertion operation
        """
        if self.collection:
            return self.collection.insert_many(documents)
        return None
    
    def find_logs(self, query=None, projection=None, sort=None, limit=None):
        """
        Generic log query method with flexible parameters.
        
        Args:
            query (dict): MongoDB query conditions
            projection (dict): Fields to include/exclude
            sort (list): Sort criteria, e.g., [("time", -1)]
            limit (int): Maximum number of results to return
            
        Returns:
            list: Query results matching the criteria
        """
        cursor = self.collection.find(query or {}, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_logs_by_text(self, text, case_sensitive=False, limit=None):
        """
        Search logs by text content.
        
        Args:
            text (str): Text to search for
            case_sensitive (bool): Whether to perform case-sensitive search
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs containing the specified text
        """
        query = {
            "message.text": {
                "$regex": text,
                "$options": "" if case_sensitive else "i"
            }
        }
        return self.find_logs(query, limit=limit)

    def find_logs_by_time_range(self, start_time=None, end_time=None, limit=None):
        """
        Query logs within a specified time range.
        
        Args:
            start_time (str): Start time in "YYYY-MM-DD HH:MM:SS" format
            end_time (str): End time in "YYYY-MM-DD HH:MM:SS" format
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs within the specified time range
        """
        query = {}
        if start_time or end_time:
            query["time"] = {}
            if start_time:
                query["time"]["$gte"] = start_time
            if end_time:
                query["time"]["$lte"] = end_time
        
        return self.find_logs(query, sort=[("time", -1)], limit=limit)

    def find_logs_by_level(self, level, limit=None):
        """
        Query logs by logging level.
        
        Args:
            level (str): Log level (e.g., "INFO", "ERROR")
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs matching the specified level
        """
        query = {"level": level.upper()}
        return self.find_logs(query, sort=[("time", -1)], limit=limit)

    def find_logs_by_category(self, category, limit=None):
        """
        Query logs by category.
        
        Args:
            category (str): Log category to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs matching the specified category
        """
        query = {"category": category}
        return self.find_logs(query, sort=[("time", -1)], limit=limit)
    
    def find_logs_by_tags(self, tags, limit=None):
        """
        Query logs by tags.
        
        Args:
            tags (list/str): Tag or list of tags to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs containing the specified tags
        """
        query = {"tags": tags}
        return self.find_logs(query, sort=[("time", -1)], limit=limit)

    def find_error_logs(self, limit=None):
        """
        Query error logs.
        
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            list: All error level logs
        """
        return self.find_logs_by_level("ERROR", limit=limit)

    def find_logs_advanced(self, text=None, level=None, category=None, tags=None, 
                         env=None, start_time=None, end_time=None, limit=None):
        """
        Advanced log query with multiple criteria.
        
        Args:
            text (str): Text to search in log messages
            level (str): Log level
            category (str): Log category
            tags (list/str): Log tags
            env (str): Environment identifier
            start_time (str): Start time for range query
            end_time (str): End time for range query
            limit (int): Maximum number of results to return
            
        Returns:
            list: Logs matching all specified criteria
        """
        query = {}
        
        # Text search
        if text:
            query["message.text"] = {"$regex": text, "$options": "i"}
        
        # Log level
        if level:
            query["level"] = level.upper()
        
        # Category
        if category:
            query["category"] = category
        
        # Tags
        if tags:
            query["tags"] = tags
        
        # Environment
        if env:
            query["env"] = env
        
        # Time range
        if start_time or end_time:
            query["time"] = {}
            if start_time:
                query["time"]["$gte"] = start_time
            if end_time:
                query["time"]["$lte"] = end_time
        
        return self.find_logs(query, sort=[("time", -1)], limit=limit)

class MongoDBLogHandler:
    """
    MongoDB Log Handler for asynchronous log processing.
    Provides buffered writing and batch processing capabilities.
    """
    def __init__(self, max_batch_size=64, flush_interval=5):
        """
        Initialize MongoDB log handler.
        
        Args:
            max_batch_size (int): Maximum number of logs to batch before writing
            flush_interval (int): Maximum time (seconds) to wait before forcing a write
        """
        self.mongo_client = LogMongoDBClient()
        self.max_batch_size = max_batch_size
        self.flush_interval = flush_interval
        self.log_queue = Queue()
        self.lock = Lock()
        self.buffer = []
        
        # Start async processing thread
        self.running = True
        self.worker_thread = Thread(target=self._process_logs, daemon=True)
        self.worker_thread.start()

    def emit(self, log_record: dict):
        """
        Add a log record to the processing queue.
        
        Args:
            log_record (dict): Log record to be processed
        """
        self.log_queue.put(log_record)

    def _process_logs(self):
        """
        Background thread for processing log records.
        Handles batching and periodic flushing of logs.
        """
        last_flush_time = time.time()

        while self.running:
            try:
                # Get log records
                while len(self.buffer) < self.max_batch_size:
                    try:
                        log_record = self.log_queue.get(timeout=0.1)
                        self.buffer.append(log_record)
                    except Empty:
                        break

                current_time = time.time()
                should_flush = (
                    len(self.buffer) >= self.max_batch_size or
                    (current_time - last_flush_time) >= self.flush_interval
                )

                if should_flush and self.buffer:
                    self._flush_buffer()
                    last_flush_time = current_time

            except Exception as e:
                print(f"Error processing logs: {e}")

    def _flush_buffer(self):
        """
        Write buffered logs to MongoDB.
        Uses thread-safe operations to prevent data corruption.
        """
        if not self.buffer:
            return

        with self.lock:
            try:
                self.mongo_client.collection.insert_many(self.buffer)
                self.buffer = []
            except Exception as e:
                print(f"Error flushing logs to MongoDB: {e}")

    def close(self):
        """
        Clean up handler resources.
        Ensures all pending logs are written before shutdown.
        """
        self.running = False
        self.worker_thread.join()
        self._flush_buffer()  # Final flush of buffer

class CustomJSONLogger:
    """
    Singleton JSON logger with file, console, and MongoDB output support.
    Provides formatted logging with metadata and multiple output channels.
    """
    _instance = None

    @classmethod
    def get_instance(cls, log_dir=settings.XLOGGER_LOG_DIR, 
                    log_filename=settings.XLOGGER_LOG_FILENAME, 
                    version=settings.XLOGGER_LOG_VER, 
                    console_output=True):
        """
        Get or create singleton logger instance.
        
        Args:
            log_dir (str): Directory for log files
            log_filename (str): Name of the log file
            version (str): Logger version
            console_output (bool): Enable console output
            
        Returns:
            CustomJSONLogger: Singleton logger instance
        """
        if cls._instance is None:
            cls._instance = cls(log_dir, log_filename, version, console_output)
        return cls._instance

    def __init__(self, log_dir=settings.XLOGGER_LOG_DIR, 
                 log_filename=settings.XLOGGER_LOG_FILENAME, 
                 version=settings.XLOGGER_LOG_VER, 
                 console_output=True):
        """
        Initialize logger with specified configuration.
        
        Args:
            log_dir (str): Directory for log files
            log_filename (str): Name of the log file
            version (str): Logger version
            console_output (bool): Enable console output
        """
        self.log_filename = log_filename
        self.default_version = version
        self.log_dir = log_dir

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create log directory if not exists
        os.makedirs(self.log_dir, exist_ok=True)

        # Configure file handler with JSON format
        file_formatter = logging.Formatter('%(message)s')  # Format for file output
        self.file_handler = CustomTimedRotatingFileHandler(
            log_dir=self.log_dir,
            log_filename=self.log_filename,
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        self.file_handler.setFormatter(file_formatter)
        self.logger.addHandler(self.file_handler)

        # Configure console handler with colored output
        if console_output:
            console_formatter = ColoredFormatter('%(message)s')  # Format for console output
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # Initialize MongoDB handler if enabled
        self.mongo_handler = None
        if settings.XLOGGER_LOG_MONGODB_ENABLE:
            mongo_client = LogMongoDBClient()
            if mongo_client.check_connection():
                self.mongo_handler = MongoDBLogHandler()
            else:
                print("Failed to connect to MongoDB. Disabling MongoDB logging.")

    def get_calling_class(self):
        """
        Get the name of the calling class.
        
        Returns:
            str: Name of the calling class or None if not called from a class
        """
        current_frame = inspect.currentframe()
        calling_frame = inspect.getouterframes(current_frame, 2)
        calling_class = calling_frame[2].frame.f_locals.get('self', None)
        if calling_class:
            return calling_class.__class__.__name__
        return None
    
    def safe_str(self, obj):
        """
        Safely convert object to string, handling encoding issues.
        
        Args:
            obj: Object to convert to string
            
        Returns:
            str: Safe string representation of the object
        """
        try:
            return str(obj)
        except UnicodeEncodeError:
            return obj.encode('utf-8', errors='ignore').decode('utf-8')

    def log(self, message, data=None, log_level=None, category=None, version=None, tags=None):
        """
        Main logging method with support for structured data and metadata.
        
        Args:
            message: Log message content
            data: Additional structured data to include
            log_level: Logging level (DEBUG, INFO, etc.)
            category: Log category for grouping
            version: Version information
            tags: Tags for filtering logs
        """
        if log_level is None:
            log_level = logging.DEBUG

        if category is None:
            category = self.get_caller_script_name()

        # Get environment from settings or environment variable
        env = os.getenv('PROJ_ENV', settings.PROJ_ENV)
        
        # Format current time with milliseconds precision
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Construct log data structure
        log_data = {
            'time': current_time,
            'version': version or self.default_version,
            'level': logging.getLevelName(log_level),
            'category': category,
            'tags': tags,
            'env': env,
            'message': {
                'text': self.safe_str(message) if isinstance(message, dict) else self.safe_str(message)
            }
        }

        # Add error details for ERROR level logs
        if log_level == logging.ERROR:
            caller = self.logger.findCaller()
            log_data['message']['line'] = f"{caller[1]}:{caller[2]}"
            calling_class = self.get_calling_class()
            if calling_class:
                log_data['message']['classname'] = calling_class

        # Add additional data if provided
        if data is not None:
            if isinstance(data, dict):
                log_data['message'].update(data)
            else:
                log_data['message']['data'] = data

        # Prepare JSON formatted log message for file handler
        json_log_message = json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        
        # Prepare formatted log message for console handler
        console_log_message = f"{log_data['time']} - {log_data['level']} - {log_data['category']}: {log_data['message']['text']}"
        
        # Record to file and console separately
        for handler in self.logger.handlers:
            if isinstance(handler, CustomTimedRotatingFileHandler):
                handler.emit(logging.LogRecord(
                    name=self.logger.name,
                    level=log_level,
                    pathname='',
                    lineno=0,
                    msg=json_log_message,
                    args=(),
                    exc_info=None
                ))
            elif isinstance(handler, logging.StreamHandler):
                handler.emit(logging.LogRecord(
                    name=self.logger.name,
                    level=log_level,
                    pathname='',
                    lineno=0,
                    msg=console_log_message,
                    args=(),
                    exc_info=None
                ))

        # Add MongoDB logging if enabled
        if self.mongo_handler:
            self.mongo_handler.emit(log_data)

    def __del__(self):
        """Ensure proper cleanup of MongoDB handler on object destruction"""
        if self.mongo_handler:
            self.mongo_handler.close()

    @staticmethod
    def get_caller_script_name():
        """
        Get the name of the calling script.
        
        Returns:
            str: Name of the calling script file
        """
        frame = inspect.currentframe()
        while frame:
            filename = frame.f_code.co_filename
            if filename != __file__:
                return os.path.basename(filename)
            frame = frame.f_back
        return None

    # Convenience methods for different log levels
    def warning(self, message, data=None, category=None, version=None, tags=None):
        """Log a warning message"""
        self.log(message, data, log_level=logging.WARNING, category=category, version=version, tags=tags)

    def error(self, message, data=None, category=None, version=None, tags=None):
        """Log an error message"""
        self.log(message, data, log_level=logging.ERROR, category=category, version=version, tags=tags)

    def exceptions(self, message, category=None, version=None, tags=None):
        """Log an exception message"""
        self.log(message, log_level=logging.ERROR, category=category, version=version, tags=tags)

    def info(self, message, data=None, category=None, version=None, tags=None):
        """Log an info message"""
        self.log(message, data, log_level=logging.INFO, category=category, version=version, tags=tags)

    def debug(self, message, data=None, category=None, version=None, tags=None):
        """Log a debug message"""
        self.log(message, data, log_level=logging.DEBUG, category=category, version=version, tags=tags)

# Create global logger instance
logger = CustomJSONLogger.get_instance()
