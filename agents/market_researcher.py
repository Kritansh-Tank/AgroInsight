import pandas as pd
import numpy as np
from agents.base_agent import BaseAgent

class MarketResearcher(BaseAgent):
    """
    Market Researcher agent that analyzes regional market trends, crop pricing,
    and demand forecasts to suggest the most profitable crops to plant.
    """
    
    def __init__(self, db_connection):
        """Initialize the Market Researcher agent."""
        super().__init__("Market Researcher", db_connection)
        self.market_data = None
        self.load_market_data()
    
    def load_market_data(self):
        """Load market data from the database."""
        self.market_data = self.db.get_market_data()
        self.log_action(
            action_type="data_loading",
            action_details=f"Loaded market data: {len(self.market_data) if self.market_data else 0} records"
        )
        
        if self.market_data:
            # Convert to DataFrame for easier analysis
            self.market_df = pd.DataFrame(self.market_data)
            self.update_state("market_data_loaded", True)
        else:
            self.update_state("market_data_loaded", False)
    
    def process_input(self, input_data):
        """
        Process input data related to market queries.
        
        Args:
            input_data (dict): Data containing market query parameters
                - product: Specific crop to analyze (optional)
                - region: Region for market analysis (optional)
                - time_horizon: Short-term or long-term forecast
                - price_threshold: Minimum price threshold for recommendations
        
        Returns:
            dict: Processed market data and analysis
        """
        self.log_action("input_processing", f"Processing market query: {str(input_data)[:100]}...")
        
        # Store the input in state
        self.update_state("market_query", input_data)
        
        # Process specific product query if provided
        product = input_data.get("product")
        time_horizon = input_data.get("time_horizon", "short-term")
        
        if product:
            # Filter for specific product
            product_data = [item for item in self.market_data if item["product"].lower() == product.lower()]
            
            if not product_data:
                return {"status": "error", "message": f"No market data found for {product}"}
            
            # Analyze product market data
            analysis = self.analyze_product_market(product_data, time_horizon)
            return {
                "status": "success",
                "product": product,
                "market_analysis": analysis
            }
        else:
            # General market overview
            overview = self.generate_market_overview(time_horizon)
            return {
                "status": "success",
                "market_overview": overview
            }
    
    def analyze_product_market(self, product_data, time_horizon="short-term"):
        """
        Analyze market data for a specific product.
        
        Args:
            product_data (list): Market data for the specific product
            time_horizon (str): "short-term" or "long-term"
            
        Returns:
            dict: Product market analysis
        """
        # Convert to DataFrame
        product_df = pd.DataFrame(product_data)
        
        # Calculate statistics
        avg_price = product_df["market_price_per_ton"].mean()
        avg_demand = product_df["demand_index"].mean()
        avg_supply = product_df["supply_index"].mean()
        
        # Prepare analysis
        analysis = {
            "product": product_df.iloc[0]["product"],
            "avg_market_price": avg_price,
            "avg_demand_index": avg_demand,
            "avg_supply_index": avg_supply,
            "market_status": self.determine_market_status(avg_demand, avg_supply)
        }
        
        # Add seasonal insights
        seasonal_analysis = self.analyze_seasonal_factors(product_df)
        analysis["seasonal_analysis"] = seasonal_analysis
        
        # Add demand trends
        analysis["demand_trend"] = self.analyze_demand_trend(product_df)
        
        # Add price forecast based on time horizon
        analysis["price_forecast"] = self.forecast_price(product_df, time_horizon)
        
        # Add recommendations
        analysis["market_recommendations"] = self.generate_market_recommendations(analysis)
        
        return analysis
    
    def determine_market_status(self, demand, supply):
        """
        Determine the current market status based on demand and supply.
        
        Args:
            demand (float): Demand index
            supply (float): Supply index
            
        Returns:
            str: Market status
        """
        ratio = demand / supply if supply > 0 else float('inf')
        
        if ratio > 1.2:
            return "undersupplied"
        elif ratio < 0.8:
            return "oversupplied"
        else:
            return "balanced"
    
    def analyze_seasonal_factors(self, market_df):
        """
        Analyze seasonal factors affecting market conditions.
        
        Args:
            market_df (DataFrame): Market data
            
        Returns:
            dict: Seasonal analysis
        """
        # Group by seasonal factor
        seasonal_groups = market_df.groupby("seasonal_factor")
        
        seasonal_data = {}
        for season, group in seasonal_groups:
            seasonal_data[season] = {
                "avg_price": group["market_price_per_ton"].mean(),
                "avg_demand": group["demand_index"].mean(),
                "avg_supply": group["supply_index"].mean(),
                "count": len(group)
            }
        
        # Identify highest price season
        highest_price_season = max(seasonal_data.items(), key=lambda x: x[1]["avg_price"])[0]
        
        # Identify highest demand season
        highest_demand_season = max(seasonal_data.items(), key=lambda x: x[1]["avg_demand"])[0]
        
        return {
            "seasonal_data": seasonal_data,
            "highest_price_season": highest_price_season,
            "highest_demand_season": highest_demand_season,
            "recommendations": self.generate_seasonal_recommendations(seasonal_data)
        }
    
    def analyze_demand_trend(self, market_df):
        """
        Analyze demand trends based on consumer trend index.
        
        Args:
            market_df (DataFrame): Market data
            
        Returns:
            dict: Demand trend analysis
        """
        avg_consumer_trend = market_df["consumer_trend_index"].mean()
        
        if avg_consumer_trend > 120:
            trend_status = "strongly_increasing"
            trend_message = "Consumer demand is growing rapidly, indicating a strong market outlook."
        elif avg_consumer_trend > 100:
            trend_status = "increasing"
            trend_message = "Consumer demand is growing steadily, suggesting a positive market outlook."
        elif avg_consumer_trend > 90:
            trend_status = "stable"
            trend_message = "Consumer demand is stable, suggesting a consistent market."
        elif avg_consumer_trend > 70:
            trend_status = "decreasing"
            trend_message = "Consumer demand is declining, suggesting caution in market planning."
        else:
            trend_status = "strongly_decreasing"
            trend_message = "Consumer demand is falling rapidly, suggesting significant market challenges."
        
        return {
            "consumer_trend_index": avg_consumer_trend,
            "trend_status": trend_status,
            "trend_message": trend_message
        }
    
    def forecast_price(self, market_df, time_horizon):
        """
        Forecast prices based on market data and time horizon.
        
        Args:
            market_df (DataFrame): Market data
            time_horizon (str): "short-term" or "long-term"
            
        Returns:
            dict: Price forecast
        """
        current_price = market_df["market_price_per_ton"].mean()
        demand_index = market_df["demand_index"].mean()
        supply_index = market_df["supply_index"].mean()
        competitor_price = market_df["competitor_price_per_ton"].mean()
        consumer_trend = market_df["consumer_trend_index"].mean()
        
        # Simple forecast model - in a real system this would be more sophisticated
        if time_horizon == "short-term":
            # For short-term, weigh current conditions more heavily
            demand_factor = 0.6 * (demand_index / 125 - 1) + 1  # Normalize around 125
            supply_factor = 0.4 * (1 - supply_index / 125) + 1  # Inverse relationship
            competitor_factor = 0.3 * (competitor_price / current_price - 1) + 1
            trend_factor = 0.2 * (consumer_trend / 100 - 1) + 1
            
            # Combine factors
            forecast_factor = (demand_factor + supply_factor + competitor_factor + trend_factor) / 4
            
            # Apply to current price
            forecast_price = current_price * forecast_factor
            
            # Calculate confidence (simplified)
            forecast_confidence = 0.8  # Higher confidence for short-term
        else:
            # For long-term, weigh trends more heavily
            demand_factor = 0.3 * (demand_index / 125 - 1) + 1
            supply_factor = 0.2 * (1 - supply_index / 125) + 1
            competitor_factor = 0.2 * (competitor_price / current_price - 1) + 1
            trend_factor = 0.5 * (consumer_trend / 100 - 1) + 1
            
            # Combine factors
            forecast_factor = (demand_factor + supply_factor + competitor_factor + trend_factor) / 4
            
            # Apply to current price with longer trend
            forecast_price = current_price * (forecast_factor ** 1.5)  # Stronger effect
            
            # Calculate confidence (simplified)
            forecast_confidence = 0.6  # Lower confidence for long-term
        
        # Format the results
        if forecast_price > current_price * 1.1:
            trend = "increasing"
            message = "Prices are expected to increase significantly."
        elif forecast_price > current_price * 1.02:
            trend = "slightly_increasing"
            message = "Prices are expected to increase slightly."
        elif forecast_price < current_price * 0.9:
            trend = "decreasing"
            message = "Prices are expected to decrease significantly."
        elif forecast_price < current_price * 0.98:
            trend = "slightly_decreasing"
            message = "Prices are expected to decrease slightly."
        else:
            trend = "stable"
            message = "Prices are expected to remain stable."
        
        return {
            "current_price": current_price,
            "forecast_price": forecast_price,
            "price_change_percent": ((forecast_price / current_price) - 1) * 100,
            "forecast_confidence": forecast_confidence,
            "price_trend": trend,
            "forecast_message": message,
            "time_horizon": time_horizon
        }
    
    def generate_market_recommendations(self, analysis):
        """
        Generate market recommendations based on the analysis.
        
        Args:
            analysis (dict): Product market analysis
            
        Returns:
            list: Market recommendations
        """
        product = analysis["product"]
        market_status = analysis["market_status"]
        price_forecast = analysis["price_forecast"]
        demand_trend = analysis["demand_trend"]
        
        recommendations = []
        
        # Recommendation based on market status
        if market_status == "undersupplied":
            recommendations.append({
                "focus": "Production Increase",
                "action": f"Consider increasing {product} production to capitalize on high demand",
                "economic_impact": 2.0,
                "confidence": 0.85
            })
        elif market_status == "oversupplied":
            recommendations.append({
                "focus": "Diversification",
                "action": f"Consider reducing {product} production or finding alternative markets",
                "economic_impact": 1.2,
                "confidence": 0.8
            })
        
        # Recommendation based on price forecast
        if price_forecast["price_trend"] in ["increasing", "slightly_increasing"]:
            recommendations.append({
                "focus": "Investment",
                "action": f"Consider investing in {product} production capacity for {price_forecast['time_horizon']} gains",
                "economic_impact": 1.8,
                "confidence": price_forecast["forecast_confidence"]
            })
        elif price_forecast["price_trend"] in ["decreasing", "slightly_decreasing"]:
            recommendations.append({
                "focus": "Cost Reduction",
                "action": f"Focus on reducing production costs for {product} to maintain profitability as prices decline",
                "economic_impact": 1.5,
                "confidence": price_forecast["forecast_confidence"]
            })
        
        # Recommendation based on consumer trends
        if demand_trend["trend_status"] in ["strongly_increasing", "increasing"]:
            recommendations.append({
                "focus": "Market Expansion",
                "action": f"Explore new market channels for {product} to capitalize on growing consumer interest",
                "economic_impact": 1.7,
                "confidence": 0.75
            })
        elif demand_trend["trend_status"] in ["decreasing", "strongly_decreasing"]:
            recommendations.append({
                "focus": "Crop Switching",
                "action": f"Consider gradually transitioning from {product} to crops with better demand trends",
                "economic_impact": 1.6,
                "confidence": 0.7
            })
        
        # Recommendation on timing based on seasonality
        if "seasonal_analysis" in analysis and "highest_price_season" in analysis["seasonal_analysis"]:
            best_season = analysis["seasonal_analysis"]["highest_price_season"]
            recommendations.append({
                "focus": "Timing Optimization",
                "action": f"Time your {product} harvest to coincide with {best_season} season for optimal pricing",
                "economic_impact": 1.4,
                "confidence": 0.8
            })
        
        return recommendations
    
    def generate_seasonal_recommendations(self, seasonal_data):
        """
        Generate recommendations based on seasonal analysis.
        
        Args:
            seasonal_data (dict): Seasonal market data
            
        Returns:
            list: Seasonal recommendations
        """
        recommendations = []
        
        # Find the highest price season
        highest_price_season = max(seasonal_data.items(), key=lambda x: x[1]["avg_price"])[0]
        
        # Find the highest demand season
        highest_demand_season = max(seasonal_data.items(), key=lambda x: x[1]["avg_demand"])[0]
        
        recommendations.append({
            "focus": "Seasonal Timing",
            "action": f"Target {highest_price_season} season for selling when prices are typically highest",
            "economic_impact": 1.6,
            "confidence": 0.8
        })
        
        if highest_demand_season != highest_price_season:
            recommendations.append({
                "focus": "Production Planning",
                "action": f"Plan production cycles to have maximum harvest ready for {highest_demand_season} season when demand peaks",
                "economic_impact": 1.4,
                "confidence": 0.75
            })
        
        return recommendations
    
    def generate_market_overview(self, time_horizon="short-term"):
        """
        Generate a general overview of the market across all crops.
        
        Args:
            time_horizon (str): "short-term" or "long-term"
            
        Returns:
            dict: Market overview
        """
        # Convert market data to DataFrame
        market_df = pd.DataFrame(self.market_data)
        
        # Group by product
        product_groups = market_df.groupby("product")
        
        # Analyze each product
        product_analysis = {}
        for product, group in product_groups:
            product_analysis[product] = {
                "avg_price": group["market_price_per_ton"].mean(),
                "avg_demand": group["demand_index"].mean(),
                "avg_supply": group["supply_index"].mean(),
                "avg_consumer_trend": group["consumer_trend_index"].mean(),
                "market_status": self.determine_market_status(
                    group["demand_index"].mean(), 
                    group["supply_index"].mean()
                )
            }
        
        # Sort products by profitability potential
        profit_potential = {}
        for product, data in product_analysis.items():
            # Simple profit potential calculation
            supply_demand_ratio = data["avg_demand"] / data["avg_supply"] if data["avg_supply"] > 0 else float('inf')
            growth_factor = data["avg_consumer_trend"] / 100
            
            # Combine factors
            potential = data["avg_price"] * supply_demand_ratio * growth_factor
            profit_potential[product] = potential
        
        # Sort by potential
        sorted_products = sorted(profit_potential.items(), key=lambda x: x[1], reverse=True)
        
        # Generate top recommendations
        top_recommendations = []
        for product, potential in sorted_products[:3]:
            product_data = product_analysis[product]
            
            if product_data["market_status"] == "undersupplied":
                status_msg = "demand exceeds supply"
            elif product_data["market_status"] == "oversupplied":
                status_msg = "supply exceeds demand"
            else:
                status_msg = "market is balanced"
            
            if product_data["avg_consumer_trend"] > 110:
                trend_msg = "strongly growing consumer interest"
            elif product_data["avg_consumer_trend"] > 100:
                trend_msg = "growing consumer interest"
            elif product_data["avg_consumer_trend"] > 90:
                trend_msg = "stable consumer interest"
            else:
                trend_msg = "declining consumer interest"
            
            top_recommendations.append({
                "product": product,
                "profit_potential": potential,
                "avg_price": product_data["avg_price"],
                "market_status": product_data["market_status"],
                "consumer_trend": product_data["avg_consumer_trend"],
                "recommendation": f"{product} shows high profit potential with {status_msg} and {trend_msg}",
                "confidence": 0.8 if time_horizon == "short-term" else 0.6
            })
        
        return {
            "time_horizon": time_horizon,
            "top_profit_potential_crops": top_recommendations,
            "full_market_analysis": product_analysis
        }
    
    def generate_recommendations(self, context):
        """
        Generate detailed market recommendations based on context.
        
        Args:
            context (dict): Context data containing query parameters
                - farm_id: Farm ID (optional)
                - crop_type: Current crop type (optional)
                - region: Region (optional)
                - time_horizon: Short-term or long-term forecast
                
        Returns:
            list: Detailed market recommendations
        """
        self.log_action("recommendation_generation", f"Generating market recommendations for: {str(context)[:100]}...")
        
        farm_id = context.get("farm_id")
        crop_type = context.get("crop_type")
        time_horizon = context.get("time_horizon", "short-term")
        
        # If farm_id is provided, get farm data
        farm_data = None
        if farm_id:
            farm_data = self.db.get_farm_data(farm_id)
            if farm_data:
                crop_type = farm_data["crop_type"]
        
        # Generate recommendations
        recommendations = []
        
        # 1. Top market opportunities
        market_overview = self.generate_market_overview(time_horizon)
        recommendations.append({
            "category": "Market Opportunities",
            "recommendations": [
                {
                    "focus": f"High Potential: {rec['product']}",
                    "action": rec["recommendation"],
                    "economic_impact": rec["profit_potential"] / 100,  # Scale to a reasonable range
                    "confidence": rec["confidence"]
                }
                for rec in market_overview["top_profit_potential_crops"]
            ],
            "explanation": f"Top {time_horizon} market opportunities across all crops"
        })
        
        # 2. Current crop analysis if applicable
        if crop_type:
            product_data = [item for item in self.market_data if item["product"].lower() == crop_type.lower()]
            if product_data:
                crop_analysis = self.analyze_product_market(product_data, time_horizon)
                
                recommendations.append({
                    "category": f"Current Crop Analysis ({crop_type})",
                    "recommendations": crop_analysis["market_recommendations"],
                    "explanation": f"Analysis of your current crop ({crop_type}) market conditions"
                })
        
        # 3. Diversification strategies
        diversification_recs = self.recommend_diversification(market_overview, crop_type)
        if diversification_recs:
            recommendations.append({
                "category": "Diversification Strategy",
                "recommendations": diversification_recs,
                "explanation": "Recommendations for crop diversification to optimize profits and reduce risk"
            })
        
        # 4. Seasonal strategy
        seasonal_recs = self.recommend_seasonal_strategy(time_horizon)
        if seasonal_recs:
            recommendations.append({
                "category": "Seasonal Strategy",
                "recommendations": seasonal_recs,
                "explanation": "Recommendations for optimizing planting and harvesting timing"
            })
        
        # Store recommendations in database if farm_id is available
        if farm_id:
            for category in recommendations:
                for rec in category["recommendations"]:
                    self.db.add_recommendation(
                        farm_id=farm_id,
                        rec_type=category["category"],
                        rec_text=rec["action"],
                        sustainability_impact=0,  # Market researcher focuses on economic impact
                        economic_impact=rec.get("economic_impact", 0),
                        confidence_score=rec.get("confidence", 0)
                    )
        
        return recommendations
    
    def recommend_diversification(self, market_overview, current_crop=None):
        """
        Recommend diversification strategies based on market analysis.
        
        Args:
            market_overview (dict): Market overview data
            current_crop (str): Current crop being grown
            
        Returns:
            list: Diversification recommendations
        """
        recommendations = []
        
        # Get top crops sorted by profit potential
        top_crops = market_overview["top_profit_potential_crops"]
        
        # Filter out current crop
        if current_crop:
            diversification_options = [
                crop for crop in top_crops 
                if crop["product"].lower() != current_crop.lower()
            ]
        else:
            diversification_options = top_crops
        
        # Recommend complementary crops for diversification
        if diversification_options:
            for i, crop in enumerate(diversification_options[:2]):  # Top 2 alternatives
                recommendations.append({
                    "focus": f"Diversification: {crop['product']}",
                    "action": f"Consider allocating a portion of your land to {crop['product']} as a diversification strategy",
                    "economic_impact": crop["profit_potential"] / 100,  # Scale to a reasonable range
                    "confidence": crop["confidence"]
                })
        
        # Add general diversification recommendation
        recommendations.append({
            "focus": "Risk Management",
            "action": "Implement a multi-crop strategy to reduce market volatility risks",
            "economic_impact": 1.4,
            "confidence": 0.85
        })
        
        return recommendations
    
    def recommend_seasonal_strategy(self, time_horizon):
        """
        Recommend seasonal strategies based on market data.
        
        Args:
            time_horizon (str): Short-term or long-term forecast
            
        Returns:
            list: Seasonal strategy recommendations
        """
        # Convert market data to DataFrame
        market_df = pd.DataFrame(self.market_data)
        
        # Group by seasonal factor and product
        seasonal_product_groups = market_df.groupby(["seasonal_factor", "product"])
        
        # Calculate average prices by season and product
        seasonal_prices = {}
        for (season, product), group in seasonal_product_groups:
            if season not in seasonal_prices:
                seasonal_prices[season] = {}
            
            seasonal_prices[season][product] = {
                "avg_price": group["market_price_per_ton"].mean(),
                "avg_demand": group["demand_index"].mean()
            }
        
        # Find best season for each product
        best_seasons = {}
        for product in market_df["product"].unique():
            max_price = 0
            best_season = None
            
            for season in seasonal_prices:
                if product in seasonal_prices[season]:
                    price = seasonal_prices[season][product]["avg_price"]
                    if price > max_price:
                        max_price = price
                        best_season = season
            
            if best_season:
                best_seasons[product] = best_season
        
        # Generate recommendations
        recommendations = []
        
        # Recommend crop selection based on upcoming seasons
        # Note: In a real system, we would need to know the current season
        for product, best_season in best_seasons.items():
            recommendations.append({
                "focus": f"Seasonal Timing: {product}",
                "action": f"For {product}, plan harvest to coincide with {best_season} season for optimal pricing",
                "economic_impact": 1.5,
                "confidence": 0.8 if time_horizon == "short-term" else 0.6
            })
            
            # Just provide top 3 recommendations to avoid overwhelming
            if len(recommendations) >= 3:
                break
        
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
            # Extract the user message
            user_message = message.get("message", "")
            if "crop_market_analysis" in message:
                crop_type = message.get("crop_type", "corn")
            else:
                # Try to extract crop type from the message
                crop_type = self.extract_crop_from_message(user_message) 
            
            # If we have a crop type, analyze it
            if crop_type:
                product_data = [item for item in self.market_data if item["product"].lower() == crop_type.lower()]
                
                # If we found data for this crop
                if product_data:
                    crop_analysis = self.analyze_product_market(
                        product_data, 
                        message.get("time_horizon", "short-term")
                    )
                    
                    # Format the response for display
                    price_trend = crop_analysis.get("price_forecast", {}).get("price_trend", "stable")
                    price_message = crop_analysis.get("price_forecast", {}).get("forecast_message", "")
                    analysis_summary = crop_analysis.get("analysis_summary", "")
                    
                    response_text = f"Market Analysis for {crop_type.capitalize()}:\n\n"
                    response_text += f"Price Trend: {price_trend.replace('_', ' ').capitalize()}\n"
                    response_text += f"Forecast: {price_message}\n\n"
                    response_text += f"Analysis: {analysis_summary}\n\n"
                    
                    # Add recommendations
                    if "market_recommendations" in crop_analysis:
                        response_text += "Recommendations:\n"
                        for rec in crop_analysis["market_recommendations"]:
                            response_text += f"• {rec.get('action', '')}\n"
                    
                    return {
                        "status": "success",
                        "response": response_text,
                        "crop_type": crop_type,
                        "market_analysis": crop_analysis
                    }
                else:
                    # Generate general market overview
                    overview = self.generate_market_overview("short-term")
                    
                    # Try to find closest crop match
                    similar_crops = self.find_similar_crops(crop_type)
                    
                    response_text = f"I don't have specific market data for {crop_type}.\n\n"
                    
                    if similar_crops:
                        response_text += f"Did you mean one of these crops: {', '.join(similar_crops)}?\n\n"
                    
                    response_text += "Here's a general market overview:\n\n"
                    
                    # Add top crops from the overview
                    if "top_profit_potential_crops" in overview:
                        response_text += "Top crops by profit potential:\n"
                        for crop in overview["top_profit_potential_crops"]:
                            response_text += f"• {crop.get('product', '')}: {crop.get('recommendation', '')}\n"
                    
                    return {
                        "status": "success",
                        "response": response_text,
                        "market_overview": overview
                    }
            else:
                # No specific crop mentioned, provide general market overview
                overview = self.generate_market_overview("short-term")
                
                response_text = "General Market Overview:\n\n"
                
                # Add top crops from the overview
                if "top_profit_potential_crops" in overview:
                    response_text += "Top crops by profit potential:\n"
                    for crop in overview["top_profit_potential_crops"]:
                        response_text += f"• {crop.get('product', '')}: {crop.get('recommendation', '')}\n"
                
                return {
                    "status": "success",
                    "response": response_text,
                    "market_overview": overview
                }
        
        elif sender_agent.name == "Farmer Advisor":
            # Handle specific request types from Farmer Advisor
            if message.get("request_type") == "crop_market_analysis":
                crop_type = message.get("crop_type")
                
                if crop_type:
                    product_data = [item for item in self.market_data if item["product"].lower() == crop_type.lower()]
                    
                    if product_data:
                        crop_analysis = self.analyze_product_market(
                            product_data, 
                            message.get("time_horizon", "short-term")
                        )
                        
                        return {
                            "status": "success",
                            "crop_type": crop_type,
                            "market_analysis": crop_analysis
                        }
                    else:
                        return {"status": "error", "message": f"No market data found for {crop_type}"}
                else:
                    return {"status": "error", "message": "No crop type specified in the request"}
            
            elif message.get("request_type") == "recommend_crops":
                farm_id = message.get("farm_id")
                sustainability_preference = message.get("sustainability_preference", 5)
                
                # Generate market-based crop recommendations
                market_overview = self.generate_market_overview(message.get("time_horizon", "short-term"))
                
                # Filter recommendations based on sustainability preference
                if sustainability_preference > 7:
                    # For high sustainability preference, prioritize stable crops
                    filtered_recommendations = [
                        crop for crop in market_overview["top_profit_potential_crops"]
                        if self.is_sustainable_market(crop)
                    ]
                else:
                    # Otherwise, use all recommendations
                    filtered_recommendations = market_overview["top_profit_potential_crops"]
                
                return {
                    "status": "success",
                    "crop_recommendations": filtered_recommendations[:3]  # Top 3 recommendations
                }
            
            else:
                # Default response for unknown request types
                return {"status": "error", "message": "Unknown request type from Farmer Advisor"}
        
        # Default implementation for other agents
        return {"status": "received", "message": "Message received by Market Researcher"}
        
    def extract_crop_from_message(self, message):
        """
        Extract crop mentions from a user message.
        
        Args:
            message (str): User message
            
        Returns:
            str: Extracted crop name or None
        """
        # List of common crops to check for
        common_crops = ["wheat", "corn", "rice", "soybean", "barley", "oats", 
                        "cotton", "potato", "tomato", "lettuce", "carrot", "onion"]
        
        # Check for each crop in the message
        message_lower = message.lower()
        for crop in common_crops:
            if crop.lower() in message_lower:
                return crop
                
        # Check for phrases like "market for X" or "price of X"
        import re
        patterns = [
            r"market for (\w+)",
            r"price[s]? of (\w+)",
            r"(\w+) prices?",
            r"(\w+) market"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                potential_crop = match.group(1)
                # Verify this is a known crop
                if potential_crop in common_crops:
                    return potential_crop
        
        # No crop found
        return None
        
    def find_similar_crops(self, crop_name):
        """
        Find similar crop names from the available data.
        
        Args:
            crop_name (str): The crop name to match
            
        Returns:
            list: List of similar crop names
        """
        # Get all unique products from market data
        available_crops = list(set(item["product"] for item in self.market_data))
        
        # Simple string similarity - find crops that start with similar letters
        similarities = []
        crop_lower = crop_name.lower()
        
        for available_crop in available_crops:
            available_lower = available_crop.lower()
            # Simple prefix matching
            if available_lower.startswith(crop_lower[:2]) or crop_lower.startswith(available_lower[:2]):
                similarities.append(available_crop)
        
        return similarities[:3]  # Return top 3 similar crops
    
    def is_sustainable_market(self, crop_data):
        """
        Determine if a crop's market conditions are suitable for sustainable farming.
        
        Args:
            crop_data (dict): Crop market data
            
        Returns:
            bool: Whether market conditions support sustainable farming
        """
        # Define criteria for sustainable market conditions
        # Example: Stable or growing markets are better for sustainable practices
        # as they allow long-term investment in sustainable methods
        
        if crop_data.get("market_status") == "balanced":
            return True
        
        if crop_data.get("consumer_trend", 0) > 95:  # Stable or growing interest
            return True
        
        return False 