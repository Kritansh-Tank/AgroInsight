import pandas as pd
import numpy as np
from agents.base_agent import BaseAgent
from utils.data_loader import get_crop_sustainability_ranking, get_fertilizer_efficiency_by_crop

class FarmerAdvisor(BaseAgent):
    """
    Farmer Advisor agent that provides actionable insights by analyzing input
    from the farmer about land, crop preferences, and financial goals.
    
    The agent uses farm data to recommend sustainable practices that optimize
    resource usage while meeting the farmer's goals.
    """
    
    def __init__(self, db_connection):
        """Initialize the Farmer Advisor agent."""
        super().__init__("Farmer Advisor", db_connection)
        self.farm_data = None
        self.load_farm_data()
    
    def load_farm_data(self):
        """Load farm data from the database."""
        self.farm_data = self.db.get_farm_data()
        self.log_action(
            action_type="data_loading",
            action_details=f"Loaded farm data: {len(self.farm_data) if self.farm_data else 0} records"
        )
        
        if self.farm_data:
            # Convert to DataFrame for easier analysis
            self.farm_df = pd.DataFrame(self.farm_data)
            self.update_state("farm_data_loaded", True)
        else:
            self.update_state("farm_data_loaded", False)
    
    def process_input(self, input_data):
        """
        Process input data from the farmer.
        
        Args:
            input_data (dict): Data containing information about the farm and farmer preferences
                - farm_id: If existing farm
                - soil_ph: Soil pH level (if new farm)
                - soil_moisture: Soil moisture level (if new farm)
                - temperature_c: Average temperature in Celsius (if new farm)
                - rainfall_mm: Average rainfall in mm (if new farm)
                - current_crop: Current crop type (if any)
                - financial_goal: "maximize_profit", "minimize_cost", or "balance"
                - sustainability_preference: Value from 1-10 indicating importance of sustainability
        
        Returns:
            dict: Processed data and initial analysis
        """
        self.log_action("input_processing", f"Processing farmer input: {str(input_data)[:100]}...")
        
        # Store the input in state
        self.update_state("farmer_input", input_data)
        
        # Process the input
        farm_id = input_data.get("farm_id")
        
        if farm_id:
            # Get existing farm data
            farm_data = self.db.get_farm_data(farm_id)
            if not farm_data:
                return {"status": "error", "message": f"Farm ID {farm_id} not found"}
            
            self.update_state("current_farm", farm_data)
            
            # Analyze the farm data
            analysis = self.analyze_farm(farm_data)
            return {
                "status": "success",
                "farm_data": farm_data,
                "analysis": analysis
            }
        else:
            # New farm being registered
            # Only basic analysis possible until more data is collected
            return {
                "status": "success",
                "message": "New farm registered. Basic analysis provided.",
                "soil_analysis": self.analyze_soil_data({
                    "soil_ph": input_data.get("soil_ph"),
                    "soil_moisture": input_data.get("soil_moisture")
                }),
                "climate_analysis": self.analyze_climate_data({
                    "temperature_c": input_data.get("temperature_c"),
                    "rainfall_mm": input_data.get("rainfall_mm")
                })
            }
    
    def analyze_farm(self, farm_data):
        """
        Perform a comprehensive analysis of a farm.
        
        Args:
            farm_data (dict): Farm data to analyze
            
        Returns:
            dict: Analysis results
        """
        # Convert to DataFrame if it's not already
        if isinstance(farm_data, dict):
            farm_df = pd.DataFrame([farm_data])
        else:
            farm_df = pd.DataFrame(farm_data)
        
        # Get basic analyses
        soil_analysis = self.analyze_soil_data({
            "soil_ph": farm_df.iloc[0]["soil_ph"],
            "soil_moisture": farm_df.iloc[0]["soil_moisture"]
        })
        
        climate_analysis = self.analyze_climate_data({
            "temperature_c": farm_df.iloc[0]["temperature_c"],
            "rainfall_mm": farm_df.iloc[0]["rainfall_mm"]
        })
        
        # Analyze current farming practices
        practice_analysis = self.analyze_farming_practices({
            "crop_type": farm_df.iloc[0]["crop_type"],
            "fertilizer_usage_kg": farm_df.iloc[0]["fertilizer_usage_kg"],
            "pesticide_usage_kg": farm_df.iloc[0]["pesticide_usage_kg"],
            "crop_yield_ton": farm_df.iloc[0]["crop_yield_ton"],
            "sustainability_score": farm_df.iloc[0]["sustainability_score"]
        })
        
        # Compile the analysis
        return {
            "soil_analysis": soil_analysis,
            "climate_analysis": climate_analysis,
            "practice_analysis": practice_analysis,
            "sustainability_score": float(farm_df.iloc[0]["sustainability_score"]),
            "overall_assessment": self.generate_overall_assessment(
                soil_analysis, climate_analysis, practice_analysis, 
                float(farm_df.iloc[0]["sustainability_score"])
            )
        }
    
    def analyze_soil_data(self, soil_data):
        """
        Analyze soil data and provide insights.
        
        Args:
            soil_data (dict): Soil data including pH and moisture
            
        Returns:
            dict: Soil analysis results
        """
        soil_ph = soil_data.get("soil_ph")
        soil_moisture = soil_data.get("soil_moisture")
        
        results = {
            "soil_ph": soil_ph,
            "soil_moisture": soil_moisture,
            "recommendations": []
        }
        
        # pH analysis
        if soil_ph is not None:
            if soil_ph < 5.5:
                results["ph_status"] = "acidic"
                results["recommendations"].append({
                    "issue": "Low soil pH (acidic)",
                    "action": "Apply agricultural lime to raise pH",
                    "sustainability_impact": 1.5,
                    "cost_impact": -0.8  # Negative means it costs money
                })
            elif soil_ph > 7.5:
                results["ph_status"] = "alkaline"
                results["recommendations"].append({
                    "issue": "High soil pH (alkaline)",
                    "action": "Apply organic matter or elemental sulfur to lower pH",
                    "sustainability_impact": 1.2,
                    "cost_impact": -0.5
                })
            else:
                results["ph_status"] = "optimal"
        
        # Moisture analysis
        if soil_moisture is not None:
            if soil_moisture < 20:
                results["moisture_status"] = "dry"
                results["recommendations"].append({
                    "issue": "Low soil moisture",
                    "action": "Implement drip irrigation system and mulching to conserve water",
                    "sustainability_impact": 2.0,
                    "cost_impact": -1.2
                })
            elif soil_moisture > 40:
                results["moisture_status"] = "wet"
                results["recommendations"].append({
                    "issue": "High soil moisture",
                    "action": "Improve drainage and consider raised beds",
                    "sustainability_impact": 1.0,
                    "cost_impact": -0.9
                })
            else:
                results["moisture_status"] = "optimal"
        
        return results
    
    def analyze_climate_data(self, climate_data):
        """
        Analyze climate data and provide insights.
        
        Args:
            climate_data (dict): Climate data including temperature and rainfall
            
        Returns:
            dict: Climate analysis results
        """
        temperature = climate_data.get("temperature_c")
        rainfall = climate_data.get("rainfall_mm")
        
        results = {
            "temperature_c": temperature,
            "rainfall_mm": rainfall,
            "recommendations": []
        }
        
        # Temperature analysis
        if temperature is not None:
            if temperature < 18:
                results["temperature_category"] = "cool"
                results["suitable_crops"] = ["Wheat", "Barley", "Oats"]
            elif temperature > 30:
                results["temperature_category"] = "hot"
                results["suitable_crops"] = ["Corn", "Sorghum", "Cotton"]
            else:
                results["temperature_category"] = "moderate"
                results["suitable_crops"] = ["Rice", "Soybean", "Corn", "Wheat"]
        
        # Rainfall analysis
        if rainfall is not None:
            if rainfall < 100:
                results["rainfall_category"] = "low"
                results["recommendations"].append({
                    "issue": "Low rainfall",
                    "action": "Implement water harvesting and drought-resistant crops",
                    "sustainability_impact": 2.5,
                    "cost_impact": -1.5
                })
            elif rainfall > 250:
                results["rainfall_category"] = "high"
                results["recommendations"].append({
                    "issue": "High rainfall",
                    "action": "Ensure good drainage and consider raised beds",
                    "sustainability_impact": 1.0,
                    "cost_impact": -0.7
                })
            else:
                results["rainfall_category"] = "moderate"
        
        return results
    
    def analyze_farming_practices(self, practice_data):
        """
        Analyze current farming practices and suggest improvements.
        
        Args:
            practice_data (dict): Data about current farming practices
            
        Returns:
            dict: Analysis and recommendations
        """
        # Get all farms growing the same crop for comparison
        crop_type = practice_data.get("crop_type")
        similar_farms = [farm for farm in self.farm_data if farm["crop_type"] == crop_type]
        
        if not similar_farms:
            return {
                "status": "insufficient_data",
                "message": f"No comparative data available for {crop_type}"
            }
        
        # Convert to DataFrame for analysis
        similar_farms_df = pd.DataFrame(similar_farms)
        
        # Calculate benchmarks
        avg_fertilizer = similar_farms_df["fertilizer_usage_kg"].mean()
        avg_pesticide = similar_farms_df["pesticide_usage_kg"].mean()
        avg_yield = similar_farms_df["crop_yield_ton"].mean()
        avg_sustainability = similar_farms_df["sustainability_score"].mean()
        
        # Compare with current farm
        current_fertilizer = practice_data.get("fertilizer_usage_kg")
        current_pesticide = practice_data.get("pesticide_usage_kg")
        current_yield = practice_data.get("crop_yield_ton")
        current_sustainability = practice_data.get("sustainability_score")
        
        # Calculate efficiency metrics
        fertilizer_efficiency = current_yield / current_fertilizer if current_fertilizer else 0
        pesticide_efficiency = current_yield / current_pesticide if current_pesticide else 0
        
        avg_fertilizer_efficiency = avg_yield / avg_fertilizer if avg_fertilizer else 0
        avg_pesticide_efficiency = avg_yield / avg_pesticide if avg_pesticide else 0
        
        # Prepare recommendations
        recommendations = []
        
        if current_fertilizer > avg_fertilizer * 1.2:
            recommendations.append({
                "issue": "High fertilizer usage",
                "action": "Consider precision agriculture techniques to optimize fertilizer application",
                "sustainability_impact": 2.0,
                "cost_impact": 0.5  # Positive means it saves money
            })
        
        if current_pesticide > avg_pesticide * 1.2:
            recommendations.append({
                "issue": "High pesticide usage",
                "action": "Implement integrated pest management (IPM) techniques",
                "sustainability_impact": 2.5,
                "cost_impact": 0.3
            })
        
        if current_yield < avg_yield * 0.8:
            recommendations.append({
                "issue": "Below average crop yield",
                "action": "Consider soil testing and targeted nutrient management",
                "sustainability_impact": 1.0,
                "cost_impact": -0.2
            })
        
        return {
            "benchmarks": {
                "avg_fertilizer_usage_kg": avg_fertilizer,
                "avg_pesticide_usage_kg": avg_pesticide,
                "avg_crop_yield_ton": avg_yield,
                "avg_sustainability_score": avg_sustainability
            },
            "current_performance": {
                "fertilizer_usage_kg": current_fertilizer,
                "pesticide_usage_kg": current_pesticide,
                "crop_yield_ton": current_yield,
                "sustainability_score": current_sustainability
            },
            "efficiency_metrics": {
                "fertilizer_efficiency": fertilizer_efficiency,
                "pesticide_efficiency": pesticide_efficiency,
                "vs_avg_fertilizer_efficiency": (fertilizer_efficiency / avg_fertilizer_efficiency - 1) * 100 if avg_fertilizer_efficiency else 0,
                "vs_avg_pesticide_efficiency": (pesticide_efficiency / avg_pesticide_efficiency - 1) * 100 if avg_pesticide_efficiency else 0
            },
            "recommendations": recommendations
        }
    
    def generate_overall_assessment(self, soil_analysis, climate_analysis, practice_analysis, sustainability_score):
        """
        Generate an overall assessment based on all analysis components.
        
        Args:
            soil_analysis (dict): Soil analysis results
            climate_analysis (dict): Climate analysis results
            practice_analysis (dict): Practice analysis results
            sustainability_score (float): Current sustainability score
            
        Returns:
            dict: Overall assessment and high-priority recommendations
        """
        # Collect all recommendations
        all_recommendations = []
        
        if "recommendations" in soil_analysis:
            all_recommendations.extend(soil_analysis["recommendations"])
        
        if "recommendations" in climate_analysis:
            all_recommendations.extend(climate_analysis["recommendations"])
        
        if "recommendations" in practice_analysis:
            all_recommendations.extend(practice_analysis["recommendations"])
        
        # Sort recommendations by sustainability impact
        sorted_recommendations = sorted(
            all_recommendations, 
            key=lambda x: x.get("sustainability_impact", 0), 
            reverse=True
        )
        
        # Categorize the farm
        if sustainability_score < 30:
            sustainability_category = "poor"
            improvement_potential = "high"
        elif sustainability_score < 60:
            sustainability_category = "moderate"
            improvement_potential = "medium"
        else:
            sustainability_category = "good"
            improvement_potential = "low"
        
        return {
            "sustainability_category": sustainability_category,
            "improvement_potential": improvement_potential,
            "high_priority_recommendations": sorted_recommendations[:3] if sorted_recommendations else [],
            "overall_message": self.generate_message(sustainability_category, improvement_potential)
        }
    
    def generate_message(self, sustainability_category, improvement_potential):
        """Generate an overall message based on sustainability category."""
        if sustainability_category == "poor" and improvement_potential == "high":
            return ("Your farm's sustainability score needs significant improvement. "
                    "Implementing our high-priority recommendations could substantially "
                    "increase your sustainability while potentially reducing costs over time.")
        elif sustainability_category == "moderate" and improvement_potential == "medium":
            return ("Your farm has a moderate sustainability score. With targeted improvements "
                    "in resource management and sustainable practices, you can enhance both "
                    "sustainability and productivity.")
        else:
            return ("Your farm shows good sustainability practices. Continue to optimize "
                    "and consider the recommended refinements to maintain your positive "
                    "environmental impact and potentially improve efficiency further.")
    
    def generate_recommendations(self, context):
        """
        Generate detailed recommendations based on context.
        
        Args:
            context (dict): Context data containing farm info and preferences
                - farm_id: Farm ID
                - financial_goal: Financial goal of the farmer
                - sustainability_preference: Importance of sustainability (1-10)
                
        Returns:
            list: Detailed recommendations
        """
        self.log_action("recommendation_generation", f"Generating recommendations for: {str(context)[:100]}...")
        
        farm_id = context.get("farm_id")
        financial_goal = context.get("financial_goal", "balance")
        sustainability_preference = context.get("sustainability_preference", 5)
        
        # Get farm data
        farm_data = self.db.get_farm_data(farm_id)
        if not farm_data:
            return {"status": "error", "message": f"Farm ID {farm_id} not found"}
        
        # Get crop rankings
        crop_sustainability = get_crop_sustainability_ranking(self.farm_df)
        fertilizer_efficiency = get_fertilizer_efficiency_by_crop(self.farm_df)
        
        # Generate comprehensive recommendations
        recommendations = []
        
        # 1. Crop recommendations based on soil, climate, and market
        crop_recs = self.recommend_crops(farm_data, financial_goal, sustainability_preference)
        recommendations.append({
            "category": "Crop Selection",
            "recommendations": crop_recs,
            "explanation": "Crop selection based on your soil conditions, climate, and market demand"
        })
        
        # 2. Resource optimization recommendations
        resource_recs = self.recommend_resource_optimization(farm_data, sustainability_preference)
        recommendations.append({
            "category": "Resource Optimization",
            "recommendations": resource_recs,
            "explanation": "Optimizing resource usage to reduce environmental impact and costs"
        })
        
        # 3. Sustainable practice recommendations
        practice_recs = self.recommend_sustainable_practices(farm_data, sustainability_preference)
        recommendations.append({
            "category": "Sustainable Practices",
            "recommendations": practice_recs,
            "explanation": "Sustainable farming practices to improve long-term soil health and productivity"
        })
        
        # Store recommendations in database
        for category in recommendations:
            for rec in category["recommendations"]:
                self.db.add_recommendation(
                    farm_id=farm_id,
                    rec_type=category["category"],
                    rec_text=rec["action"],
                    sustainability_impact=rec.get("sustainability_impact", 0),
                    economic_impact=rec.get("economic_impact", 0),
                    confidence_score=rec.get("confidence", 0)
                )
        
        return recommendations
    
    def recommend_crops(self, farm_data, financial_goal, sustainability_preference):
        """
        Recommend crops based on farm conditions and preferences.
        
        Args:
            farm_data (dict): Farm data
            financial_goal (str): Financial goal of the farmer
            sustainability_preference (int): Importance of sustainability (1-10)
            
        Returns:
            list: Crop recommendations
        """
        # Simple implementation - in a real system this would be more sophisticated
        soil_ph = farm_data["soil_ph"]
        soil_moisture = farm_data["soil_moisture"]
        temperature = farm_data["temperature_c"]
        rainfall = farm_data["rainfall_mm"]
        
        recommendations = []
        
        # Recommend crops based on conditions
        if soil_ph < 6.0:
            if temperature < 25 and rainfall > 200:
                recommendations.append({
                    "crop": "Rice",
                    "action": "Consider planting Rice which performs well in acidic soils with high rainfall",
                    "sustainability_impact": 1.5,
                    "economic_impact": 1.8,
                    "confidence": 0.8
                })
        elif soil_ph >= 6.0 and soil_ph <= 7.0:
            if soil_moisture > 30:
                recommendations.append({
                    "crop": "Corn",
                    "action": "Consider planting Corn which performs well in neutral soils with good moisture",
                    "sustainability_impact": 1.7,
                    "economic_impact": 2.0,
                    "confidence": 0.85
                })
            else:
                recommendations.append({
                    "crop": "Wheat",
                    "action": "Consider planting Wheat which performs well in neutral soils with moderate moisture",
                    "sustainability_impact": 1.8,
                    "economic_impact": 1.6,
                    "confidence": 0.8
                })
        else:  # pH > 7.0
            recommendations.append({
                "crop": "Soybean",
                "action": "Consider planting Soybean which can perform well in slightly alkaline soils",
                "sustainability_impact": 2.0,
                "economic_impact": 1.7,
                "confidence": 0.75
            })
        
        # If sustainability is a high priority, add additional recommendations
        if sustainability_preference > 7:
            recommendations.append({
                "crop": "Crop Rotation",
                "action": "Implement a crop rotation system including nitrogen-fixing legumes to improve soil health",
                "sustainability_impact": 2.5,
                "economic_impact": 1.0,
                "confidence": 0.9
            })
        
        return recommendations
    
    def recommend_resource_optimization(self, farm_data, sustainability_preference):
        """
        Recommend resource optimization strategies.
        
        Args:
            farm_data (dict): Farm data
            sustainability_preference (int): Importance of sustainability (1-10)
            
        Returns:
            list: Resource optimization recommendations
        """
        fertilizer_usage = farm_data["fertilizer_usage_kg"]
        pesticide_usage = farm_data["pesticide_usage_kg"]
        rainfall = farm_data["rainfall_mm"]
        
        recommendations = []
        
        # Water management
        if rainfall < 150:
            recommendations.append({
                "resource": "Water",
                "action": "Implement drip irrigation and rainwater harvesting to optimize water usage",
                "sustainability_impact": 2.2,
                "economic_impact": 0.8,
                "confidence": 0.85
            })
        
        # Fertilizer optimization
        if fertilizer_usage > 120:
            recommendations.append({
                "resource": "Fertilizer",
                "action": "Implement precision agriculture techniques for targeted fertilizer application",
                "sustainability_impact": 2.0,
                "economic_impact": 1.2,
                "confidence": 0.8
            })
        
        # Pesticide optimization
        if pesticide_usage > 10:
            recommendations.append({
                "resource": "Pesticides",
                "action": "Adopt integrated pest management (IPM) to reduce chemical pesticide usage",
                "sustainability_impact": 2.5,
                "economic_impact": 0.9,
                "confidence": 0.85
            })
        
        # For all farms, recommend soil health management
        recommendations.append({
            "resource": "Soil",
            "action": "Implement cover cropping and minimal tillage to improve soil health and reduce erosion",
            "sustainability_impact": 2.3,
            "economic_impact": 1.0,
            "confidence": 0.9
        })
        
        return recommendations
    
    def recommend_sustainable_practices(self, farm_data, sustainability_preference):
        """
        Recommend sustainable farming practices.
        
        Args:
            farm_data (dict): Farm data
            sustainability_preference (int): Importance of sustainability (1-10)
            
        Returns:
            list: Sustainable practice recommendations
        """
        # Current practices
        current_crop = farm_data["crop_type"]
        
        recommendations = []
        
        # Basic sustainable practices for all farms
        recommendations.append({
            "practice": "Soil Testing",
            "action": "Conduct regular soil testing to optimize inputs and reduce waste",
            "sustainability_impact": 1.8,
            "economic_impact": 1.5,
            "confidence": 0.9
        })
        
        recommendations.append({
            "practice": "Organic Matter",
            "action": "Increase soil organic matter through compost application and crop residue management",
            "sustainability_impact": 2.0,
            "economic_impact": 0.9,
            "confidence": 0.85
        })
        
        # Add more recommendations based on sustainability preference
        if sustainability_preference > 5:
            recommendations.append({
                "practice": "Biodiversity",
                "action": "Maintain field margins and hedgerows to promote biodiversity and natural pest control",
                "sustainability_impact": 2.2,
                "economic_impact": 0.5,
                "confidence": 0.8
            })
        
        if sustainability_preference > 8:
            recommendations.append({
                "practice": "Renewable Energy",
                "action": "Consider installing solar panels or wind turbines to power farm operations",
                "sustainability_impact": 2.5,
                "economic_impact": -0.5,  # Initial investment may be high
                "confidence": 0.75
            })
        
        return recommendations
        
    def receive_message(self, sender_agent, message):
        """
        Receive and process a message from another agent or the web interface.
        
        Args:
            sender_agent: The agent or user that sent the message
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
            # Check if it's a farming advice request
            if message.get("request_type") == "farming_advice":
                user_message = message.get("message", "")
                
                # Extract crop mentions from the message
                crops = self.extract_crops_from_message(user_message)
                
                # Generate general farming advice
                response = {
                    "status": "success",
                    "response": self.generate_general_advice(user_message, crops)
                }
                
                return response
                
            # Return a default response if request type not recognized
            return {
                "status": "success",
                "response": "Hello! I'm your Farmer Advisor. I can help with sustainable farming practices, crop selection, and resource optimization. What would you like to know about?"
            }
                
        # Handle requests from other agents
        elif sender_agent.name == "Market Researcher":
            # Handle market information
            return {"status": "received", "message": "Thank you for the market information."}
            
        elif sender_agent.name == "Weather Station":
            # Handle weather information
            return {"status": "received", "message": "Thank you for the weather data."}
            
        # Default response for unrecognized senders
        return {"status": "received", "message": "Message received by Farmer Advisor"}
        
    def extract_crops_from_message(self, message):
        """Extract crop mentions from a user message."""
        # List of common crops to check for
        common_crops = ["wheat", "corn", "rice", "soybean", "barley", "oats", 
                        "cotton", "potato", "tomato", "lettuce", "carrot", "onion"]
        
        # Check for each crop in the message
        found_crops = []
        for crop in common_crops:
            if crop.lower() in message.lower():
                found_crops.append(crop)
                
        return found_crops
        
    def generate_general_advice(self, message, crops):
        """Generate general farming advice based on the user message and any mentioned crops."""
        # Default advice if no specific context is provided
        if not crops:
            return ("Here are some general sustainable farming tips:\n\n"
                   "• Implement crop rotation to improve soil health and reduce pest pressure\n"
                   "• Consider cover cropping during off-seasons to prevent erosion\n"
                   "• Use soil testing to optimize fertilizer application\n"
                   "• Employ integrated pest management to reduce chemical usage\n"
                   "• Maximize water efficiency with drip irrigation or other conservation methods\n\n"
                   "For more specific advice, please mention which crops you're growing or interested in.")
        
        # If crops were mentioned, provide more targeted advice
        crop_advice = f"Here's some advice for growing {', '.join(crops)}:\n\n"
        
        for crop in crops:
            if crop.lower() == "wheat":
                crop_advice += ("Wheat:\n"
                               "• Best planted in well-drained soils with pH 6.0-7.0\n"
                               "• Consider reduced tillage to maintain soil structure\n"
                               "• Monitor for rust and fusarium head blight\n\n")
            elif crop.lower() == "corn":
                crop_advice += ("Corn:\n"
                               "• Requires nutrient-rich soil and consistent moisture\n"
                               "• Plant when soil temperatures reach 50-55°F\n"
                               "• Consider precision application of nitrogen fertilizer\n\n")
            elif crop.lower() == "rice":
                crop_advice += ("Rice:\n"
                               "• Requires consistent water management\n"
                               "• Consider alternate wetting and drying techniques to reduce water usage\n"
                               "• Monitor for blast disease and stem borers\n\n")
            elif crop.lower() == "soybean":
                crop_advice += ("Soybean:\n"
                               "• Fixes nitrogen, making it excellent in crop rotations\n"
                               "• Plant in well-drained soils with pH 6.0-6.8\n"
                               "• Consider narrow row spacing for weed suppression\n\n")
            else:
                crop_advice += (f"{crop.capitalize()}:\n"
                               "• Ensure proper soil preparation and appropriate planting dates\n"
                               "• Monitor for pests and diseases regularly\n"
                               "• Follow recommended fertilizer application rates\n\n")
        
        return crop_advice 