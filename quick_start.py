#!/usr/bin/env python3
"""
Quick Start Script untuk Hands-On ETL Sensor Data
Jalankan script ini untuk setup dan demo lengkap
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print banner informasi"""
    print("=" * 60)
    print("🚀 HANDS-ON ETL SENSOR DATA DENGAN PANDAS")
    print("=" * 60)
    print("Script ini akan:")
    print("1. 🔧 Setup environment dan dependencies")
    print("2. 📊 Generate sample sensor data")
    print("3. 🔄 Menjalankan ETL pipeline")
    print("4. 📁 Membuat output files")
    print("=" * 60)

def check_requirements():
    """Check apakah requirements sudah terinstall"""
    print("\\n🔍 Checking requirements...")
    
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 
        'seaborn', 'openpyxl', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install dengan: pip install " + " ".join(missing_packages))
        return False
    
    print("\\n✅ All requirements satisfied!")
    return True

def setup_directories():
    """Setup directory structure"""
    print("\\n📁 Setting up directories...")
    
    directories = [
        'data/raw',
        'data/processed', 
        'data/output',
        'notebooks',
        'scripts',
        'utils',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")

def generate_sample_data():
    """Generate sample sensor data"""
    print("\\n📊 Generating sample sensor data...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/generate_sample_data.py'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Sample data generated successfully!")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating data: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    
    except FileNotFoundError:
        print("❌ generate_sample_data.py not found")
        print("Make sure you're running from the project root directory")
        return False

def run_etl_pipeline():
    """Run the ETL pipeline"""
    print("\\n🔄 Running ETL Pipeline...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/etl_pipeline.py'
        ], capture_output=True, text=True, check=True)
        
        print("✅ ETL Pipeline completed successfully!")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ETL Pipeline failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    
    except FileNotFoundError:
        print("❌ etl_pipeline.py not found")
        return False

def show_results():
    """Show hasil processing"""
    print("\\n📋 PROCESSING RESULTS")
    print("=" * 30)
    
    # Check output directory
    output_dir = Path('data/output')
    if output_dir.exists():
        output_files = list(output_dir.glob('*'))
        if output_files:
            print(f"📁 Output files generated: {len(output_files)}")
            for file in output_files[:10]:  # Show first 10 files
                size_mb = file.stat().st_size / (1024*1024)
                print(f"   📄 {file.name} ({size_mb:.2f} MB)")
            
            if len(output_files) > 10:
                print(f"   ... and {len(output_files) - 10} more files")
        else:
            print("❌ No output files found")
    else:
        print("❌ Output directory not found")
    
    # Check raw data
    raw_dir = Path('data/raw')
    if raw_dir.exists():
        raw_files = list(raw_dir.glob('*'))
        print(f"\\n📊 Raw data files: {len(raw_files)}")
        for file in raw_files:
            size_mb = file.stat().st_size / (1024*1024)
            print(f"   📄 {file.name} ({size_mb:.2f} MB)")

def show_next_steps():
    """Show panduan next steps"""
    print("\\n🎯 NEXT STEPS")
    print("=" * 15)
    print("1. 📓 Explore Jupyter Notebook:")
    print("   jupyter notebook 01_ETL_Sensor_Data_Tutorial.ipynb")
    print("\\n2. 📊 Analyze output files:")
    print("   - CSV: data/output/processed_sensor_data_*.csv")
    print("   - Excel: data/output/sensor_analysis_*.xlsx") 
    print("   - JSON: data/output/processed_sensor_data_*.json")
    print("\\n3. 🔧 Customize ETL pipeline:")
    print("   - Edit config/etl_config.json")
    print("   - Modify scripts/etl_pipeline.py")
    print("\\n4. 📈 Create visualizations:")
    print("   - Use utils/sensor_utils.py functions")
    print("   - Create custom analysis notebooks")
    print("\\n5. 🚀 Deploy to production:")
    print("   - Schedule ETL pipeline")
    print("   - Add data quality monitoring")
    print("   - Integrate with databases")

def main():
    """Main function"""
    print_banner()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print(f"\\n📂 Working directory: {os.getcwd()}")
    
    try:
        # Step 1: Check requirements
        if not check_requirements():
            print("\\n❌ Please install missing requirements first")
            return False
        
        # Step 2: Setup directories
        setup_directories()
        
        # Step 3: Generate sample data
        if not generate_sample_data():
            print("\\n❌ Failed to generate sample data")
            return False
        
        # Step 4: Run ETL pipeline
        if not run_etl_pipeline():
            print("\\n❌ ETL Pipeline failed")
            return False
        
        # Step 5: Show results
        show_results()
        
        # Step 6: Show next steps
        show_next_steps()
        
        print("\\n🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("Happy learning with Pandas ETL! 🐼")
        
        return True
        
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Setup interrupted by user")
        return False
    
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)