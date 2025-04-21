import os
import pandas as pd
import numpy as np
from db.database import AgriDatabase

def load_datasets():
    """Load the datasets from the provided CSV files."""
    data_path = os.path.join('Dataset', '[Usecase 3] AI for Sustainable Agriculture')
    
    farmer_path = os.path.join(data_path, 'farmer_advisor_dataset.csv')
    market_path = os.path.join(data_path, 'market_researcher_dataset.csv')
    
    print(f"Loading datasets from: {data_path}")
    print(f"Farmer advisor file exists: {os.path.exists(farmer_path)}")
    print(f"Market researcher file exists: {os.path.exists(market_path)}")
    
    farmer_df = pd.read_csv(farmer_path)
    market_df = pd.read_csv(market_path)
    
    return farmer_df, market_df

def preprocess_farm_data(df):
    """Preprocess and normalize the farm data."""
    processed_df = df.copy()
    
    # Handle missing values if any
    processed_df.fillna({
        'Soil_pH': processed_df['Soil_pH'].mean(),
        'Soil_Moisture': processed_df['Soil_Moisture'].mean(),
        'Temperature_C': processed_df['Temperature_C'].mean(),
        'Rainfall_mm': processed_df['Rainfall_mm'].mean(),
        'Fertilizer_Usage_kg': processed_df['Fertilizer_Usage_kg'].mean(),
        'Pesticide_Usage_kg': processed_df['Pesticide_Usage_kg'].mean(),
        'Crop_Yield_ton': processed_df['Crop_Yield_ton'].mean(),
    }, inplace=True)
    
    # Create derived features for sustainability analysis
    processed_df['Fertilizer_per_Yield'] = processed_df['Fertilizer_Usage_kg'] / processed_df['Crop_Yield_ton']
    processed_df['Pesticide_per_Yield'] = processed_df['Pesticide_Usage_kg'] / processed_df['Crop_Yield_ton']
    
    # Normalize numeric features
    numeric_cols = ['Soil_pH', 'Soil_Moisture', 'Temperature_C', 'Rainfall_mm', 
                   'Fertilizer_Usage_kg', 'Pesticide_Usage_kg', 'Crop_Yield_ton']
    
    for col in numeric_cols:
        col_min = processed_df[col].min()
        col_max = processed_df[col].max()
        processed_df[f'{col}_normalized'] = (processed_df[col] - col_min) / (col_max - col_min)
    
    return processed_df

def preprocess_market_data(df):
    """Preprocess and normalize the market data."""
    processed_df = df.copy()
    
    # Handle missing values if any
    numeric_cols = ['Market_Price_per_ton', 'Demand_Index', 'Supply_Index', 
                  'Competitor_Price_per_ton', 'Economic_Indicator', 
                  'Weather_Impact_Score', 'Consumer_Trend_Index']
    
    for col in numeric_cols:
        processed_df[col].fillna(processed_df[col].mean(), inplace=True)
    
    # Create derived features
    processed_df['Price_Competitiveness'] = processed_df['Market_Price_per_ton'] / processed_df['Competitor_Price_per_ton']
    processed_df['Market_Balance'] = processed_df['Demand_Index'] - processed_df['Supply_Index']
    
    # Categorize seasonal factor if needed
    if processed_df['Seasonal_Factor'].dtype == 'object':
        season_mapping = {'Low': 0, 'Medium': 1, 'High': 2}
        processed_df['Seasonal_Factor_Numeric'] = processed_df['Seasonal_Factor'].map(season_mapping)
    
    # Normalize numeric features
    for col in numeric_cols:
        col_min = processed_df[col].min()
        col_max = processed_df[col].max()
        processed_df[f'{col}_normalized'] = (processed_df[col] - col_min) / (col_max - col_min)
    
    return processed_df

def calculate_sustainability_metrics(farm_df):
    """Calculate additional sustainability metrics for farm data."""
    metrics_df = farm_df.copy()
    
    # Calculate water efficiency (higher is better)
    metrics_df['Water_Efficiency'] = metrics_df['Crop_Yield_ton'] / metrics_df['Soil_Moisture']
    
    # Calculate chemical usage efficiency (higher is better)
    total_chemicals = metrics_df['Fertilizer_Usage_kg'] + metrics_df['Pesticide_Usage_kg']
    metrics_df['Chemical_Efficiency'] = metrics_df['Crop_Yield_ton'] / total_chemicals
    
    # Calculate environmental impact score (lower is better)
    # This is a made-up score based on fertilizer, pesticide usage, and soil conditions
    metrics_df['Environmental_Impact'] = (
        0.5 * metrics_df['Fertilizer_Usage_kg'] / metrics_df['Fertilizer_Usage_kg'].max() +
        0.5 * metrics_df['Pesticide_Usage_kg'] / metrics_df['Pesticide_Usage_kg'].max()
    )
    
    # Calculate overall sustainability index (higher is better)
    # Combine multiple factors into a 0-100 score
    metrics_df['Calculated_Sustainability'] = (
        0.3 * (1 - metrics_df['Environmental_Impact']) * 100 +
        0.3 * (metrics_df['Water_Efficiency'] / metrics_df['Water_Efficiency'].max()) * 100 +
        0.4 * (metrics_df['Chemical_Efficiency'] / metrics_df['Chemical_Efficiency'].max()) * 100
    )
    
    return metrics_df

def initialize_database(farmer_df, market_df):
    """Initialize the database with the preprocessed datasets."""
    # Create database instance
    db = AgriDatabase()
    
    # Load the data
    db.load_initial_data(farmer_df, market_df)
    
    # Close the connection
    db.close()
    
    return True

def get_crop_sustainability_ranking(farm_data):
    """Get sustainability ranking by crop type."""
    # If column names are lowercase, use lowercase
    crop_type_col = 'crop_type' if 'crop_type' in farm_data.columns else 'Crop_Type'
    sustainability_col = 'sustainability_score' if 'sustainability_score' in farm_data.columns else 'Sustainability_Score'
    
    crop_sustainability = farm_data.groupby(crop_type_col)[sustainability_col].agg(['mean', 'min', 'max']).reset_index()
    crop_sustainability = crop_sustainability.sort_values('mean', ascending=False)
    return crop_sustainability

def get_fertilizer_efficiency_by_crop(farm_data):
    """Calculate fertilizer efficiency by crop type."""
    # Create a copy to avoid SettingWithCopyWarning
    data = farm_data.copy()
    
    # Determine column names (handle both lowercase and uppercase)
    crop_type_col = 'crop_type' if 'crop_type' in data.columns else 'Crop_Type'
    crop_yield_col = 'crop_yield_ton' if 'crop_yield_ton' in data.columns else 'Crop_Yield_ton'
    fertilizer_col = 'fertilizer_usage_kg' if 'fertilizer_usage_kg' in data.columns else 'Fertilizer_Usage_kg'
    
    # Calculate fertilizer efficiency (yield per kg of fertilizer)
    data['Fertilizer_Efficiency'] = data[crop_yield_col] / data[fertilizer_col]
    
    # Group by crop type and calculate statistics
    fertilizer_efficiency = data.groupby(crop_type_col)['Fertilizer_Efficiency'].agg(['mean', 'min', 'max']).reset_index()
    fertilizer_efficiency = fertilizer_efficiency.sort_values('mean', ascending=False)
    
    return fertilizer_efficiency 
