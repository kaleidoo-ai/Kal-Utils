import sys
from loguru import logger
import logging

# Remove any pre-configured handlers
logger.remove()

# Directory and file name for the logs
log_directory = "/app/logs"
log_file = f"{log_directory}/app.log"

# log format
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"


# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(sys.stderr, 
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           level="DEBUG")
logger.add("/app/logs/fastapi.log", 
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           level="DEBUG",
           rotation="10 MB",
           retention="5 days")

# Create a custom logging config for uvicorn
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "default": {
            "class": "core.logging.InterceptHandler",  # make sure this points to the InterceptHandler in your main script
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "DEBUG"},
        "uvicorn": {"handlers": ["default"], "level": "DEBUG"},
        "uvicorn.error": {"handlers": ["default"], "level": "DEBUG"},
        "aio_pika": {"handlers": ["default"], "level": "WARNING"},
        "aiormq": {"handlers": ["default"], "level": "WARNING"},
    },
}







# # Add a new handler with a custom format
# logger.add(
#     log_file,
#     format=log_format,
#     level="DEBUG",
# )

# logging_config = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "default": {
#             "()": "uvicorn.logging.DefaultFormatter",
#             "fmt": log_format,
#             "use_colors": True,
#         },
#     },
#     "handlers": {
#         "default": {
#             "formatter": "default",
#             "class": "logging.StreamHandler",
#             "stream": "ext://sys.stderr",
#         },
#         "file": {
#             "formatter": "default",
#             "class": "logging.handlers.RotatingFileHandler",
#             "filename": "/app/logs/fastapi.log",
#             "maxBytes": 10000000,  # 10MB
#             "backupCount": 5,
#         },
#     },
#     "loggers": {
#         "": {"handlers": ["default", "file"], "level": "DEBUG"},
#     },
# }


# Add a new handler for file output with the same custom format
# logger.add(
#     log_file,
#     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>: <cyan>{function}</cyan>: <cyan>{line}</cyan> - <level>{message}</level>",
#     level="INFO",
#     rotation="10 MB",  # Rotate the log file after it reaches 10 MB
#     retention="10 days",  # Keep logs for 10 days
#     compression="zip"  # Compress logs to save space
# )
# logger.add(log_file)