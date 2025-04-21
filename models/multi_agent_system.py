import os
import pandas as pd
from db.database import AgriDatabase
from agents.farmer_advisor import FarmerAdvisor
from agents.market_researcher import MarketResearcher
from agents.weather_station import WeatherStation
from utils.data_loader import load_datasets, initialize_database
from utils.llm_integration import OllamaLLM

class SustainableFarmingSystem:
    """
    Main system class for the multi-agent sustainable farming system.
    
    This class coordinates the different agents, manages data flow between them,
    and provides an interface for users to interact with the system.
    """
    
    def __init__(self, use_llm=True):
        """Initialize the sustainable farming system."""
        # Initialize database
        self.db = AgriDatabase()
        
        # Load data if database is empty
        self.initialize_data()
        
        # Initialize agents
        self.agents = {
            "farmer_advisor": FarmerAdvisor(self.db),
            "market_researcher": MarketResearcher(self.db),
            "weather_station": WeatherStation(self.db)
        }
        
        # Initialize LLM integration if enabled
        self.use_llm = use_llm
        if self.use_llm:
            self.llm = OllamaLLM()
            # Disable LLM if not available
            if not self.llm.is_available:
                self.use_llm = False
                print("LLM integration disabled due to connection issues")
        
        print("Sustainable Farming System initialized with all agents")
    
    def initialize_data(self):
        """Initialize the database with data if it's empty."""
        # Check if database contains data
        farm_data = self.db.get_farm_data()
        market_data = self.db.get_market_data()
        
        if not farm_data or not market_data:
            print("Database is empty. Loading initial data...")
            
            # Load datasets
            farmer_df, market_df = load_datasets()
            
            # Initialize database
            self.db.load_initial_data(farmer_df, market_df)
            
            print("Database initialized with data")
    
    def generate_farm_recommendations(self, farm_id, region="central", financial_goal="balance", sustainability_preference=5):
        """
        Generate comprehensive recommendations for a specific farm.
        
        Args:
            farm_id (int): Farm ID
            region (str): Geographic region (north, central, south)
            financial_goal (str): Farmer's financial goal (maximize_profit, minimize_cost, balance)
            sustainability_preference (int): Importance of sustainability (1-10)
            
        Returns:
            dict: Comprehensive recommendations from all agents
        """
        # Get farm data
        farm_data = self.db.get_farm_data(farm_id)
        if not farm_data:
            return {"status": "error", "message": f"Farm ID {farm_id} not found"}
        
        # Context for all agents
        context = {
            "farm_id": farm_id,
            "region": region,
            "financial_goal": financial_goal,
            "sustainability_preference": sustainability_preference,
            "crop_type": farm_data["crop_type"]
        }
        
        # Get recommendations from all agents
        recommendations = {
            "farm_data": farm_data,
            "farming_recommendations": self.agents["farmer_advisor"].generate_recommendations(context),
            "market_recommendations": self.agents["market_researcher"].generate_recommendations(context),
            "weather_recommendations": self.agents["weather_station"].generate_recommendations(context),
        }
        
        # Extract high priority recommendations across all categories
        high_priority = []
        
        # Function to extract and score recommendations
        def extract_recs(category, source, weight):
            for group in source:
                for rec in group["recommendations"]:
                    # Calculate combined score (sustainability + economic weighted by preference)
                    sustainability = rec.get("sustainability_impact", 0)
                    economic = rec.get("economic_impact", 0)
                    confidence = rec.get("confidence", 0.5)
                    
                    # Weight the scores based on preference
                    sustainability_weight = sustainability_preference / 10
                    economic_weight = 1 - sustainability_weight
                    
                    score = (sustainability * sustainability_weight + 
                           economic * economic_weight) * confidence * weight
                    
                    high_priority.append({
                        "category": category,
                        "focus": rec.get("focus", ""),
                        "action": rec["action"],
                        "sustainability_impact": sustainability,
                        "economic_impact": economic,
                        "confidence": confidence,
                        "score": score
                    })
        
        # Extract and score recommendations from each agent
        extract_recs("Farming Practices", recommendations["farming_recommendations"], 1.0)
        extract_recs("Market Strategy", recommendations["market_recommendations"], 0.9)
        extract_recs("Weather Management", recommendations["weather_recommendations"], 0.8)
        
        # Sort by score and get top recommendations
        high_priority.sort(key=lambda x: x["score"], reverse=True)
        recommendations["high_priority_actions"] = high_priority[:5]  # Top 5 recommendations
        
        # Calculate overall sustainability potential
        initial_sustainability = farm_data["sustainability_score"]
        potential_improvement = sum(rec["sustainability_impact"] for rec in high_priority[:5]) * 0.2
        
        recommendations["sustainability_summary"] = {
            "current_score": initial_sustainability,
            "potential_score": min(100, initial_sustainability + potential_improvement),
            "improvement_percentage": (potential_improvement / initial_sustainability) * 100 if initial_sustainability > 0 else 0
        }
        
        # Enhance recommendations with LLM if available
        if self.use_llm:
            # Get LLM-enhanced analysis of farm data
            llm_farm_analysis = self.llm.analyze_farm_data(farm_data)
            if llm_farm_analysis.get("status") == "success":
                recommendations["llm_farm_analysis"] = llm_farm_analysis["generated_text"]
            
            # Get LLM-enhanced market insights
            market_data = self.db.get_market_data()
            llm_market_insights = self.llm.generate_market_insights(market_data, farm_data["crop_type"])
            if llm_market_insights.get("status") == "success":
                recommendations["llm_market_insights"] = llm_market_insights["generated_text"]
            
            # Get LLM-enhanced weather recommendations
            forecast = self.agents["weather_station"].generate_forecast(region, 7)
            llm_weather_insights = self.llm.enhance_weather_recommendations(
                forecast, 
                recommendations["weather_recommendations"],
                farm_data["crop_type"]
            )
            if llm_weather_insights.get("status") == "success":
                recommendations["llm_weather_insights"] = llm_weather_insights["generated_text"]
        
        return recommendations
    
    def query_market_data(self, product=None, time_horizon="short-term"):
        """
        Query market data for specific products or overall market analysis.
        
        Args:
            product (str): Specific crop to analyze (optional)
            time_horizon (str): "short-term" or "long-term"
            
        Returns:
            dict: Market data and analysis
        """
        query = {
            "product": product,
            "time_horizon": time_horizon
        }
        
        return self.agents["market_researcher"].process_input(query)
    
    def query_weather_data(self, region="central", forecast_days=7, include_historical=False):
        """
        Query weather data and forecasts.
        
        Args:
            region (str): Geographic region (north, central, south)
            forecast_days (int): Number of days to forecast
            include_historical (bool): Whether to include historical data
            
        Returns:
            dict: Weather data and forecasts
        """
        query = {
            "region": region,
            "forecast_days": forecast_days,
            "include_historical": include_historical
        }
        
        return self.agents["weather_station"].process_input(query)
    
    def analyze_new_farm(self, soil_ph, soil_moisture, temperature_c, rainfall_mm, region="central"):
        """
        Analyze data for a new farm that isn't yet in the database.
        
        Args:
            soil_ph (float): Soil pH
            soil_moisture (float): Soil moisture
            temperature_c (float): Average temperature in Celsius
            rainfall_mm (float): Average rainfall in mm
            region (str): Geographic region
            
        Returns:
            dict: Initial analysis and recommendations
        """
        # Prepare input data
        input_data = {
            "soil_ph": soil_ph,
            "soil_moisture": soil_moisture,
            "temperature_c": temperature_c,
            "rainfall_mm": rainfall_mm
        }
        
        # Get initial analysis from Farmer Advisor
        farm_analysis = self.agents["farmer_advisor"].process_input(input_data)
        
        # Get weather forecast
        weather_data = self.query_weather_data(region)
        
        # Get market overview
        market_overview = self.query_market_data()
        
        # Compile the response
        response = {
            "status": "success",
            "initial_analysis": farm_analysis,
            "weather_forecast": weather_data.get("forecast", [])[:7],  # 7-day forecast
            "agricultural_impact": weather_data.get("agricultural_impact", {}),
            "market_overview": market_overview.get("market_overview", {})
        }
        
        # Generate crop recommendations based on soil and climate
        if "suitable_crops" in farm_analysis.get("climate_analysis", {}):
            suitable_crops = farm_analysis["climate_analysis"]["suitable_crops"]
            
            # Filter market data for these crops
            if "top_profit_potential_crops" in market_overview.get("market_overview", {}):
                market_crops = market_overview["market_overview"]["top_profit_potential_crops"]
                recommended_crops = []
                
                for crop_data in market_crops:
                    if crop_data["product"] in suitable_crops:
                        recommended_crops.append({
                            "crop": crop_data["product"],
                            "market_recommendation": crop_data["recommendation"],
                            "economic_potential": "High" if crop_data["profit_potential"] > 500 else "Medium"
                        })
                
                response["recommended_crops"] = recommended_crops
        
        return response
    
    def get_sustainability_comparison(self, crop_type=None):
        """
        Get sustainability comparison data across farms, optionally filtered by crop.
        
        Args:
            crop_type (str): Crop type to filter by (optional)
            
        Returns:
            dict: Sustainability comparison data
        """
        # Get all farm data
        farm_data = self.db.get_farm_data()
        if not farm_data:
            return {"status": "error", "message": "No farm data available"}
        
        # Convert to DataFrame
        farm_df = pd.DataFrame(farm_data)
        
        # Filter by crop if specified
        if crop_type:
            farm_df = farm_df[farm_df["crop_type"] == crop_type]
            if len(farm_df) == 0:
                return {"status": "error", "message": f"No farms growing {crop_type}"}
        
        # Calculate statistics
        stats = {
            "avg_sustainability_score": farm_df["sustainability_score"].mean(),
            "min_sustainability_score": farm_df["sustainability_score"].min(),
            "max_sustainability_score": farm_df["sustainability_score"].max(),
            "count": len(farm_df)
        }
        
        # Calculate resource efficiency metrics
        farm_df["fertilizer_efficiency"] = farm_df["crop_yield_ton"] / farm_df["fertilizer_usage_kg"]
        farm_df["pesticide_efficiency"] = farm_df["crop_yield_ton"] / farm_df["pesticide_usage_kg"]
        
        efficiency_stats = {
            "avg_fertilizer_efficiency": farm_df["fertilizer_efficiency"].mean(),
            "avg_pesticide_efficiency": farm_df["pesticide_efficiency"].mean(),
            "best_practices": []
        }
        
        # Identify top 5 most sustainable farms for best practices
        top_farms = farm_df.sort_values("sustainability_score", ascending=False).head(5)
        
        for _, farm in top_farms.iterrows():
            efficiency_stats["best_practices"].append({
                "farm_id": int(farm["farm_id"]),
                "crop_type": farm["crop_type"],
                "sustainability_score": float(farm["sustainability_score"]),
                "fertilizer_efficiency": float(farm["fertilizer_efficiency"]),
                "pesticide_efficiency": float(farm["pesticide_efficiency"])
            })
        
        # Group by crop type
        if crop_type is None:
            crop_stats = farm_df.groupby("crop_type")["sustainability_score"].agg(["mean", "count"]).reset_index()
            crop_stats = crop_stats.sort_values("mean", ascending=False)
            
            crop_comparison = []
            for _, row in crop_stats.iterrows():
                crop_comparison.append({
                    "crop_type": row["crop_type"],
                    "avg_sustainability_score": float(row["mean"]),
                    "farm_count": int(row["count"])
                })
            
            stats["crop_comparison"] = crop_comparison
        
        return {
            "status": "success",
            "sustainability_stats": stats,
            "efficiency_stats": efficiency_stats,
            "filter": {"crop_type": crop_type} if crop_type else "all_crops"
        }
    
    def agent_communication_test(self, farm_id, region="central"):
        """
        Test inter-agent communication for a specific farm.
        
        Args:
            farm_id (int): Farm ID
            region (str): Geographic region
            
        Returns:
            dict: Results of agent communication
        """
        # Get farm data
        farm_data = self.db.get_farm_data(farm_id)
        if not farm_data:
            return {"status": "error", "message": f"Farm ID {farm_id} not found"}
        
        # 1. Farmer Advisor requests weather forecast from Weather Station
        weather_request = {
            "request_type": "weather_forecast",
            "region": region,
            "days": 7
        }
        weather_response = self.agents["weather_station"].receive_message(
            self.agents["farmer_advisor"], 
            weather_request
        )
        
        # 2. Farmer Advisor requests market analysis from Market Researcher
        market_request = {
            "request_type": "crop_market_analysis",
            "crop_type": farm_data["crop_type"],
            "time_horizon": "short-term"
        }
        market_response = self.agents["market_researcher"].receive_message(
            self.agents["farmer_advisor"], 
            market_request
        )
        
        # 3. Farmer Advisor requests planting advice from Weather Station
        planting_request = {
            "request_type": "planting_advice",
            "region": region,
            "crop_type": farm_data["crop_type"]
        }
        planting_response = self.agents["weather_station"].receive_message(
            self.agents["farmer_advisor"], 
            planting_request
        )
        
        return {
            "status": "success",
            "farm_id": farm_id,
            "farm_data": farm_data,
            "weather_forecast_response": weather_response,
            "market_analysis_response": market_response,
            "planting_advice_response": planting_response
        }
    
    def close(self):
        """Close all connections and resources."""
        try:
            # Close database connection
            if hasattr(self, 'db'):
                self.db.close()
            
            # Close any agent resources
            for agent_name, agent in self.agents.items():
                if hasattr(agent, 'close'):
                    agent.close()
            
            # Close LLM if available
            if self.use_llm and hasattr(self, 'llm') and hasattr(self.llm, 'close'):
                self.llm.close()
            
            print("All system resources closed")
        except Exception as e:
            print(f"Error closing system resources: {e}")
    
    def reset_database(self):
        """Reset the database and reload initial data."""
        # Reset the database (drop and recreate tables)
        if not self.db.reset_database():
            return {"status": "error", "message": "Failed to reset database tables"}
            
        # Load initial data
        try:
            print("Loading fresh data into database...")
            farmer_df, market_df = load_datasets()
            self.db.load_initial_data(farmer_df, market_df)
            print("Database successfully reset and reloaded with fresh data")
            return {"status": "success", "message": "Database reset and reloaded successfully"}
        except Exception as e:
            print(f"Error reloading data: {e}")
            return {"status": "error", "message": f"Database tables reset but failed to reload data: {str(e)}"} 