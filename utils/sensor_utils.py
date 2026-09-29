"""
Utility functions untuk ETL Sensor Data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def validate_sensor_data(df, sensor_ranges=None):
    """
    Validasi data sensor berdasarkan range yang realistis
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    sensor_ranges : dict
        Dictionary dengan range validasi untuk setiap sensor
        
    Returns:
    --------
    dict : Hasil validasi
    """
    
    if sensor_ranges is None:
        sensor_ranges = {
            'temperature_celsius': (-50, 60),
            'humidity_percent': (0, 100),
            'pressure_hpa': (900, 1100),
            'air_quality_aqi': (0, 500)
        }
    
    validation_results = {}
    
    for column, (min_val, max_val) in sensor_ranges.items():
        if column in df.columns:
            total_records = len(df)
            valid_records = df[(df[column] >= min_val) & (df[column] <= max_val)][column].count()
            invalid_records = total_records - valid_records
            validity_percentage = (valid_records / total_records) * 100
            
            validation_results[column] = {
                'total_records': total_records,
                'valid_records': valid_records,
                'invalid_records': invalid_records,
                'validity_percentage': validity_percentage,
                'range': (min_val, max_val)
            }
    
    return validation_results

def detect_anomalies(df, column, method='iqr', threshold=1.5):
    """
    Deteksi anomali dalam data sensor
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    column : str
        Nama kolom untuk deteksi anomali
    method : str
        Metode deteksi ('iqr', 'zscore', 'isolation')
    threshold : float
        Threshold untuk deteksi anomali
        
    Returns:
    --------
    pandas.Series : Boolean mask untuk anomali
    """
    
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataframe")
    
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        anomalies = (df[column] < lower_bound) | (df[column] > upper_bound)
        
    elif method == 'zscore':
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        anomalies = z_scores > threshold
        
    else:
        raise ValueError("Method must be 'iqr' or 'zscore'")
    
    return anomalies

def calculate_data_quality_score(df):
    """
    Hitung skor kualitas data (0-100)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
        
    Returns:
    --------
    dict : Skor kualitas data dan komponennya
    """
    
    scores = {}
    
    # 1. Completeness (tidak ada missing values)
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells) * 100
    scores['completeness'] = completeness
    
    # 2. Uniqueness (tidak ada duplikasi)
    total_rows = len(df)
    unique_rows = len(df.drop_duplicates())
    uniqueness = (unique_rows / total_rows) * 100
    scores['uniqueness'] = uniqueness
    
    # 3. Validity (data dalam range yang valid)
    sensor_cols = ['temperature_celsius', 'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
    available_sensor_cols = [col for col in sensor_cols if col in df.columns]
    
    if available_sensor_cols:
        validation_results = validate_sensor_data(df)
        validity_scores = [validation_results[col]['validity_percentage'] 
                         for col in available_sensor_cols if col in validation_results]
        validity = np.mean(validity_scores) if validity_scores else 100
    else:
        validity = 100
    
    scores['validity'] = validity
    
    # 4. Consistency (format data konsisten)
    consistency = 100  # Simplified - assume consistent after cleaning
    scores['consistency'] = consistency
    
    # Overall quality score (weighted average)
    weights = {'completeness': 0.3, 'uniqueness': 0.2, 'validity': 0.4, 'consistency': 0.1}
    overall_score = sum(scores[key] * weights[key] for key in scores.keys())
    scores['overall_quality'] = overall_score
    
    return scores

def create_sensor_summary_report(df):
    """
    Buat summary report untuk data sensor
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
        
    Returns:
    --------
    dict : Summary report
    """
    
    report = {}
    
    # Basic info
    report['dataset_info'] = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2,
        'date_range': {
            'start': df['timestamp'].min() if 'timestamp' in df.columns else 'N/A',
            'end': df['timestamp'].max() if 'timestamp' in df.columns else 'N/A'
        }
    }
    
    # Sensor info
    if 'sensor_id' in df.columns:
        report['sensor_info'] = {
            'unique_sensors': df['sensor_id'].nunique(),
            'sensor_ids': df['sensor_id'].unique().tolist(),
            'readings_per_sensor': df['sensor_id'].value_counts().to_dict()
        }
    
    # Location info
    if 'location' in df.columns:
        report['location_info'] = {
            'unique_locations': df['location'].nunique(),
            'locations': df['location'].unique().tolist(),
            'readings_per_location': df['location'].value_counts().to_dict()
        }
    
    # Sensor readings statistics
    sensor_cols = ['temperature_celsius', 'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
    available_sensor_cols = [col for col in sensor_cols if col in df.columns]
    
    if available_sensor_cols:
        report['sensor_statistics'] = {}
        for col in available_sensor_cols:
            report['sensor_statistics'][col] = {
                'count': df[col].count(),
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'median': df[col].median(),
                'missing_values': df[col].isnull().sum()
            }
    
    # Data quality
    quality_scores = calculate_data_quality_score(df)
    report['data_quality'] = quality_scores
    
    return report

def plot_sensor_trends(df, columns=None, figsize=(15, 10)):
    """
    Plot trend data sensor dari waktu ke waktu
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    columns : list
        List kolom sensor untuk di-plot
    figsize : tuple
        Ukuran figure
    """
    
    if 'timestamp' not in df.columns:
        print("❌ Kolom 'timestamp' tidak ditemukan")
        return
    
    if columns is None:
        columns = ['temperature_celsius', 'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
    
    # Filter kolom yang tersedia
    available_columns = [col for col in columns if col in df.columns]
    
    if not available_columns:
        print("❌ Tidak ada kolom sensor yang tersedia untuk plotting")
        return
    
    # Create subplots
    n_plots = len(available_columns)
    fig, axes = plt.subplots(n_plots, 1, figsize=figsize, sharex=True)
    
    if n_plots == 1:
        axes = [axes]
    
    # Plot each sensor
    for i, column in enumerate(available_columns):
        axes[i].plot(df['timestamp'], df[column], alpha=0.7, linewidth=0.8)
        axes[i].set_title(f'{column.replace("_", " ").title()} Over Time')
        axes[i].set_ylabel(column.replace('_', ' ').title())
        axes[i].grid(True, alpha=0.3)
        
        # Add rolling average if enough data points
        if len(df) > 100:
            rolling_mean = df[column].rolling(window=24, center=True).mean()
            axes[i].plot(df['timestamp'], rolling_mean, 
                        color='red', linewidth=2, label='24h Rolling Average')
            axes[i].legend()
    
    plt.xlabel('Timestamp')
    plt.title('Sensor Data Trends', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.show()

def plot_sensor_distributions(df, columns=None, figsize=(15, 10)):
    """
    Plot distribusi data sensor
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    columns : list
        List kolom sensor untuk di-plot
    figsize : tuple
        Ukuran figure
    """
    
    if columns is None:
        columns = ['temperature_celsius', 'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
    
    # Filter kolom yang tersedia
    available_columns = [col for col in columns if col in df.columns]
    
    if not available_columns:
        print("❌ Tidak ada kolom sensor yang tersedia untuk plotting")
        return
    
    # Create subplots
    n_plots = len(available_columns)
    fig, axes = plt.subplots(2, (n_plots + 1) // 2, figsize=figsize)
    axes = axes.flatten() if n_plots > 1 else [axes]
    
    for i, column in enumerate(available_columns):
        # Histogram with KDE
        axes[i].hist(df[column].dropna(), bins=50, alpha=0.7, density=True, color='skyblue')
        
        # Add KDE line
        df[column].dropna().plot.kde(ax=axes[i], color='red', linewidth=2)
        
        axes[i].set_title(f'{column.replace("_", " ").title()} Distribution')
        axes[i].set_xlabel(column.replace('_', ' ').title())
        axes[i].set_ylabel('Density')
        axes[i].grid(True, alpha=0.3)
        
        # Add statistics text
        mean_val = df[column].mean()
        std_val = df[column].std()
        axes[i].axvline(mean_val, color='green', linestyle='--', 
                       label=f'Mean: {mean_val:.2f}')
        axes[i].legend()
    
    # Remove empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    
    plt.suptitle('Sensor Data Distributions', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

def plot_correlation_heatmap(df, figsize=(10, 8)):
    """
    Plot correlation heatmap untuk data sensor
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    figsize : tuple
        Ukuran figure
    """
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    sensor_cols = [col for col in numeric_cols if any(x in col for x in 
                  ['temperature', 'humidity', 'pressure', 'aqi', 'comfort'])]
    
    if len(sensor_cols) < 2:
        print("❌ Butuh minimal 2 kolom numerik untuk correlation heatmap")
        return
    
    # Calculate correlation
    corr_matrix = df[sensor_cols].corr()
    
    # Create heatmap
    plt.figure(figsize=figsize)
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, fmt='.2f', cbar_kws={'label': 'Correlation'})
    plt.title('Sensor Data Correlation Heatmap', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

def export_summary_to_excel(df, filepath, include_charts=False):
    """
    Export summary dan analisis ke Excel
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    filepath : str
        Path file Excel output
    include_charts : bool
        Include charts dalam Excel (requires xlsxwriter)
    """
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Raw data (sample)
        df.head(1000).to_excel(writer, sheet_name='Sample_Data', index=False)
        
        # Summary statistics
        df.describe().to_excel(writer, sheet_name='Statistics')
        
        # Data quality report
        quality_scores = calculate_data_quality_score(df)
        quality_df = pd.DataFrame(list(quality_scores.items()), 
                                columns=['Metric', 'Score'])
        quality_df.to_excel(writer, sheet_name='Data_Quality', index=False)
        
        # Summary report
        report = create_sensor_summary_report(df)
        
        # Dataset info
        if 'dataset_info' in report:
            info_df = pd.DataFrame(list(report['dataset_info'].items()),
                                 columns=['Metric', 'Value'])
            info_df.to_excel(writer, sheet_name='Dataset_Info', index=False)
        
        # Sensor statistics
        if 'sensor_statistics' in report:
            sensor_stats = pd.DataFrame(report['sensor_statistics']).T
            sensor_stats.to_excel(writer, sheet_name='Sensor_Statistics')
        
        # Missing values summary
        missing_summary = pd.DataFrame({
            'Column': df.columns,
            'Missing_Count': [df[col].isnull().sum() for col in df.columns],
            'Missing_Percentage': [df[col].isnull().sum() / len(df) * 100 for col in df.columns]
        })
        missing_summary = missing_summary[missing_summary['Missing_Count'] > 0]
        missing_summary.to_excel(writer, sheet_name='Missing_Values', index=False)
    
    print(f"✅ Summary exported to {filepath}")

# Additional utility functions

def resample_sensor_data(df, freq='H', agg_func='mean'):
    """
    Resample time series sensor data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor dan timestamp
    freq : str
        Frequency untuk resampling ('H', 'D', '15min', etc.)
    agg_func : str atau dict
        Aggregation function
        
    Returns:
    --------
    pandas.DataFrame : Resampled data
    """
    
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame must have 'timestamp' column")
    
    df_copy = df.copy()
    df_copy = df_copy.set_index('timestamp')
    
    # Define aggregation functions for different columns
    if isinstance(agg_func, str):
        agg_dict = {}
        numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            agg_dict[col] = agg_func
    else:
        agg_dict = agg_func
    
    # Resample
    resampled = df_copy.resample(freq).agg(agg_dict)
    resampled = resampled.reset_index()
    
    return resampled

def flag_sensor_maintenance_periods(df, sensors_col='sensor_id', 
                                   temp_col='temperature_celsius',
                                   threshold_hours=6):
    """
    Flag period dimana sensor mungkin dalam maintenance
    berdasarkan data yang tidak berubah
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame dengan data sensor
    sensors_col : str
        Nama kolom sensor ID
    temp_col : str
        Nama kolom temperature untuk deteksi
    threshold_hours : int
        Minimum hours of unchanged data to flag as maintenance
        
    Returns:
    --------
    pandas.DataFrame : DataFrame dengan flag maintenance
    """
    
    df_copy = df.copy()
    df_copy['maintenance_flag'] = False
    
    if all(col in df_copy.columns for col in [sensors_col, temp_col, 'timestamp']):
        for sensor_id in df_copy[sensors_col].unique():
            sensor_data = df_copy[df_copy[sensors_col] == sensor_id].copy()
            sensor_data = sensor_data.sort_values('timestamp')
            
            # Check for unchanged values
            unchanged_mask = sensor_data[temp_col].diff() == 0
            
            # Group consecutive unchanged periods
            groups = (unchanged_mask != unchanged_mask.shift()).cumsum()
            unchanged_groups = sensor_data[unchanged_mask].groupby(groups)
            
            for _, group in unchanged_groups:
                if len(group) >= threshold_hours:  # Assuming hourly data
                    df_copy.loc[group.index, 'maintenance_flag'] = True
    
    return df_copy