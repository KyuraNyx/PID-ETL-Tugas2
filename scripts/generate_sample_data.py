"""
Script untuk menghasilkan data sensor simulasi untuk keperluan tutorial ETL
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random
import os

def generate_sensor_data(start_date='2024-01-01', days=30, sensors_count=5):
    """
    Generate data sensor simulasi
    
    Parameters:
    - start_date: Tanggal mulai data
    - days: Jumlah hari data
    - sensors_count: Jumlah sensor
    """
    
    # Setup tanggal
    start = datetime.strptime(start_date, '%Y-%m-%d')
    dates = [start + timedelta(hours=x) for x in range(days * 24)]
    
    data = []
    
    for sensor_id in range(1, sensors_count + 1):
        for date in dates:
            # Simulasi data dengan pola dan noise
            hour = date.hour
            
            # Suhu dengan pola harian (lebih panas siang hari)
            base_temp = 25 + 8 * np.sin((hour - 6) * np.pi / 12)
            temperature = base_temp + np.random.normal(0, 2)
            
            # Kelembaban berbanding terbalik dengan suhu
            humidity = 85 - (temperature - 20) * 1.5 + np.random.normal(0, 5)
            humidity = max(20, min(100, humidity))  # Batasi 20-100%
            
            # Tekanan atmosfer dengan variasi kecil
            pressure = 1013.25 + np.random.normal(0, 10)
            
            # Kualitas udara (AQI) - lebih buruk di jam sibuk
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                aqi_base = 80
            else:
                aqi_base = 50
            aqi = aqi_base + np.random.normal(0, 15)
            aqi = max(0, aqi)
            
            # Tambahkan beberapa missing values dan outliers secara acak
            if random.random() < 0.02:  # 2% missing values
                temperature = np.nan
            if random.random() < 0.01:  # 1% outliers
                temperature = temperature * 3
                
            if random.random() < 0.03:  # 3% missing humidity
                humidity = np.nan
                
            data.append({
                'timestamp': date,
                'sensor_id': f'SENSOR_{sensor_id:03d}',
                'location': f'Location_{chr(65 + sensor_id % 5)}',  # A, B, C, D, E
                'temperature_celsius': round(temperature, 2),
                'humidity_percent': round(humidity, 1),
                'pressure_hpa': round(pressure, 2),
                'air_quality_aqi': round(aqi, 1),
                'status': 'active' if random.random() > 0.01 else 'maintenance'
            })
    
    return pd.DataFrame(data)

def add_data_quality_issues(df):
    """
    Tambahkan berbagai masalah kualitas data untuk simulasi realistic
    """
    df_copy = df.copy()
    
    # Tambahkan duplikasi data
    duplicate_indices = np.random.choice(df_copy.index, size=int(len(df_copy) * 0.005), replace=False)
    duplicates = df_copy.loc[duplicate_indices].copy()
    df_with_duplicates = pd.concat([df_copy, duplicates], ignore_index=True)
    
    # Tambahkan inconsistent formatting untuk location
    mask = np.random.random(len(df_with_duplicates)) < 0.1
    df_with_duplicates.loc[mask, 'location'] = df_with_duplicates.loc[mask, 'location'].str.lower()
    
    return df_with_duplicates

def save_data_different_formats(df):
    """
    Simpan data dalam berbagai format untuk demonstrasi extraction
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    base_path = os.path.join(project_root, 'data', 'raw', '')
    os.makedirs(base_path, exist_ok=True)
    
    # CSV format - data utama
    df.to_csv(f"{base_path}sensor_data_main.csv", index=False)
    
    # Excel format - data bulanan
    df_jan = df[df['timestamp'].dt.month == 1]
    df_feb = df[df['timestamp'].dt.month == 2] if not df[df['timestamp'].dt.month == 2].empty else df.head(100)
    
    with pd.ExcelWriter(f"{base_path}sensor_data_monthly.xlsx") as writer:
        df_jan.to_excel(writer, sheet_name='January', index=False)
        df_feb.to_excel(writer, sheet_name='February', index=False)
    
    # JSON format - konfigurasi sensor
    sensor_config = []
    for sensor_id in df['sensor_id'].unique():
        sensor_info = df[df['sensor_id'] == sensor_id].iloc[0]
        config = {
            'sensor_id': sensor_id,
            'location': sensor_info['location'],
            'installation_date': '2024-01-01',
            'calibration_date': '2024-01-15',
            'specifications': {
                'temperature_range': [-10, 50],
                'humidity_range': [0, 100],
                'pressure_range': [950, 1050],
                'accuracy': {
                    'temperature': 0.5,
                    'humidity': 3.0,
                    'pressure': 1.0
                }
            }
        }
        sensor_config.append(config)
    
    with open(f"{base_path}sensor_config.json", 'w') as f:
        json.dump(sensor_config, f, indent=2)
    
    # CSV dengan separator berbeda (semicolon)
    df_sample = df.sample(1000)
    df_sample.to_csv(f"{base_path}sensor_data_semicolon.csv", index=False, sep=';')
    
    print("Data berhasil disimpan dalam berbagai format:")
    print("- sensor_data_main.csv")
    print("- sensor_data_monthly.xlsx")  
    print("- sensor_config.json")
    print("- sensor_data_semicolon.csv")

if __name__ == "__main__":
    print("Generating sensor data...")
    
    # Generate data
    df = generate_sensor_data(start_date='2024-01-01', days=60, sensors_count=10)
    
    # Tambahkan masalah kualitas data
    df_with_issues = add_data_quality_issues(df)
    
    print(f"Generated {len(df_with_issues)} records")
    print(f"Date range: {df_with_issues['timestamp'].min()} to {df_with_issues['timestamp'].max()}")
    print(f"Sensors: {df_with_issues['sensor_id'].nunique()}")
    
    # Simpan dalam berbagai format
    save_data_different_formats(df_with_issues)
    
    print("\nData summary:")
    print(df_with_issues.describe())