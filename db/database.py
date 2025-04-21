import os
import sqlite3
from sqlite3 import Error
import pandas as pd
import threading

class AgriDatabase:
    """
    SQLite database for storing agricultural data and agent interactions.
    Acts as long-term memory for the multi-agent system.
    """
    
    # Thread-local storage for connections
    _local = threading.local()
    
    def __init__(self, db_path="db/agri_data.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # Initialize database tables if they don't exist
        self.setup_tables()
    
    def get_connection(self):
        """
        Get a thread-local database connection.
        This ensures each thread has its own connection.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            try:
                self._local.conn = sqlite3.connect(self.db_path)
                print(f"Connected to SQLite database at {self.db_path} in thread {threading.get_ident()}")
            except Error as e:
                print(f"Error connecting to database: {e}")
        return self._local.conn
    
    def setup_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Farm Data table (from farmer advisor dataset)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS farm_data (
                farm_id INTEGER PRIMARY KEY,
                soil_ph REAL,
                soil_moisture REAL,
                temperature_c REAL,
                rainfall_mm REAL,
                crop_type TEXT,
                fertilizer_usage_kg REAL,
                pesticide_usage_kg REAL,
                crop_yield_ton REAL,
                sustainability_score REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Market Data table (from market researcher dataset)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                market_id INTEGER PRIMARY KEY,
                product TEXT,
                market_price_per_ton REAL,
                demand_index REAL,
                supply_index REAL,
                competitor_price_per_ton REAL,
                economic_indicator REAL,
                weather_impact_score REAL,
                seasonal_factor TEXT,
                consumer_trend_index REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Recommendations table (for storing agent recommendations)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id INTEGER,
                recommendation_type TEXT,
                recommendation_text TEXT,
                sustainability_impact REAL,
                economic_impact REAL,
                confidence_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farm_id) REFERENCES farm_data (farm_id)
            )
            ''')
            
            # Agent Interactions table (for tracking agent activities)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                action_type TEXT,
                action_details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Weather Forecasts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                forecast_date DATE,
                temperature_high_c REAL,
                temperature_low_c REAL,
                precipitation_mm REAL,
                humidity_percent REAL,
                wind_speed_kph REAL,
                forecast_notes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            print("All tables created successfully")
        except Error as e:
            print(f"Error setting up tables: {e}")
    
    def load_initial_data(self, farmer_df, market_df):
        """Load initial data from the CSV datasets into the database."""
        try:
            conn = self.get_connection()
            
            # Prepare farmer data for insertion
            farmer_records = []
            for _, row in farmer_df.iterrows():
                record = (
                    int(row['Farm_ID']),
                    float(row['Soil_pH']),
                    float(row['Soil_Moisture']),
                    float(row['Temperature_C']),
                    float(row['Rainfall_mm']),
                    str(row['Crop_Type']),
                    float(row['Fertilizer_Usage_kg']),
                    float(row['Pesticide_Usage_kg']),
                    float(row['Crop_Yield_ton']),
                    float(row['Sustainability_Score'])
                )
                farmer_records.append(record)
            
            # Insert farmer data
            cursor = conn.cursor()
            cursor.executemany('''
            INSERT OR REPLACE INTO farm_data (
                farm_id, soil_ph, soil_moisture, temperature_c, rainfall_mm,
                crop_type, fertilizer_usage_kg, pesticide_usage_kg, 
                crop_yield_ton, sustainability_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', farmer_records)
            
            # Prepare market data for insertion
            market_records = []
            for _, row in market_df.iterrows():
                record = (
                    int(row['Market_ID']),
                    str(row['Product']),
                    float(row['Market_Price_per_ton']),
                    float(row['Demand_Index']),
                    float(row['Supply_Index']),
                    float(row['Competitor_Price_per_ton']),
                    float(row['Economic_Indicator']),
                    float(row['Weather_Impact_Score']),
                    str(row['Seasonal_Factor']),
                    float(row['Consumer_Trend_Index'])
                )
                market_records.append(record)
            
            # Insert market data
            cursor.executemany('''
            INSERT OR REPLACE INTO market_data (
                market_id, product, market_price_per_ton, demand_index, supply_index,
                competitor_price_per_ton, economic_indicator, weather_impact_score,
                seasonal_factor, consumer_trend_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', market_records)
            
            conn.commit()
            print(f"Loaded {len(farmer_records)} farm records and {len(market_records)} market records into the database")
        except Error as e:
            print(f"Error loading initial data: {e}")
    
    def add_recommendation(self, farm_id, rec_type, rec_text, sustainability_impact, economic_impact, confidence_score):
        """Add a new recommendation to the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO recommendations (
                farm_id, recommendation_type, recommendation_text,
                sustainability_impact, economic_impact, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (farm_id, rec_type, rec_text, sustainability_impact, economic_impact, confidence_score))
            
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error adding recommendation: {e}")
            return None
    
    def log_agent_interaction(self, agent_name, action_type, action_details):
        """Log an agent interaction in the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO agent_interactions (
                agent_name, action_type, action_details
            ) VALUES (?, ?, ?)
            ''', (agent_name, action_type, action_details))
            
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error logging agent interaction: {e}")
            return None
    
    def get_farm_data(self, farm_id=None):
        """Get farm data from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if farm_id:
                cursor.execute("SELECT * FROM farm_data WHERE farm_id = ?", (farm_id,))
                columns = [col[0].lower() for col in cursor.description]
                result = cursor.fetchone()
                if result:
                    return dict(zip(columns, result))
                return None
            else:
                cursor.execute("SELECT * FROM farm_data")
                columns = [col[0].lower() for col in cursor.description]
                results = cursor.fetchall()
                return [dict(zip(columns, row)) for row in results]
        except Error as e:
            print(f"Error retrieving farm data: {e}")
            return None
    
    def get_market_data(self, product=None):
        """Get market data from the database, optionally filtered by product."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if product:
                cursor.execute("SELECT * FROM market_data WHERE product = ?", (product,))
            else:
                cursor.execute("SELECT * FROM market_data")
                
            columns = [col[0].lower() for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Error as e:
            print(f"Error retrieving market data: {e}")
            return None
    
    def get_recommendations(self, farm_id=None, rec_type=None):
        """Get recommendations from the database, with optional filters."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM recommendations"
            params = []
            
            if farm_id or rec_type:
                query += " WHERE"
                
                if farm_id:
                    query += " farm_id = ?"
                    params.append(farm_id)
                    
                    if rec_type:
                        query += " AND recommendation_type = ?"
                        params.append(rec_type)
                elif rec_type:
                    query += " recommendation_type = ?"
                    params.append(rec_type)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            columns = [col[0].lower() for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Error as e:
            print(f"Error retrieving recommendations: {e}")
            return None
    
    def get_agent_interactions(self, agent_name=None, limit=100):
        """Get recent agent interactions from the database."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if agent_name:
                cursor.execute(
                    "SELECT * FROM agent_interactions WHERE agent_name = ? ORDER BY timestamp DESC LIMIT ?",
                    (agent_name, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM agent_interactions ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                
            columns = [col[0].lower() for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Error as e:
            print(f"Error retrieving agent interactions: {e}")
            return None
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
            print("Database connection closed")
    
    def reset_database(self):
        """Reset the database by dropping and recreating all tables."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Drop all tables
            cursor.execute("DROP TABLE IF EXISTS agent_interactions")
            cursor.execute("DROP TABLE IF EXISTS recommendations")
            cursor.execute("DROP TABLE IF EXISTS weather_forecasts")
            cursor.execute("DROP TABLE IF EXISTS farm_data")
            cursor.execute("DROP TABLE IF EXISTS market_data")
            
            conn.commit()
            print("All tables dropped successfully")
            
            # Recreate tables
            self.setup_tables()
            
            return True
        except Error as e:
            print(f"Error resetting database: {e}")
            return False 