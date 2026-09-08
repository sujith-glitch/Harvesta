"""
Weather Service for fetching real-time weather metrics.
Uses Open-Meteo REST API (public, no API key required).
"""

import json
import logging
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

class WeatherService:
    # Transient failures (429 rate-limit, 5xx, network blips) are retried once
    # after a short backoff before surfacing an error to the farmer.
    MAX_ATTEMPTS = 2
    RETRY_BACKOFF_SECONDS = 1.5

    @staticmethod
    def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetches current weather metrics for specified latitude and longitude.
        
        Returns:
            dict: {
                "temperature": float,
                "humidity": float,
                "precipitation": float,
                "wind_speed": float
            }
        """
        # Validate coordinates
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Invalid latitude '{latitude}'. Must be between -90 and 90.")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Invalid longitude '{longitude}'. Must be between -180 and 180.")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        }

        url = f"{OPEN_METEO_BASE_URL}?{urllib.parse.urlencode(params)}"

        last_error: Exception = None
        for attempt in range(1, WeatherService.MAX_ATTEMPTS + 1):
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SmartAgricultureAI/1.0"}
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Open-Meteo API returned status HTTP {response.status}")
                        raise RuntimeError(f"Weather API request failed with status code {response.status}")

                    raw_body = response.read().decode('utf-8')
                    data = json.loads(raw_body)

                    current = data.get("current", {})

                    temperature = float(current.get("temperature_2m", 25.0))
                    humidity = float(current.get("relative_humidity_2m", 60.0))
                    precipitation = float(current.get("precipitation", 0.0))
                    wind_speed = float(current.get("wind_speed_10m", 10.0))

                    return {
                        "temperature": round(temperature, 2),
                        "humidity": round(humidity, 2),
                        "precipitation": round(precipitation, 2),
                        "wind_speed": round(wind_speed, 2)
                    }

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limited — friendly message for the farmer UI.
                    logger.warning(f"Open-Meteo rate limit hit (attempt {attempt}): {e}")
                    last_error = RuntimeError(
                        "Weather service is temporarily busy (rate limited). "
                        "Please try again in a few minutes, or use Manual mode with your own readings."
                    )
                elif 500 <= e.code < 600:
                    logger.warning(f"Open-Meteo server error {e.code} (attempt {attempt})")
                    last_error = RuntimeError(
                        "Weather service is temporarily unavailable. Please try again shortly or use Manual mode."
                    )
                else:
                    logger.error(f"Open-Meteo API HTTP error: {e}")
                    raise RuntimeError(f"Weather API request failed with status code {e.code}")
            except urllib.error.URLError as e:
                logger.warning(f"Failed to reach Weather API (attempt {attempt}): {e}")
                last_error = RuntimeError(
                    "Unable to connect to the weather service. Check your internet connection or use Manual mode."
                )
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Weather API response: {e}")
                raise RuntimeError("Received invalid data format from weather service.")
            except Exception as e:
                logger.error(f"Unexpected error in WeatherService: {e}")
                raise RuntimeError(f"Error fetching weather data: {str(e)}")

            # Backoff before retry (only for transient classes handled above)
            if attempt < WeatherService.MAX_ATTEMPTS:
                time.sleep(WeatherService.RETRY_BACKOFF_SECONDS)

        raise last_error
