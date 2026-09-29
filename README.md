# Hands-On: Ekstraksi dan Transformasi Data Sensor dengan Pandas

## Deskripsi
Proyek ini berisi tutorial hands-on untuk melakukan ekstraksi, transformasi, dan loading (ETL) data sensor menggunakan Python Pandas. Anda akan belajar mengolah data dari berbagai jenis sensor seperti suhu, kelembaban, tekanan, dan kualitas udara.

## Dataset
Dataset yang digunakan merupakan simulasi data sensor IoT yang mencakup:
- **Sensor Suhu**: Pengukuran suhu dalam Celsius
- **Sensor Kelembaban**: Pengukuran kelembaban relatif (%)
- **Sensor Tekanan**: Pengukuran tekanan atmosfer (hPa)
- **Sensor Kualitas Udara**: Indeks kualitas udara (AQI)

## Struktur Proyek
```
ETL-Pandas/
├── data/
│   ├── raw/              # Data mentah dari sensor
│   ├── processed/        # Data yang sudah diproses
│   └── output/          # Hasil akhir
├── notebooks/           # Jupyter notebooks untuk tutorial
├── scripts/            # Script Python untuk ETL
├── utils/              # Fungsi utility
└── config/             # File konfigurasi
```

## Fitur Tutorial
1. **Data Extraction**: Membaca data dari berbagai format (CSV, JSON, Excel)
2. **Data Cleaning**: Menangani missing values, outliers, dan duplikasi
3. **Data Transformation**: Agregasi, filtering, dan feature engineering
4. **Data Validation**: Memastikan kualitas data
5. **Data Export**: Menyimpan hasil ke berbagai format

## Requirements
- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn
- jupyter
- openpyxl

## Installation
```bash
pip install -r requirements.txt
```

## Quick Start
1. Jalankan notebook tutorial: `01_ETL_Sensor_Data_Tutorial.ipynb`
2. Eksekusi script ETL: `python scripts/etl_pipeline.py`
3. Lihat hasil di folder `data/output/`