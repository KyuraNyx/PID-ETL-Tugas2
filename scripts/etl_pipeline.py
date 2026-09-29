"""
ETL Pipeline Script untuk Data Sensor
Automated pipeline untuk Extract, Transform, Load data sensor
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings('ignore')

class SensorETLPipeline:
    """
    Kelas untuk menjalankan ETL Pipeline pada data sensor IoT
    """
    
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.raw_data = None
        self.processed_data = None
        self.processing_log = []
        
    def _load_config(self, config_path):
        """Load konfigurasi ETL"""
        default_config = {
            'input_paths': {
                'csv_main': 'data/raw/sensor_data_main.csv',
                'excel': 'data/raw/sensor_data_monthly.xlsx',
                'json_config': 'data/raw/sensor_config.json'
            },
            'output_path': 'data/output',
            'processing': {
                'remove_duplicates': True,
                'handle_missing': True,
                'feature_engineering': True,
                'normalize_data': True
            },
            'export_formats': ['csv', 'excel', 'json', 'parquet'],
            'aggregations': ['hourly', 'daily', 'location']
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
            default_config.update(custom_config)
            
        return default_config
    
    def log_step(self, message):
        """Logging untuk tracking proses ETL"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.processing_log.append(log_entry)
        print(log_entry)
    
    def extract_data(self):
        """
        Extract data dari berbagai sumber
        """
        self.log_step("🔄 Starting data extraction...")
        
        data_frames = []
        
        # Extract CSV
        try:
            csv_path = self.config['input_paths']['csv_main']
            if os.path.exists(csv_path):
                df_csv = pd.read_csv(csv_path)
                data_frames.append(df_csv)
                self.log_step(f"✅ CSV loaded: {df_csv.shape[0]} rows")
            else:
                self.log_step(f"⚠️ CSV file not found: {csv_path}")
        except Exception as e:
            self.log_step(f"❌ Error loading CSV: {str(e)}")
        
        # Extract Excel
        try:
            excel_path = self.config['input_paths']['excel']
            if os.path.exists(excel_path):
                excel_file = pd.ExcelFile(excel_path)
                for sheet_name in excel_file.sheet_names:
                    df_sheet = pd.read_excel(excel_path, sheet_name=sheet_name)
                    data_frames.append(df_sheet)
                self.log_step(f"✅ Excel loaded: {len(excel_file.sheet_names)} sheets")
        except Exception as e:
            self.log_step(f"❌ Error loading Excel: {str(e)}")
        
        # Combine all dataframes
        if data_frames:
            self.raw_data = pd.concat(data_frames, ignore_index=True)
            self.log_step(f"📊 Combined dataset: {self.raw_data.shape}")
        else:
            raise ValueError("No data could be extracted from sources")
    
    def transform_data(self):
        """
        Transform dan clean data
        """
        self.log_step("🔧 Starting data transformation...")
        
        if self.raw_data is None:
            raise ValueError("No raw data available for transformation")
        
        df = self.raw_data.copy()
        
        # 1. Remove duplicates
        if self.config['processing']['remove_duplicates']:
            before_dup = len(df)
            df = df.drop_duplicates()
            removed_dup = before_dup - len(df)
            self.log_step(f"🔁 Removed {removed_dup} duplicate records")
        
        # 2. Standardize column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        self.log_step("📝 Column names standardized")
        
        # 3. Handle timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Extract time features
            df['year'] = df['timestamp'].dt.year
            df['month'] = df['timestamp'].dt.month
            df['day'] = df['timestamp'].dt.day
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
            
            # Time periods
            df['time_period'] = pd.cut(df['hour'], 
                                     bins=[0, 6, 12, 18, 24], 
                                     labels=['Night', 'Morning', 'Afternoon', 'Evening'],
                                     include_lowest=True)
            
            self.log_step("📅 Time features engineered")
        
        # 4. Feature engineering
        if self.config['processing']['feature_engineering']:
            self._engineer_features(df)
        
        # 5. Handle missing values
        if self.config['processing']['handle_missing']:
            df = self._handle_missing_values(df)
        
        # 6. Data normalization
        if self.config['processing']['normalize_data']:
            numeric_cols = ['temperature_celsius', 'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
            available_numeric = [col for col in numeric_cols if col in df.columns]
            
            for col in available_numeric:
                col_min = df[col].min()
                col_max = df[col].max()
                df[f'{col}_normalized'] = (df[col] - col_min) / (col_max - col_min)
            
            self.log_step(f"📊 Normalized {len(available_numeric)} numeric columns")
        
        self.processed_data = df
        self.log_step(f"✅ Transformation completed: {df.shape}")
    
    def _engineer_features(self, df):
        """
        Feature engineering untuk data sensor
        """
        # Temperature conversions
        if 'temperature_celsius' in df.columns:
            df['temperature_fahrenheit'] = (df['temperature_celsius'] * 9/5) + 32
            df['temperature_kelvin'] = df['temperature_celsius'] + 273.15
        
        # Heat index (simplified)
        if all(col in df.columns for col in ['temperature_fahrenheit', 'humidity_percent']):
            temp_f = df['temperature_fahrenheit']
            rh = df['humidity_percent']
            
            heat_index = np.where(
                temp_f >= 80,
                -42.379 + 2.04901523*temp_f + 10.14333127*rh - 0.22475541*temp_f*rh,
                temp_f
            )
            df['heat_index_f'] = heat_index
            df['heat_index_c'] = (heat_index - 32) * 5/9
        
        # Air quality categories
        if 'air_quality_aqi' in df.columns:
            def categorize_aqi(aqi):
                if pd.isna(aqi):
                    return 'Unknown'
                elif aqi <= 50:
                    return 'Good'
                elif aqi <= 100:
                    return 'Moderate'
                elif aqi <= 150:
                    return 'Unhealthy for Sensitive Groups'
                elif aqi <= 200:
                    return 'Unhealthy'
                else:
                    return 'Very Unhealthy'
            
            df['aqi_category'] = df['air_quality_aqi'].apply(categorize_aqi)
        
        # Comfort index
        if all(col in df.columns for col in ['temperature_celsius', 'humidity_percent']):
            def comfort_score(temp, humidity):
                if pd.isna(temp) or pd.isna(humidity):
                    return np.nan
                
                temp_score = 100 - abs(temp - 22) * 5
                humidity_score = 100 - abs(humidity - 50) * 2
                comfort = (temp_score + humidity_score) / 2
                return max(0, min(100, comfort))
            
            df['comfort_index'] = df.apply(
                lambda row: comfort_score(row['temperature_celsius'], row['humidity_percent']), 
                axis=1
            )
        
        self.log_step("🔧 Feature engineering completed")
    
    def _handle_missing_values(self, df):
        """
        Handle missing values menggunakan berbagai strategi
        """
        initial_missing = df.isnull().sum().sum()
        
        # Forward fill untuk time series
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        sensor_cols = [col for col in numeric_cols if any(x in col for x in ['temperature', 'humidity', 'pressure', 'aqi'])]
        
        if 'sensor_id' in df.columns:
            for col in sensor_cols:
                df[col] = df.groupby('sensor_id')[col].ffill()
        
        # Interpolation
        for col in sensor_cols:
            if 'sensor_id' in df.columns:
                df[col] = df.groupby('sensor_id')[col].transform(
                    lambda x: x.interpolate(method='linear')
                )
            else:
                df[col] = df[col].interpolate(method='linear')
        
        # Statistical imputation
        for col in sensor_cols:
            if df[col].isnull().sum() > 0:
                if 'location' in df.columns:
                    location_means = df.groupby('location')[col].mean()
                    df[col] = df[col].fillna(df['location'].map(location_means))
                else:
                    df[col] = df[col].fillna(df[col].mean())
        
        # Categorical missing values
        if 'status' in df.columns:
            df['status'] = df['status'].fillna('active')
        
        final_missing = df.isnull().sum().sum()
        handled = initial_missing - final_missing
        self.log_step(f"🔍 Handled {handled} missing values")
        
        return df
    
    def create_aggregations(self):
        """
        Buat agregasi data
        """
        if self.processed_data is None:
            self.log_step("⚠️ No processed data available for aggregation")
            return
        
        self.log_step("📊 Creating data aggregations...")
        
        aggregations = {}
        df = self.processed_data
        
        # Hourly aggregation
        if 'hourly' in self.config['aggregations'] and 'timestamp' in df.columns:
            hourly = df.groupby(df['timestamp'].dt.floor('h')).agg({
                'temperature_celsius': ['mean', 'min', 'max', 'std'],
                'humidity_percent': ['mean', 'min', 'max'],
                'pressure_hpa': 'mean',
                'air_quality_aqi': 'mean'
            }).round(2)
            hourly.columns = ['_'.join(col).strip() for col in hourly.columns]
            aggregations['hourly'] = hourly.reset_index()
            self.log_step(f"⏰ Hourly aggregation: {len(hourly)} records")
        
        # Daily aggregation
        if 'daily' in self.config['aggregations'] and 'timestamp' in df.columns:
            daily = df.groupby(df['timestamp'].dt.date).agg({
                'temperature_celsius': ['mean', 'min', 'max'],
                'humidity_percent': ['mean', 'min', 'max'],
                'air_quality_aqi': ['mean', 'max']
            }).round(2)
            daily.columns = ['_'.join(col).strip() for col in daily.columns]
            aggregations['daily'] = daily.reset_index()
            self.log_step(f"📅 Daily aggregation: {len(daily)} records")
        
        # Location aggregation
        if 'location' in self.config['aggregations'] and 'location' in df.columns:
            location = df.groupby('location').agg({
                'temperature_celsius': ['count', 'mean', 'std'],
                'humidity_percent': ['mean', 'std'],
                'air_quality_aqi': ['mean', 'max']
            }).round(2)
            location.columns = ['_'.join(col).strip() for col in location.columns]
            aggregations['location'] = location.reset_index()
            self.log_step(f"🗺️ Location aggregation: {len(location)} records")
        
        self.aggregations = aggregations
    
    def load_data(self):
        """
        Load/Export data ke berbagai format
        """
        if self.processed_data is None:
            raise ValueError("No processed data available for loading")
        
        self.log_step("💾 Starting data loading...")
        
        # Create output directory
        output_dir = Path(self.config['output_path'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export processed data
        if 'csv' in self.config['export_formats']:
            csv_file = output_dir / f"processed_sensor_data_{timestamp}.csv"
            self.processed_data.to_csv(csv_file, index=False)
            self.log_step(f"📄 CSV exported: {csv_file}")
        
        if 'excel' in self.config['export_formats']:
            excel_file = output_dir / f"sensor_analysis_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                self.processed_data.to_excel(writer, sheet_name='Processed_Data', index=False)
                self.processed_data.describe().to_excel(writer, sheet_name='Summary_Stats')
                
                # Add aggregations if available
                if hasattr(self, 'aggregations'):
                    for agg_name, agg_data in self.aggregations.items():
                        agg_data.to_excel(writer, sheet_name=f'{agg_name.title()}_Agg', index=False)
            
            self.log_step(f"📊 Excel exported: {excel_file}")
        
        if 'json' in self.config['export_formats']:
            json_file = output_dir / f"processed_sensor_data_{timestamp}.json"
            
            # Convert datetime for JSON
            df_json = self.processed_data.copy()
            for col in df_json.columns:
                if df_json[col].dtype == 'datetime64[ns]':
                    df_json[col] = df_json[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                elif pd.api.types.is_categorical_dtype(df_json[col]):
                    df_json[col] = df_json[col].astype(str)
            
            df_json.to_json(json_file, orient='records', indent=2)
            self.log_step(f"🔗 JSON exported: {json_file}")
        
        if 'parquet' in self.config['export_formats']:
            try:
                parquet_file = output_dir / f"processed_sensor_data_{timestamp}.parquet"
                self.processed_data.to_parquet(parquet_file, index=False)
                self.log_step(f"🗜️ Parquet exported: {parquet_file}")
            except ImportError:
                self.log_step("⚠️ Parquet export requires 'pyarrow'. Install with: pip install pyarrow")
        
        # Export processing log
        log_file = output_dir / f"processing_log_{timestamp}.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.processing_log))
        self.log_step(f"📝 Processing log saved: {log_file}")
    
    def run_pipeline(self):
        """
        Jalankan complete ETL pipeline
        """
        try:
            self.log_step("🚀 Starting ETL Pipeline...")
            
            # Extract
            self.extract_data()
            
            # Transform
            self.transform_data()
            
            # Create aggregations
            self.create_aggregations()
            
            # Load
            self.load_data()
            
            self.log_step("🎉 ETL Pipeline completed successfully!")
            
            # Final summary
            self.log_step(f"📊 Final dataset: {self.processed_data.shape}")
            self.log_step(f"🏷️ Features created: {len(self.processed_data.columns)}")
            
            return True
            
        except Exception as e:
            self.log_step(f"❌ ETL Pipeline failed: {str(e)}")
            raise

def main():
    """
    Main function untuk menjalankan ETL pipeline
    """
    print("🚀 Sensor Data ETL Pipeline")
    print("=" * 40)
    
    # Initialize pipeline
    pipeline = SensorETLPipeline()
    
    # Run pipeline
    try:
        success = pipeline.run_pipeline()
        
        if success:
            print("\\n✅ ETL Pipeline berhasil diselesaikan!")
            print("📁 Check folder 'data/output' untuk hasil processing")
        
    except Exception as e:
        print(f"\\n❌ ETL Pipeline gagal: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()