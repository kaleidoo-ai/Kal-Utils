import sys
from kal_utils.event_messaging.core.logging import logger
import traceback
import asyncio
import psutil

original_stop_method = asyncio.AbstractEventLoop.stop

def handle_system_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Uncaught exception:\n{error_msg}")

    # Log additional system information
    import psutil
    logger.info(f"CPU usage: {psutil.cpu_percent()}%")
    logger.info(f"Memory usage: {psutil.virtual_memory().percent}%")
    logger.info(f"Disk usage: {psutil.disk_usage('/').percent}%")

def handle_task_exception(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation is not an error
    except Exception:
        logger.exception(f"Unhandled exception in background task {task.get_name()}")

async def monitor_tasks_handler():
    while True:
        for task in asyncio.all_tasks():
            if task.done() and not task.cancelled():
                handle_task_exception(task)
        await asyncio.sleep(60)  # Check every minute


async def monitor_resources_handler():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            logger.warning(f"High resource usage detected: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
        
        await asyncio.sleep(60)  # Check every minute
    
async def heartbeat():
    while True:
        logger.info("Application heartbeat")
        await asyncio.sleep(300)  # Log every 5 minutes

# handle loop errors
def patched_stop(self):
    logger.warning("Event loop is stopping", stack_info=True)
    original_stop_method(self)