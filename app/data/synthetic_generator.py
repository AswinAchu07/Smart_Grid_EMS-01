"""High-fidelity synthetic dataset generator for Smart Grid Solar PV & Load forecasting.

Generates physically grounded hourly time-series data:
- Solar irradiance (clear-sky model + cloud attenuation)
- Solar PV power (rated capacity, temperature coefficient, inverter efficiency)
- Multi-component electricity load (base, morning/evening peaks, weekend profiles, HVAC cooling/heating)
- Weather parameters (temperature, humidity, wind speed, cloud cover)
- Time-of-Use (TOU) electricity pricing
"""

import numpy as np
import pandas as pd
from typing import Optional


def generate_synthetic_dataset(
    start_date: str = "2024-01-01 00:00:00",
    periods: int = 8760,  # 1 full year of hourly data
    pv_capacity_kw: float = 6.0,
    seed: int = 42,
    save_path: Optional[str] = None,
) -> pd.DataFrame:
    """Generate a realistic hourly dataset for solar PV, load, weather, and tariffs.

    Parameters
    ----------
    start_date : str
        Start timestamp string (format YYYY-MM-DD HH:MM:SS)
    periods : int
        Number of hourly intervals to generate (default: 8760)
    pv_capacity_kw : float
        Peak rated PV array capacity in kW (default: 6.0 kW)
    seed : int
        Random seed for reproducibility
    save_path : Optional[str]
        File path to save the generated CSV

    Returns
    -------
    pd.DataFrame
        Clean DataFrame with timestamps, weather, solar generation, load, and tariffs.
    """
    np.random.seed(seed)
    timestamps = pd.date_range(start=start_date, periods=periods, freq="h")
    df = pd.DataFrame({"timestamp": timestamps})

    # Temporal properties
    hour = df["timestamp"].dt.hour.values
    day_of_year = df["timestamp"].dt.dayofyear.values
    weekday = df["timestamp"].dt.weekday.values
    is_weekend = (weekday >= 5).astype(int)

    # 1. Weather Modeling
    # Ambient Temperature: seasonal sinusoidal wave + diurnal wave + random noise
    seasonal_temp = 20.0 + 10.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
    diurnal_temp = 6.0 * np.sin(2 * np.pi * (hour - 9) / 24.0)
    temp_noise = np.random.normal(0, 1.5, size=periods)
    temperature = np.clip(seasonal_temp + diurnal_temp + temp_noise, -5.0, 45.0)

    # Cloud cover: Autoregressive noise (0.0 = clear sky, 1.0 = overcast)
    cloud_noise = np.random.beta(0.5, 1.5, size=periods)
    # Smooth cloud cover with a rolling window for realistic cloud fronts
    cloud_cover = pd.Series(cloud_noise).rolling(window=4, min_periods=1).mean().values
    cloud_cover = np.clip(cloud_cover, 0.0, 0.95)

    # Relative Humidity (%): Inversely correlated with temperature + noise
    base_humidity = 85.0 - (temperature - temperature.min()) / (temperature.max() - temperature.min() + 1e-5) * 45.0
    humidity = np.clip(base_humidity + np.random.normal(0, 5.0, size=periods) + cloud_cover * 20.0, 20.0, 98.0)

    # Wind Speed (m/s): Weibull-like distribution
    wind_speed = np.clip(np.random.weibull(2.0, size=periods) * 3.5, 0.2, 22.0)

    # 2. Solar Irradiance (GHI in W/m²) & Solar PV Generation (kW)
    # Solar elevation angle approximation (positive only between sunrise and sunset ~6am to 6pm)
    solar_hour_angle = np.pi * (hour - 12.0) / 12.0
    declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365.0))
    lat_rad = np.radians(35.0)  # Mid-latitude (~35°N)
    dec_rad = np.radians(declination)

    sin_elevation = np.sin(lat_rad) * np.sin(dec_rad) + np.cos(lat_rad) * np.cos(dec_rad) * np.cos(solar_hour_angle)
    elevation = np.arcsin(np.clip(sin_elevation, -1.0, 1.0))
    elevation_deg = np.degrees(elevation)

    # Clear Sky Irradiance (GHI)
    clear_sky_ghi = np.maximum(0.0, 1050.0 * np.sin(np.maximum(0.0, elevation)))
    # Apply cloud attenuation: GHI = ClearSky * (1 - 0.75 * cloud_cover^2)
    ghi = clear_sky_ghi * (1.0 - 0.75 * (cloud_cover ** 2.0))
    # Night hours are strictly zero
    ghi[elevation_deg <= 2.0] = 0.0

    # Solar PV Power (kW)
    # P_pv = P_rated * (GHI / 1000) * [1 - gamma * (T_cell - 25)] * eta_inv
    # T_cell ≈ T_ambient + (NOCT - 20)/800 * GHI
    t_cell = temperature + (45.0 - 20.0) / 800.0 * ghi
    temp_derate = 1.0 - 0.004 * np.maximum(0.0, t_cell - 25.0)
    inverter_eff = 0.96

    solar_power_kw = pv_capacity_kw * (ghi / 1000.0) * temp_derate * inverter_eff
    solar_power_kw = np.clip(solar_power_kw, 0.0, pv_capacity_kw * 1.05)
    # Strict night zeroing
    solar_power_kw[elevation_deg <= 2.0] = 0.0

    # 3. Electricity Load Modeling (kW)
    # Typical smart household / community microgrid load
    base_load = 1.2  # Always-on appliances

    # Diurnal peak shapes
    # Morning peak: 07:00 - 09:00 (cooking, water heating, wake-up)
    morning_peak = 2.2 * np.exp(-((hour - 7.5) ** 2) / (2 * 1.2 ** 2))
    # Evening peak: 18:00 - 21:30 (lighting, electronics, cooking, EV/appliances)
    evening_peak = 3.8 * np.exp(-((hour - 19.5) ** 2) / (2 * 1.8 ** 2))
    # Midday load (higher on weekends)
    midday_load = (0.8 + 0.9 * is_weekend) * np.exp(-((hour - 13.0) ** 2) / (2 * 2.5 ** 2))

    # Weekend shift: morning peak happens ~1.5 hours later
    weekend_morning = 2.0 * np.exp(-((hour - 9.0) ** 2) / (2 * 1.5 ** 2)) * is_weekend
    morning_component = np.where(is_weekend == 1, weekend_morning, morning_peak)

    # HVAC Temperature Sensitivity:
    # Cooling load when Temp > 24°C; Heating load when Temp < 15°C
    cooling_load = 0.12 * np.maximum(0.0, temperature - 24.0) ** 1.3
    heating_load = 0.10 * np.maximum(0.0, 15.0 - temperature) ** 1.2

    # Aggregate total load with realistic stochastic noise
    load_noise = np.random.normal(0, 0.25, size=periods)
    load_kw = base_load + morning_component + evening_peak + midday_load + cooling_load + heating_load + load_noise
    load_kw = np.clip(load_kw, 0.5, 12.0)  # Non-negative, bounded

    # 4. Electricity Tariffs ($/kWh)
    # Time-of-Use (TOU) Structure:
    # Peak (16:00 - 21:00 on weekdays): $0.35/kWh
    # Standard (07:00 - 16:00, 21:00 - 23:00 on weekdays; 12:00 - 20:00 on weekends): $0.18/kWh
    # Off-peak (all other hours): $0.10/kWh
    # Feed-in Tariff (solar export): $0.08/kWh
    price_import = np.full(periods, 0.10)  # Default off-peak

    # Standard hours
    std_mask_weekday = (is_weekend == 0) & (((hour >= 7) & (hour < 16)) | ((hour >= 21) & (hour < 23)))
    std_mask_weekend = (is_weekend == 1) & ((hour >= 11) & (hour < 20))
    price_import[std_mask_weekday | std_mask_weekend] = 0.18

    # Peak hours
    peak_mask = (is_weekend == 0) & (hour >= 16) & (hour < 21)
    price_import[peak_mask] = 0.35

    price_export = np.full(periods, 0.08)

    # Assemble final DataFrame
    df["temperature_c"] = np.round(temperature, 2)
    df["humidity_pct"] = np.round(humidity, 2)
    df["wind_speed_ms"] = np.round(wind_speed, 2)
    df["cloud_cover"] = np.round(cloud_cover, 3)
    df["irradiance_ghi_wm2"] = np.round(ghi, 2)
    df["solar_power_kw"] = np.round(solar_power_kw, 3)
    df["load_power_kw"] = np.round(load_kw, 3)
    df["grid_import_price"] = np.round(price_import, 4)
    df["grid_export_price"] = np.round(price_export, 4)

    if save_path:
        df.to_csv(save_path, index=False)

    return df
