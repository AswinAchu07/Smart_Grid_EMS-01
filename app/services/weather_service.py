"""Live Global Weather and Real-Time Solar PV Generation Service via Open-Meteo API.
"""

from typing import Dict, Any, List, Optional
import time
import math
import requests
import numpy as np

# In-memory short-lived cache: (lat, lon, days) -> (timestamp, data)
_WEATHER_CACHE: Dict[str, Any] = {}
CACHE_TTL_SECONDS = 600.0  # 10 minutes

PRESET_CITIES = [
    {"name": "New Delhi", "country": "India", "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata"},
    {"name": "Bengaluru", "country": "India", "latitude": 12.9716, "longitude": 77.5946, "timezone": "Asia/Kolkata"},
    {"name": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "timezone": "Asia/Kolkata"},
    {"name": "Chennai", "country": "India", "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata"},
    {"name": "San Francisco", "country": "USA", "latitude": 37.7749, "longitude": -122.4194, "timezone": "America/Los_Angeles"},
    {"name": "Berlin", "country": "Germany", "latitude": 52.5200, "longitude": 13.4050, "timezone": "Europe/Berlin"},
    {"name": "London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"},
    {"name": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503, "timezone": "Asia/Tokyo"},
    {"name": "Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093, "timezone": "Australia/Sydney"},
    {"name": "Cairo", "country": "Egypt", "latitude": 30.0444, "longitude": 31.2357, "timezone": "Africa/Cairo"},
]


class WeatherService:
    """Fetches high-resolution numerical weather forecasts and converts them to physical PV power."""

    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

    @classmethod
    def get_preset_cities(cls) -> List[Dict[str, Any]]:
        """Return global smart grid benchmark cities."""
        return PRESET_CITIES

    @classmethod
    def convert_irradiance_to_pv_power(
        cls,
        ghi_w_m2: float,
        temp_c: float,
        pv_capacity_kw: float,
        temp_coefficient: float = 0.004,
        inverter_efficiency: float = 0.96,
        noct_celsius: float = 45.0,
    ) -> float:
        """Physics-based PV conversion with cell temperature derating and inverter efficiency."""
        if ghi_w_m2 <= 1.0 or pv_capacity_kw <= 0.0:
            return 0.0

        # Standard cell temperature approximation: T_cell = T_amb + ((NOCT - 20) / 800) * GHI
        t_cell = temp_c + ((noct_celsius - 20.0) / 800.0) * ghi_w_m2

        # Temperature derating factor
        temp_derating = 1.0 - temp_coefficient * max(-10.0, (t_cell - 25.0))
        temp_derating = max(0.60, min(1.05, temp_derating))

        # Irradiance proportion (Standard Test Conditions = 1000 W/m²)
        raw_power = pv_capacity_kw * (ghi_w_m2 / 1000.0) * temp_derating * inverter_efficiency
        return float(min(pv_capacity_kw * 1.05, max(0.0, raw_power)))

    @classmethod
    def _generate_synthetic_fallback(
        cls,
        latitude: float,
        longitude: float,
        pv_capacity_kw: float,
        forecast_days: int,
    ) -> Dict[str, Any]:
        """High-fidelity synthetic fallback if live internet is unavailable."""
        hours = forecast_days * 24
        times = []
        temperatures = []
        clouds = []
        ghis = []
        pv_powers = []

        curr_time = int(time.time())
        # Base noon hour in local solar time
        for i in range(hours):
            t_sec = curr_time + i * 3600
            iso_time = time.strftime("%Y-%m-%dT%H:00", time.gmtime(t_sec))
            hr = (int(time.strftime("%H", time.gmtime(t_sec))) + int(longitude / 15.0)) % 24

            times.append(iso_time)
            # Temperature curve: diurnal peak at 14:00
            base_temp = 22.0 + 8.0 * math.sin(math.pi * (hr - 8.0) / 12.0)
            temperatures.append(round(base_temp, 1))

            # Cloud cover
            cloud = 20.0 + 15.0 * math.cos(i / 12.0)
            clouds.append(round(max(0.0, min(100.0, cloud)), 1))

            # Solar GHI clear sky with cloud attenuation
            if 6 <= hr <= 19:
                solar_angle = math.sin(math.pi * (hr - 6.0) / 13.0)
                clear_ghi = 950.0 * (solar_angle ** 1.1)
                attenuation = 1.0 - 0.75 * ((cloud / 100.0) ** 3)
                ghi = max(0.0, clear_ghi * attenuation)
            else:
                ghi = 0.0

            ghis.append(round(ghi, 1))
            pv_kw = cls.convert_irradiance_to_pv_power(ghi, base_temp, pv_capacity_kw)
            pv_powers.append(round(pv_kw, 3))

        return {
            "city_name": "Synthesized Coordinates",
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": 150.0,
            "timezone": "UTC",
            "pv_capacity_kw": pv_capacity_kw,
            "current_temp_c": temperatures[0],
            "current_cloud_cover_pct": clouds[0],
            "current_ghi_w_m2": ghis[0],
            "current_estimated_pv_kw": pv_powers[0],
            "hourly": {
                "time": times,
                "temperature_c": temperatures,
                "cloud_cover_pct": clouds,
                "ghi_w_m2": ghis,
                "estimated_solar_kw": pv_powers,
            },
            "source": "High-Fidelity Physical Clear-Sky Fallback Model",
        }

    @classmethod
    def get_live_forecast(
        cls,
        latitude: float,
        longitude: float,
        pv_capacity_kw: float = 5.0,
        forecast_days: int = 2,
    ) -> Dict[str, Any]:
        """Fetch live weather from Open-Meteo or return cached/fallback data."""
        cache_key = f"{round(latitude, 3)}_{round(longitude, 3)}_{forecast_days}"
        now = time.time()

        if cache_key in _WEATHER_CACHE:
            ts, cached_data = _WEATHER_CACHE[cache_key]
            if now - ts < CACHE_TTL_SECONDS:
                # Recalculate PV power for current capacity
                res = dict(cached_data)
                res["pv_capacity_kw"] = pv_capacity_kw
                res["hourly"] = dict(res["hourly"])
                res["hourly"]["estimated_solar_kw"] = [
                    round(cls.convert_irradiance_to_pv_power(ghi, temp, pv_capacity_kw), 3)
                    for ghi, temp in zip(res["hourly"]["ghi_w_m2"], res["hourly"]["temperature_c"])
                ]
                res["current_estimated_pv_kw"] = res["hourly"]["estimated_solar_kw"][0]
                return res

        # Attempt live API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,cloud_cover,direct_normal_irradiance,diffuse_radiation,shortwave_radiation_instant",
            "forecast_days": forecast_days,
            "timezone": "auto",
        }

        try:
            resp = requests.get(cls.OPEN_METEO_URL, params=params, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                hourly_raw = data.get("hourly", {})
                times = hourly_raw.get("time", [])
                temps = hourly_raw.get("temperature_2m", [])
                clouds = hourly_raw.get("cloud_cover", [])
                ghis = hourly_raw.get("shortwave_radiation_instant", [])

                if not ghis or len(ghis) == 0:
                    # Alternative: DNI + Diffuse
                    dnis = hourly_raw.get("direct_normal_irradiance", [])
                    diffs = hourly_raw.get("diffuse_radiation", [])
                    ghis = [float(d + f) for d, f in zip(dnis, diffs)]

                ghis = [round(max(0.0, float(g if g is not None else 0.0)), 1) for g in ghis]
                temps = [round(float(t if t is not None else 20.0), 1) for t in temps]
                clouds = [round(float(c if c is not None else 0.0), 1) for c in clouds]

                pv_powers = [
                    round(cls.convert_irradiance_to_pv_power(ghi, temp, pv_capacity_kw), 3)
                    for ghi, temp in zip(ghis, temps)
                ]

                # Match city name if near preset
                city_name = "Global Coordinates"
                for c in PRESET_CITIES:
                    if abs(c["latitude"] - latitude) < 0.5 and abs(c["longitude"] - longitude) < 0.5:
                        city_name = f"{c['name']}, {c['country']}"
                        break

                result = {
                    "city_name": city_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "elevation_m": float(data.get("elevation", 0.0)),
                    "timezone": str(data.get("timezone", "UTC")),
                    "pv_capacity_kw": pv_capacity_kw,
                    "current_temp_c": temps[0] if temps else 25.0,
                    "current_cloud_cover_pct": clouds[0] if clouds else 0.0,
                    "current_ghi_w_m2": ghis[0] if ghis else 0.0,
                    "current_estimated_pv_kw": pv_powers[0] if pv_powers else 0.0,
                    "hourly": {
                        "time": times,
                        "temperature_c": temps,
                        "cloud_cover_pct": clouds,
                        "ghi_w_m2": ghis,
                        "estimated_solar_kw": pv_powers,
                    },
                    "source": "Open-Meteo Global High-Resolution Weather Model",
                }

                _WEATHER_CACHE[cache_key] = (now, result)
                return result
        except Exception:
            pass

        # If call fails or times out, use reliable physical clear sky fallback
        return cls._generate_synthetic_fallback(
            latitude=latitude,
            longitude=longitude,
            pv_capacity_kw=pv_capacity_kw,
            forecast_days=forecast_days,
        )
