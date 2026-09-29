"""
Test Suite untuk ETL Sensor Data Pipeline
"""

import unittest
import pandas as pd
import numpy as np
import os
import tempfile
import json
from datetime import datetime, timedelta

# Import modules to test
import sys
sys.path.append('..')
from scripts.etl_pipeline import SensorETLPipeline
from utils.sensor_utils import (
    validate_sensor_data,
    detect_anomalies,
    calculate_data_quality_score
)

class TestSensorDataGeneration(unittest.TestCase):
    """Test sample data generation"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def test_generate_sample_data(self):
        """Test sample data generation"""
        from scripts.generate_sample_data import generate_sensor_data
        
        df = generate_sensor_data(start_date='2024-01-01', days=7, sensors_count=3)
        
        # Test basic properties
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
        # Test required columns
        required_cols = ['timestamp', 'sensor_id', 'temperature_celsius', 
                        'humidity_percent', 'pressure_hpa', 'air_quality_aqi']
        for col in required_cols:
            self.assertIn(col, df.columns)
        
        # Test data ranges (allowing for intentional outliers/missing values in simulated data)
        valid_temp = df['temperature_celsius'].dropna()
        self.assertGreater((valid_temp.between(-50, 60)).mean(), 0.95)
        valid_hum = df['humidity_percent'].dropna()
        self.assertGreater((valid_hum.between(0, 100)).mean(), 0.95)
        valid_press = df['pressure_hpa'].dropna()
        self.assertGreater((valid_press.between(900, 1100)).mean(), 0.95)

class TestDataValidation(unittest.TestCase):
    """Test data validation functions"""
    
    def setUp(self):
        """Create test dataframe"""
        self.test_data = pd.DataFrame({
            'temperature_celsius': [20, 25, 30, 100, 35],  # 100 is outlier
            'humidity_percent': [50, 60, 70, 80, 90],
            'pressure_hpa': [1010, 1015, 1020, 1025, 1030],
            'air_quality_aqi': [45, 55, 65, 75, 85]
        })
    
    def test_validate_sensor_data(self):
        """Test sensor data validation"""
        results = validate_sensor_data(self.test_data)
        
        # Check that validation results exist
        self.assertIn('temperature_celsius', results)
        self.assertIn('humidity_percent', results)
        
        # Check temperature validation (should catch outlier)
        temp_result = results['temperature_celsius']
        self.assertEqual(temp_result['total_records'], 5)
        self.assertLess(temp_result['validity_percentage'], 100)  # Due to outlier
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        anomalies = detect_anomalies(self.test_data, 'temperature_celsius', method='iqr')
        
        self.assertIsInstance(anomalies, pd.Series)
        self.assertEqual(len(anomalies), len(self.test_data))
        self.assertTrue(anomalies.dtype == bool)
    
    def test_data_quality_score(self):
        """Test data quality scoring"""
        scores = calculate_data_quality_score(self.test_data)
        
        # Check required score components
        required_scores = ['completeness', 'uniqueness', 'validity', 'overall_quality']
        for score in required_scores:
            self.assertIn(score, scores)
            self.assertIsInstance(scores[score], (int, float))
            self.assertGreaterEqual(scores[score], 0)
            self.assertLessEqual(scores[score], 100)

class TestETLPipeline(unittest.TestCase):
    """Test ETL Pipeline functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test data files
        test_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'sensor_id': ['SENSOR_001'] * 50 + ['SENSOR_002'] * 50,
            'location': ['Location_A'] * 100,
            'temperature_celsius': np.random.normal(25, 5, 100),
            'humidity_percent': np.random.normal(60, 10, 100),
            'pressure_hpa': np.random.normal(1013, 10, 100),
            'air_quality_aqi': np.random.normal(50, 15, 100),
            'status': ['active'] * 95 + ['maintenance'] * 5
        })
        
        # Save test CSV
        self.test_csv_path = os.path.join(self.temp_dir, 'test_sensor_data.csv')
        test_df.to_csv(self.test_csv_path, index=False)
        
        # Create test config
        self.test_config = {
            'input_paths': {
                'csv_main': self.test_csv_path
            },
            'output_path': self.temp_dir,
            'processing': {
                'remove_duplicates': True,
                'handle_missing': True,
                'feature_engineering': True,
                'normalize_data': True
            },
            'export_formats': ['csv']
        }
        
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = SensorETLPipeline(self.config_path)
        
        self.assertIsInstance(pipeline, SensorETLPipeline)
        self.assertEqual(pipeline.config['output_path'], self.temp_dir)
    
    def test_extract_data(self):
        """Test data extraction"""
        pipeline = SensorETLPipeline(self.config_path)
        pipeline.extract_data()
        
        self.assertIsNotNone(pipeline.raw_data)
        self.assertIsInstance(pipeline.raw_data, pd.DataFrame)
        self.assertGreater(len(pipeline.raw_data), 0)
    
    def test_transform_data(self):
        """Test data transformation"""
        pipeline = SensorETLPipeline(self.config_path)
        pipeline.extract_data()
        pipeline.transform_data()
        
        self.assertIsNotNone(pipeline.processed_data)
        self.assertIsInstance(pipeline.processed_data, pd.DataFrame)
        
        # Check if new features were created
        processed_cols = pipeline.processed_data.columns
        feature_indicators = ['fahrenheit', 'kelvin', 'normalized', 'time_period']
        
        found_features = any(any(indicator in col for col in processed_cols) 
                           for indicator in feature_indicators)
        self.assertTrue(found_features, "No engineered features found")
    
    def test_full_pipeline(self):
        """Test complete ETL pipeline"""
        pipeline = SensorETLPipeline(self.config_path)
        
        # Run pipeline
        success = pipeline.run_pipeline()
        self.assertTrue(success)
        
        # Check output files
        output_files = os.listdir(self.temp_dir)
        csv_files = [f for f in output_files if f.endswith('.csv') and 'processed' in f]
        self.assertGreater(len(csv_files), 0, "No processed CSV files found")

class TestDataTransformations(unittest.TestCase):
    """Test specific data transformation functions"""
    
    def setUp(self):
        """Create test dataframe with missing values"""
        self.df_with_missing = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='h'),
            'sensor_id': ['SENSOR_001'] * 10,
            'temperature_celsius': [20, 21, np.nan, 23, 24, np.nan, 26, 27, 28, 29],
            'humidity_percent': [50, 55, 60, 65, np.nan, 75, 80, 85, 90, 95]
        })
    
    def test_missing_value_handling(self):
        """Test missing value imputation"""
        original_missing = self.df_with_missing.isnull().sum().sum()
        
        # Forward fill
        df_filled = self.df_with_missing.copy()
        df_filled['temperature_celsius'] = df_filled['temperature_celsius'].ffill()
        df_filled['humidity_percent'] = df_filled['humidity_percent'].ffill()
        
        final_missing = df_filled.isnull().sum().sum()
        self.assertLess(final_missing, original_missing)
    
    def test_feature_engineering(self):
        """Test feature engineering"""
        df = self.df_with_missing.dropna().copy()
        
        # Add temperature conversions
        df['temperature_fahrenheit'] = (df['temperature_celsius'] * 9/5) + 32
        df['temperature_kelvin'] = df['temperature_celsius'] + 273.15
        
        # Test conversions
        self.assertTrue((df['temperature_fahrenheit'] > df['temperature_celsius']).all())
        self.assertTrue((df['temperature_kelvin'] > df['temperature_celsius']).all())
        
        # Test reasonable ranges
        self.assertTrue(df['temperature_fahrenheit'].between(32, 200).all())
        self.assertTrue(df['temperature_kelvin'].between(200, 400).all())

class TestPerformance(unittest.TestCase):
    """Test pipeline performance"""
    
    def test_processing_time(self):
        """Test processing time for different dataset sizes"""
        import time
        
        # Small dataset
        small_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'sensor_id': ['SENSOR_001'] * 100,
            'temperature_celsius': np.random.normal(25, 5, 100),
            'humidity_percent': np.random.normal(60, 10, 100)
        })
        
        start_time = time.time()
        scores = calculate_data_quality_score(small_df)
        processing_time = time.time() - start_time
        
        # Should process small dataset quickly (< 1 second)
        self.assertLess(processing_time, 1.0)
        self.assertIsInstance(scores, dict)

    def test_memory_usage(self):
        """Test memory efficiency"""
        df = pd.DataFrame({
            'sensor_id': ['SENSOR_001'] * 1000,
            'temperature_celsius': np.random.normal(25, 5, 1000),
            'humidity_percent': np.random.normal(60, 10, 1000)
        })
        
        # Test memory usage before and after optimization
        memory_before = df.memory_usage(deep=True).sum()
        
        # Optimize data types
        df['sensor_id'] = df['sensor_id'].astype('category')
        df['temperature_celsius'] = pd.to_numeric(df['temperature_celsius'], downcast='float')
        df['humidity_percent'] = pd.to_numeric(df['humidity_percent'], downcast='float')
        
        memory_after = df.memory_usage(deep=True).sum()
        
        # Should use less memory after optimization
        self.assertLess(memory_after, memory_before)

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    test_cases = [
        TestSensorDataGeneration,
        TestDataValidation,
        TestETLPipeline,
        TestDataTransformations,
        TestPerformance
    ]
    
    for test_case in test_cases:
        tests = loader.loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if (len(result.failures) + len(result.errors)) == 0 else 1
    exit(exit_code)