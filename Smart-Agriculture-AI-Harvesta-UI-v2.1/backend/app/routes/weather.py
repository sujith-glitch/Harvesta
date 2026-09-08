"""
FastAPI Router for Weather API Endpoint.
"""

from fastapi import APIRouter, Query, HTTPException, status
from backend.app.services.weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["Weather Service"])

@router.get(
    "/current",
    status_code=status.HTTP_200_OK,
    summary="Get Real-Time Weather Metrics",
    description="Retrieves current ambient temperature, humidity, precipitation, and wind speed for given geographic coordinates."
)
def get_current_weather(
    latitude: float = Query(11.6643, ge=-90.0, le=90.0, description="Latitude coordinate (-90 to 90)"),
    longitude: float = Query(78.1460, ge=-180.0, le=180.0, description="Longitude coordinate (-180 to 180)")
):
    try:
        weather_data = WeatherService.get_current_weather(latitude, longitude)
        return {
            "latitude": latitude,
            "longitude": longitude,
            "weather": weather_data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to fetch weather data: {str(e)}"
        )
