import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent

class WeatherStation(BaseAgent):
    """
    Weather Station agent that provides weather data and forecasts to help
    farmers make informed decisions about planting, irrigation, and harvesting.
    
    This agent simulates real-time weather data and forecasts to enhance
    the multi-agent system's ability to recommend sustainable practices.
    """
    
    def __init__(self, db_connection):
        """Initialize the Weather Station agent."""
        super().__init__("Weather Station", db_connection)
        
        # Initialize weather parameters (using random seed for reproducibility)
        random.seed(42)
        self.generate_weather_patterns()
    
    def generate_weather_patterns(self):
        """Generate simulated weather patterns for different regions."""
        # Define regions with different climate characteristics
        self.regions = {
            "north": {
                "base_temp": 15,  # Base temperature in Celsius
                "temp_variation": 8,  # Daily variation
                "base_rainfall": 5,  # Base rainfall in mm
                "rainfall_variation": 15,
                "seasonal_factor": 0.8,  # Seasonal influence factor
                "drought_probability": 0.05,
                "flood_probability": 0.05
            },
            "central": {
                "base_temp": 22,
                "temp_variation": 6,
                "base_rainfall": 3,
                "rainfall_variation": 10,
                "seasonal_factor": 0.6,
                "drought_probability": 0.08,
                "flood_probability": 0.03
            },
            "south": {
                "base_temp": 28,
                "temp_variation": 5,
                "base_rainfall": 2,
                "rainfall_variation": 8,
                "seasonal_factor": 0.5,
                "drought_probability": 0.12,
                "flood_probability": 0.02
            }
        }
        
        # Define seasonal patterns (simplified for simulation)
        self.seasons = {
            "spring": {
                "temp_modifier": 0,
                "rainfall_modifier": 1.2,
                "humidity_modifier": 1.1,
                "monthly_range": [3, 4, 5]  # March, April, May
            },
            "summer": {
                "temp_modifier": 1.2,
                "rainfall_modifier": 0.8,
                "humidity_modifier": 0.9,
                "monthly_range": [6, 7, 8]  # June, July, August
            },
            "fall": {
                "temp_modifier": 0,
                "rainfall_modifier": 1.0,
                "humidity_modifier": 1.0,
                "monthly_range": [9, 10, 11]  # September, October, November
            },
            "winter": {
                "temp_modifier": -1.2,
                "rainfall_modifier": 1.1,
                "humidity_modifier": 1.2,
                "monthly_range": [12, 1, 2]  # December, January, February
            }
        }
        
        self.log_action(
            action_type="initialization",
            action_details="Weather patterns and seasonal variations initialized"
        )
    
    def get_current_season(self, date=None):
        """
        Determine the current season based on the date.
        
        Args:
            date: Date to check (default is current date)
            
        Returns:
            str: Current season (spring, summer, fall, winter)
        """
        if date is None:
            date = datetime.now()
        
        month = date.month
        
        for season, data in self.seasons.items():
            if month in data["monthly_range"]:
                return season
        
        # Default fallback
        return "spring"
    
    def process_input(self, input_data):
        """
        Process weather-related queries.
        
        Args:
            input_data (dict): Query parameters
                - region: Geographic region (north, central, south)
                - forecast_days: Number of days to forecast (default: 7)
                - include_historical: Whether to include historical data (default: False)
                - specific_date: Specific date for historical data (optional)
        
        Returns:
            dict: Weather data and forecasts
        """
        self.log_action("input_processing", f"Processing weather query: {str(input_data)[:100]}...")
        
        region = input_data.get("region", "central")
        forecast_days = input_data.get("forecast_days", 7)
        include_historical = input_data.get("include_historical", False)
        specific_date = input_data.get("specific_date")
        
        if region not in self.regions:
            return {"status": "error", "message": f"Unknown region: {region}"}
        
        # Generate current weather
        current_weather = self.generate_current_weather(region)
        
        # Generate forecast
        forecast = self.generate_forecast(region, forecast_days)
        
        # Get historical data if requested
        historical_data = None
        if include_historical:
            if specific_date:
                try:
                    date = datetime.strptime(specific_date, "%Y-%m-%d")
                    historical_data = self.generate_historical_data(region, date)
                except ValueError:
                    return {"status": "error", "message": f"Invalid date format: {specific_date}. Use YYYY-MM-DD"}
            else:
                # Default to last 30 days
                historical_data = self.generate_historical_data(region)
        
        return {
            "status": "success",
            "region": region,
            "current_weather": current_weather,
            "forecast": forecast,
            "historical_data": historical_data,
            "agricultural_impact": self.assess_agricultural_impact(current_weather, forecast, region)
        }
    
    def generate_current_weather(self, region):
        """
        Generate current weather data for a specific region.
        
        Args:
            region (str): Geographic region
            
        Returns:
            dict: Current weather data
        """
        # Get region parameters
        params = self.regions[region]
        
        # Get current season
        current_season = self.get_current_season()
        season_params = self.seasons[current_season]
        
        # Generate temperature (with seasonal and random variations)
        temp_base = params["base_temp"] + (season_params["temp_modifier"] * params["seasonal_factor"])
        temp_variation = params["temp_variation"] * (0.8 + 0.4 * random.random())
        temperature = temp_base + (random.random() * 2 - 1) * temp_variation
        
        # Generate rainfall
        rainfall_base = params["base_rainfall"] * season_params["rainfall_modifier"]
        rainfall = random.random() * params["rainfall_variation"] * rainfall_base
        if random.random() < 0.6:  # 60% chance of less rainfall
            rainfall = rainfall * 0.3
        
        # Generate humidity
        humidity_base = 60 + (20 * season_params["humidity_modifier"])
        humidity = humidity_base + (random.random() * 20 - 10)
        
        # Generate wind speed
        wind_speed = 5 + random.random() * 15
        
        # Weather condition based on rainfall and temperature
        if rainfall > params["rainfall_variation"]:
            condition = "Heavy Rain"
        elif rainfall > params["rainfall_variation"] / 2:
            condition = "Light Rain"
        elif temperature > params["base_temp"] + params["temp_variation"]:
            condition = "Hot"
        elif temperature < params["base_temp"] - params["temp_variation"]:
            condition = "Cold"
        else:
            condition = "Clear"
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "season": current_season,
            "temperature_c": round(temperature, 1),
            "rainfall_mm": round(rainfall, 1),
            "humidity_percent": round(humidity, 1),
            "wind_speed_kph": round(wind_speed, 1),
            "condition": condition
        }
    
    def generate_forecast(self, region, days=7):
        """
        Generate weather forecast for the specified number of days.
        
        Args:
            region (str): Geographic region
            days (int): Number of days to forecast
            
        Returns:
            list: Weather forecast for each day
        """
        forecast = []
        params = self.regions[region]
        
        # Start with current weather as base
        current = self.generate_current_weather(region)
        temp_trend = 0
        rain_trend = 0
        
        # Generate forecast for each day
        for day in range(1, days + 1):
            date = datetime.now() + timedelta(days=day)
            season = self.get_current_season(date)
            season_params = self.seasons[season]
            
            # Update temperature trend (with some persistence)
            temp_trend = temp_trend * 0.5 + (random.random() * 2 - 1) * 0.5
            
            # Calculate temperature with trend and seasonal factors
            temp_base = params["base_temp"] + (season_params["temp_modifier"] * params["seasonal_factor"])
            temp_variation = params["temp_variation"] * (0.8 + 0.4 * random.random())
            temperature = temp_base + temp_trend * temp_variation
            
            # Update rainfall trend (with some persistence)
            rain_trend = rain_trend * 0.3 + (random.random() * 2 - 1) * 0.7
            
            # Calculate rainfall with trend and seasonal factors
            rainfall_base = params["base_rainfall"] * season_params["rainfall_modifier"]
            rainfall = max(0, rainfall_base + rain_trend * params["rainfall_variation"])
            
            # Extreme weather events
            if random.random() < params["drought_probability"]:
                rainfall = 0
                temperature += 3
                condition = "Drought Conditions"
            elif random.random() < params["flood_probability"]:
                rainfall = params["rainfall_variation"] * 2
                condition = "Flood Warning"
            else:
                # Normal conditions
                if rainfall > params["rainfall_variation"]:
                    condition = "Heavy Rain"
                elif rainfall > params["rainfall_variation"] / 2:
                    condition = "Light Rain"
                elif temperature > params["base_temp"] + params["temp_variation"]:
                    condition = "Hot"
                elif temperature < params["base_temp"] - params["temp_variation"]:
                    condition = "Cold"
                else:
                    condition = "Clear"
            
            # Generate humidity
            humidity_base = 60 + (20 * season_params["humidity_modifier"])
            humidity = humidity_base + rain_trend * 10
            
            # Generate wind speed
            wind_speed = 5 + random.random() * 15
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day,
                "season": season,
                "temperature_high_c": round(temperature + temp_variation / 2, 1),
                "temperature_low_c": round(temperature - temp_variation / 2, 1),
                "rainfall_mm": round(rainfall, 1),
                "humidity_percent": round(humidity, 1),
                "wind_speed_kph": round(wind_speed, 1),
                "condition": condition
            })
            
            # Store forecast in database
            self.db.log_agent_interaction(
                agent_name=self.name,
                action_type="forecast_generation",
                action_details=f"Generated forecast for {region}, day {day}: {condition}"
            )
        
        return forecast
    
    def generate_historical_data(self, region, specific_date=None, days=30):
        """
        Generate simulated historical weather data.
        
        Args:
            region (str): Geographic region
            specific_date (datetime): Specific date for historical data
            days (int): Number of days of historical data
            
        Returns:
            list: Historical weather data
        """
        historical_data = []
        params = self.regions[region]
        
        # Set end date
        if specific_date:
            end_date = specific_date
        else:
            end_date = datetime.now() - timedelta(days=1)
        
        # Generate data for each day
        for day in range(days):
            date = end_date - timedelta(days=day)
            season = self.get_current_season(date)
            season_params = self.seasons[season]
            
            # Calculate temperature with seasonal factors
            temp_base = params["base_temp"] + (season_params["temp_modifier"] * params["seasonal_factor"])
            temp_variation = params["temp_variation"] * (0.8 + 0.4 * random.random())
            temperature = temp_base + (random.random() * 2 - 1) * temp_variation
            
            # Calculate rainfall with seasonal factors
            rainfall_base = params["base_rainfall"] * season_params["rainfall_modifier"]
            rainfall = random.random() * params["rainfall_variation"] * rainfall_base
            
            # Generate humidity
            humidity_base = 60 + (20 * season_params["humidity_modifier"])
            humidity = humidity_base + (random.random() * 20 - 10)
            
            # Generate wind speed
            wind_speed = 5 + random.random() * 15
            
            # Determine condition
            if rainfall > params["rainfall_variation"]:
                condition = "Heavy Rain"
            elif rainfall > params["rainfall_variation"] / 2:
                condition = "Light Rain"
            elif temperature > params["base_temp"] + params["temp_variation"]:
                condition = "Hot"
            elif temperature < params["base_temp"] - params["temp_variation"]:
                condition = "Cold"
            else:
                condition = "Clear"
            
            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "season": season,
                "temperature_high_c": round(temperature + temp_variation / 2, 1),
                "temperature_low_c": round(temperature - temp_variation / 2, 1),
                "rainfall_mm": round(rainfall, 1),
                "humidity_percent": round(humidity, 1),
                "wind_speed_kph": round(wind_speed, 1),
                "condition": condition
            })
        
        return historical_data
    
    def assess_agricultural_impact(self, current_weather, forecast, region):
        """
        Assess the agricultural impact of current and forecasted weather.
        
        Args:
            current_weather (dict): Current weather data
            forecast (list): Weather forecast
            region (str): Geographic region
            
        Returns:
            dict: Agricultural impact assessment
        """
        # Calculate average forecast values
        avg_temp = sum(day["temperature_high_c"] for day in forecast) / len(forecast)
        avg_rainfall = sum(day["rainfall_mm"] for day in forecast)  # Total rainfall
        
        # Initialize impact assessment
        impact = {
            "temperature_impact": "neutral",
            "rainfall_impact": "neutral",
            "overall_impact": "neutral",
            "recommendations": []
        }
        
        # Assess temperature impact
        if avg_temp > 30:
            impact["temperature_impact"] = "negative"
            impact["recommendations"].append({
                "issue": "High temperatures forecasted",
                "action": "Implement shade structures and increase irrigation frequency",
                "sustainability_impact": 1.8,
                "confidence": 0.8
            })
        elif avg_temp < 10:
            impact["temperature_impact"] = "negative"
            impact["recommendations"].append({
                "issue": "Low temperatures forecasted",
                "action": "Consider using crop covers or delaying planting",
                "sustainability_impact": 1.5,
                "confidence": 0.8
            })
        elif 15 <= avg_temp <= 28:
            impact["temperature_impact"] = "positive"
        
        # Assess rainfall impact
        if avg_rainfall < 10:
            impact["rainfall_impact"] = "negative"
            impact["recommendations"].append({
                "issue": "Low rainfall forecasted",
                "action": "Implement water conservation techniques and drip irrigation",
                "sustainability_impact": 2.2,
                "confidence": 0.85
            })
        elif avg_rainfall > 100:
            impact["rainfall_impact"] = "negative"
            impact["recommendations"].append({
                "issue": "High rainfall forecasted",
                "action": "Ensure proper drainage and consider delayed planting",
                "sustainability_impact": 1.7,
                "confidence": 0.8
            })
        elif 20 <= avg_rainfall <= 60:
            impact["rainfall_impact"] = "positive"
        
        # Check for extreme conditions in the forecast
        extreme_conditions = [
            day for day in forecast 
            if day["condition"] in ["Drought Conditions", "Flood Warning"]
        ]
        
        if extreme_conditions:
            for condition in extreme_conditions:
                if condition["condition"] == "Drought Conditions":
                    impact["recommendations"].append({
                        "issue": f"Drought conditions forecasted on {condition['date']}",
                        "action": "Implement emergency water conservation measures and consider drought-resistant crops",
                        "sustainability_impact": 2.5,
                        "confidence": 0.7
                    })
                elif condition["condition"] == "Flood Warning":
                    impact["recommendations"].append({
                        "issue": f"Flood warning for {condition['date']}",
                        "action": "Prepare flood defenses and ensure drainage systems are clear",
                        "sustainability_impact": 2.0,
                        "confidence": 0.7
                    })
        
        # Determine overall impact
        if impact["temperature_impact"] == "negative" or impact["rainfall_impact"] == "negative":
            impact["overall_impact"] = "negative"
        elif impact["temperature_impact"] == "positive" and impact["rainfall_impact"] == "positive":
            impact["overall_impact"] = "positive"
        
        # Add crop-specific recommendations based on current season
        current_season = self.get_current_season()
        
        if current_season == "spring":
            impact["recommendations"].append({
                "issue": "Spring planting considerations",
                "action": "Ensure soil has proper temperature and moisture before planting to optimize germination",
                "sustainability_impact": 1.5,
                "confidence": 0.9
            })
        elif current_season == "summer":
            impact["recommendations"].append({
                "issue": "Summer heat management",
                "action": "Monitor soil moisture levels closely and implement shading or mulching to reduce evaporation",
                "sustainability_impact": 1.8,
                "confidence": 0.85
            })
        elif current_season == "fall":
            impact["recommendations"].append({
                "issue": "Fall harvest timing",
                "action": "Monitor forecasts for early frost and plan harvest accordingly",
                "sustainability_impact": 1.6,
                "confidence": 0.8
            })
        elif current_season == "winter":
            impact["recommendations"].append({
                "issue": "Winter soil management",
                "action": "Consider cover crops to protect soil from erosion and improve structure",
                "sustainability_impact": 2.0,
                "confidence": 0.85
            })
        
        return impact
    
    def generate_recommendations(self, context):
        """
        Generate weather-based recommendations for farming practices.
        
        Args:
            context (dict): Context for generating recommendations
                - farm_id: Farm ID (optional)
                - region: Geographic region
                - crop_type: Current crop type (optional)
                
        Returns:
            list: Weather-based recommendations
        """
        self.log_action("recommendation_generation", f"Generating weather recommendations for: {str(context)[:100]}...")
        
        farm_id = context.get("farm_id")
        region = context.get("region", "central")
        crop_type = context.get("crop_type")
        
        if region not in self.regions:
            return {"status": "error", "message": f"Unknown region: {region}"}
        
        # Get current weather and forecast
        current_weather = self.generate_current_weather(region)
        forecast = self.generate_forecast(region, days=14)  # 14-day forecast
        
        # Generate impact assessment
        impact = self.assess_agricultural_impact(current_weather, forecast, region)
        
        # Create categorized recommendations
        recommendations = []
        
        # 1. Short-term weather management
        short_term_recs = []
        for i, day in enumerate(forecast[:7]):  # Next 7 days
            if day["condition"] in ["Heavy Rain", "Flood Warning"]:
                short_term_recs.append({
                    "focus": f"Heavy Rain Management: Day {i+1}",
                    "action": "Ensure proper drainage and avoid field operations to prevent soil compaction",
                    "sustainability_impact": 1.8,
                    "confidence": 0.85 - (i * 0.05)  # Confidence decreases with forecast distance
                })
            elif day["condition"] in ["Drought Conditions", "Hot"] and day["rainfall_mm"] < 2:
                short_term_recs.append({
                    "focus": f"Drought Management: Day {i+1}",
                    "action": "Schedule irrigation for early morning to minimize evaporation",
                    "sustainability_impact": 2.0,
                    "confidence": 0.85 - (i * 0.05)
                })
        
        if short_term_recs:
            recommendations.append({
                "category": "Short-term Weather Management",
                "recommendations": short_term_recs[:3],  # Limit to top 3
                "explanation": "Immediate actions based on 7-day weather forecast"
            })
        
        # 2. Seasonal planning
        seasonal_recs = []
        current_season = self.get_current_season()
        next_season = list(self.seasons.keys())[(list(self.seasons.keys()).index(current_season) + 1) % 4]
        
        # Current season recommendations
        if current_season == "spring":
            seasonal_recs.append({
                "focus": "Spring Planting",
                "action": "Monitor soil temperature and moisture daily; wait for soil to warm sufficiently before planting",
                "sustainability_impact": 1.6,
                "confidence": 0.9
            })
        elif current_season == "summer":
            seasonal_recs.append({
                "focus": "Summer Heat Management",
                "action": "Implement mulching to conserve soil moisture and reduce irrigation needs",
                "sustainability_impact": 1.9,
                "confidence": 0.85
            })
        elif current_season == "fall":
            seasonal_recs.append({
                "focus": "Fall Preparations",
                "action": "Plan cover crop planting to protect soil through winter and improve fertility",
                "sustainability_impact": 2.1,
                "confidence": 0.9
            })
        elif current_season == "winter":
            seasonal_recs.append({
                "focus": "Winter Planning",
                "action": "Use this time for soil testing and planning crop rotations for next growing season",
                "sustainability_impact": 1.7,
                "confidence": 0.9
            })
        
        # Next season preparation
        seasonal_recs.append({
            "focus": f"{next_season.capitalize()} Preparation",
            "action": f"Begin preparing for {next_season} conditions by reviewing expected weather patterns and adjusting plans accordingly",
            "sustainability_impact": 1.5,
            "confidence": 0.8
        })
        
        recommendations.append({
            "category": "Seasonal Planning",
            "recommendations": seasonal_recs,
            "explanation": f"Recommendations for current {current_season} conditions and preparation for upcoming {next_season}"
        })
        
        # 3. Water management
        avg_rainfall = sum(day["rainfall_mm"] for day in forecast[:14]) / 14
        water_recs = []
        
        if avg_rainfall < 3:
            water_recs.append({
                "focus": "Drought Mitigation",
                "action": "Implement rainwater harvesting systems and water-efficient irrigation methods such as drip irrigation",
                "sustainability_impact": 2.3,
                "confidence": 0.8
            })
        elif avg_rainfall > 7:
            water_recs.append({
                "focus": "Excess Water Management",
                "action": "Ensure proper drainage systems are in place and consider raised beds for water-sensitive crops",
                "sustainability_impact": 1.8,
                "confidence": 0.8
            })
        
        # General water conservation
        water_recs.append({
            "focus": "Water Conservation",
            "action": "Install soil moisture sensors to optimize irrigation scheduling and prevent over-watering",
            "sustainability_impact": 2.0,
            "confidence": 0.9
        })
        
        recommendations.append({
            "category": "Water Management",
            "recommendations": water_recs,
            "explanation": "Strategies for sustainable water usage based on precipitation forecasts"
        })
        
        # Store recommendations in database if farm_id is available
        if farm_id:
            for category in recommendations:
                for rec in category["recommendations"]:
                    self.db.add_recommendation(
                        farm_id=farm_id,
                        rec_type=category["category"],
                        rec_text=rec["action"],
                        sustainability_impact=rec.get("sustainability_impact", 0),
                        economic_impact=0,  # Weather station focuses on sustainability
                        confidence_score=rec.get("confidence", 0)
                    )
        
        return recommendations
    
    def receive_message(self, sender_agent, message):
        """
        Receive and process a message from another agent or the web interface.
        
        Args:
            sender_agent: The agent that sent the message
            message: The received message
            
        Returns:
            dict: Response to the sender
        """
        self.log_action(
            action_type="communication",
            action_details=f"Received message from {sender_agent.name}: {str(message)[:100]}..."
        )
        
        # Handle web interface request
        if sender_agent.name == "Web User":
            # Get parameters from the message
            user_message = message.get("message", "")
            # Use provided region or extract from message
            if message.get("request_type") == "weather_forecast":
                region = message.get("region", "central")
                days = message.get("days", 7)
            else:
                # Try to extract region from message
                region = self.extract_region_from_message(user_message)
                if not region:
                    region = "central"  # Default
                days = self.extract_days_from_message(user_message) or 7
            
            # Generate forecast
            if region in self.regions:
                current_weather = self.generate_current_weather(region)
                forecast = self.generate_forecast(region, days)
                impact = self.assess_agricultural_impact(current_weather, forecast, region)
                
                # Format the response for display
                response_text = f"Weather Forecast for {region.capitalize()} Region:\n\n"
                
                # Current weather
                response_text += "Current Weather:\n"
                response_text += f"Temperature: {current_weather['temperature_c']}°C\n"
                response_text += f"Condition: {current_weather['condition']}\n"
                response_text += f"Humidity: {current_weather['humidity_percent']}%\n"
                response_text += f"Wind: {current_weather['wind_speed_kph']} km/h\n\n"
                
                # Forecast
                response_text += f"{days}-Day Forecast:\n"
                for day in forecast:
                    response_text += f"• {day['date']}: {day['condition']}, "
                    response_text += f"{day['temperature_high_c']}°C / {day['temperature_low_c']}°C, "
                    response_text += f"Rain: {day['rainfall_mm']}mm\n"
                
                # Agricultural impact
                response_text += "\nAgricultural Impact:\n"
                response_text += f"Temperature Impact: {impact['temperature_impact'].capitalize()}\n"
                response_text += f"Rainfall Impact: {impact['rainfall_impact'].capitalize()}\n"
                response_text += f"Overall Impact: {impact['overall_impact'].capitalize()}\n"
                
                # Recommendations
                if impact['recommendations']:
                    response_text += "\nRecommendations:\n"
                    for rec in impact['recommendations']:
                        response_text += f"• {rec['action']}\n"
                
                return {
                    "status": "success",
                    "response": response_text,
                    "region": region,
                    "forecast": forecast,
                    "agricultural_impact": impact
                }
            else:
                return {
                    "status": "error", 
                    "response": f"Unknown region: {region}. Please specify north, central, or south region."
                }
        
        elif sender_agent.name == "Farmer Advisor":
            # Handle specific request types from Farmer Advisor
            if message.get("request_type") == "weather_forecast":
                region = message.get("region", "central")
                days = message.get("days", 7)
                
                if region in self.regions:
                    # Generate forecast
                    forecast = self.generate_forecast(region, days)
                    impact = self.assess_agricultural_impact(
                        self.generate_current_weather(region),
                        forecast,
                        region
                    )
                    
                    return {
                        "status": "success",
                        "region": region,
                        "forecast": forecast,
                        "agricultural_impact": impact
                    }
                else:
                    return {"status": "error", "message": f"Unknown region: {region}"}
            
            elif message.get("request_type") == "planting_advice":
                region = message.get("region", "central")
                crop_type = message.get("crop_type")
                
                if not crop_type:
                    return {"status": "error", "message": "No crop type specified"}
                
                if region not in self.regions:
                    return {"status": "error", "message": f"Unknown region: {region}"}
                
                # Get current weather and forecast
                current = self.generate_current_weather(region)
                forecast = self.generate_forecast(region, 14)
                
                # Basic planting advice based on weather
                advice = {
                    "current_season": current["season"],
                    "recommendations": []
                }
                
                # Check rainfall forecast
                total_rainfall = sum(day["rainfall_mm"] for day in forecast[:7])
                if total_rainfall < 10:
                    advice["recommendations"].append({
                        "issue": "Low rainfall expected",
                        "action": "Consider delaying planting until rainfall increases or ensure irrigation is available",
                        "sustainability_impact": 2.0,
                        "confidence": 0.75
                    })
                
                # Check temperature forecast
                avg_low = sum(day["temperature_low_c"] for day in forecast[:7]) / 7
                if crop_type.lower() == "corn" and avg_low < 10:
                    advice["recommendations"].append({
                        "issue": "Soil temperatures likely too low for corn germination",
                        "action": "Delay corn planting until soil temperatures are consistently above 10°C",
                        "sustainability_impact": 1.8,
                        "confidence": 0.8
                    })
                elif crop_type.lower() == "wheat" and current["season"] == "fall":
                    advice["recommendations"].append({
                        "issue": "Optimal fall wheat planting window",
                        "action": "Plant winter wheat now for optimal establishment before frost",
                        "sustainability_impact": 1.5,
                        "confidence": 0.85
                    })
                
                # Add general recommendation
                advice["recommendations"].append({
                    "issue": "Weather-based planting timing",
                    "action": f"Monitor soil moisture and temperature daily; ideal planting conditions for {crop_type} are approaching",
                    "sustainability_impact": 1.7,
                    "confidence": 0.8
                })
                
                return {
                    "status": "success",
                    "crop_type": crop_type,
                    "planting_advice": advice
                }
        
        # Default implementation for other agents
        return {"status": "received", "message": "Message received by Weather Station"}
    
    def extract_region_from_message(self, message):
        """Extract region mentions from a user message."""
        message_lower = message.lower()
        
        # Check for direct region mentions
        if "north" in message_lower:
            return "north"
        elif "south" in message_lower:
            return "south"
        elif "central" in message_lower:
            return "central"
        
        # No specific region found
        return None
        
    def extract_days_from_message(self, message):
        """Extract number of days from a user message."""
        import re
        
        # Patterns for day/days mentions
        days_patterns = [
            r"(\d+)[\s-]*day(?:s)?",
            r"next (\d+) day(?:s)?",
            r"(\d+)[\s-]*day forecast"
        ]
        
        for pattern in days_patterns:
            match = re.search(pattern, message.lower())
            if match:
                try:
                    days = int(match.group(1))
                    # Cap at 14 days for reasonable forecasts
                    return min(days, 14)
                except ValueError:
                    pass
        
        return None 