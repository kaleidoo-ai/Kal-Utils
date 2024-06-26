from typing import Optional
import httpx
from .logger import init_logger

logger = init_logger("utils.requests")

async def post(
    url: str,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    files: Optional[dict] = None,
    timeout=20,
    connect=5
) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if json is not None:
                response = await client.post(url, json=json)
            elif files is not None or data is not None:
                response = await client.post(url, data=data, files=files)
            else:
                response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e} - URL: {url}")
        raise

async def get(url: str, params: dict = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=timeout)
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

async def put(url: str, json: Optional[dict] = None, data: Optional[dict] = None, timeout=20, connect=5) -> dict:
    try:
        timeout = httpx.Timeout(timeout, connect=connect)

        async with httpx.AsyncClient(timeout=timeout) as client:
            if json is not None:
                response = await client.put(url, json=json)
            else:
                response = await client.put(url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text} - URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Request error: {e} - URL: {url}")
        raise
