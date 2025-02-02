import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz

class WeatherForecast:
    """
    A class to retrieve weather forecasts using the Open-Meteo API.
    The timezone is fixed to UTC+8 (Beijing Time)

    Attributes:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEZONE = "Asia/Shanghai"  # UTC+8 (Beijing Time)

    def __init__(self, latitude: float, longitude: float, timezone: str = "Asia/Shanghai"):
        """
        Initializes the WeatherForecast instance with location.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.TIMEZONE = timezone
        self.forecast_data: Optional[Dict[str, Any]] = None

    def fetch_forecast(self, forecast_hours: int = 24) -> None:
        """
        Fetches the weather forecast data for the specified number of hours from the Open-Meteo API.

        Args:
            forecast_hours (int): Number of hours to fetch the forecast for.

        Raises:
            Exception: If the API request fails or returns invalid data.
        """
        if not isinstance(forecast_hours, int) or forecast_hours <= 0:
            raise ValueError("forecast_hours must be a positive integer.")

        # Calculate the number of forecast days needed to cover the requested hours
        forecast_days = (forecast_hours // 24) + 2  # Extra day to ensure coverage

        # Define the parameters for the API request
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": "temperature_2m,precipitation,windspeed_10m,winddirection_10m,weathercode",
            "timezone": self.TIMEZONE,
            "forecast_days": forecast_days  # Dynamic based on forecast_hours
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()

            # Validate the response structure
            if "hourly" not in data or "time" not in data["hourly"]:
                raise ValueError("Invalid response structure from Open-Meteo API.")

            self.forecast_data = data["hourly"]

        except requests.RequestException as e:
            raise Exception(f"Error fetching data from Open-Meteo API: {e}")
        except ValueError as ve:
            raise Exception(f"Data processing error: {ve}")

    def get_forecast(self, forecast_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retrieves the weather forecast for the specified number of hours.

        Args:
            forecast_hours (int): Number of hours to retrieve the forecast for.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing hourly forecast data.

        Raises:
            Exception: If forecast data has not been fetched yet.
            ValueError: If forecast_hours is not a positive integer.
        """
        if not self.forecast_data:
            raise Exception("Forecast data not fetched. Call fetch_forecast() first.")

        if not isinstance(forecast_hours, int) or forecast_hours <= 0:
            raise ValueError("forecast_hours must be a positive integer.")

        # Set timezone to UTC+8
        timezone = pytz.timezone(self.TIMEZONE)
        current_time = datetime.now(timezone)
        end_time = current_time + timedelta(hours=forecast_hours)

        forecasts = []
        times = self.forecast_data.get("time", [])
        temperatures = self.forecast_data.get("temperature_2m", [])
        precipitations = self.forecast_data.get("precipitation", [])
        windspeeds = self.forecast_data.get("windspeed_10m", [])
        winddirections = self.forecast_data.get("winddirection_10m", [])
        weathercodes = self.forecast_data.get("weathercode", [])

        for i, time_str in enumerate(times):
            # Parse the forecast time with timezone awareness
            try:
                forecast_time = datetime.fromisoformat(time_str)
                if forecast_time.tzinfo is None:
                    forecast_time = timezone.localize(forecast_time)
                else:
                    forecast_time = forecast_time.astimezone(timezone)
            except Exception as e:
                print(f"Error parsing time string '{time_str}': {e}")
                continue  # Skip this entry if time parsing fails

            if current_time <= forecast_time <= end_time:
                forecast = {
                    "time": forecast_time.strftime("%Y-%m-%d %H:%M"),
                    "temperature_2m": temperatures[i],
                    "precipitation": precipitations[i],
                    "windspeed_10m": windspeeds[i],
                    "winddirection_10m": winddirections[i],
                    "weathercode": weathercodes[i],
                    "weather_description": self._get_weather_description(weathercodes[i])
                }
                forecasts.append(forecast)

            # Early exit if we've collected enough forecasts
            if len(forecasts) >= forecast_hours:
                break

        return forecasts

    def _get_weather_description(self, code: int) -> str:
        """
        Converts Open-Meteo weather codes to human-readable descriptions.

        Args:
            code (int): Weather code from Open-Meteo API.

        Returns:
            str: Description of the weather condition.
        """
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return weather_codes.get(code, "Unknown weather condition")

    def display_forecast(self, forecast_hours: int = 24) -> None:
        """
        Displays the weather forecast for the specified number of hours in a readable format.

        Args:
            forecast_hours (int): Number of hours to display the forecast for.

        Raises:
            Exception: If forecast data has not been fetched yet.
        """
        forecasts = self.get_forecast(forecast_hours)
        print(f"Weather Forecast for the Next {forecast_hours} Hours (Location: {self.latitude}, {self.longitude})\n")
        for forecast in forecasts:
            print(f"Time: {forecast['time']}")
            print(f"  Temperature: {forecast['temperature_2m']}°C")
            print(f"  Precipitation: {forecast['precipitation']} mm")
            print(f"  Wind Speed: {forecast['windspeed_10m']} km/h")
            print(f"  Wind Direction: {forecast['winddirection_10m']}°")
            print(f"  Condition: {forecast['weather_description']}")
            print("-" * 40)
