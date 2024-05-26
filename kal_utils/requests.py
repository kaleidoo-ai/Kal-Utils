import httpx
from .logger import init_logger

logger = init_logger("utils.requests")

async def post(url: str, json: dict, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=json)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise

async def get(url: str, params: dict = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise

async def delete(url: str, json: dict = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.delete(url, json=json)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise

async def put(url: str, json: dict, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.put(url, json=json)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e}")
        raise
