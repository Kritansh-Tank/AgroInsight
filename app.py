import os
import json
import sys
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import time
import datetime
import markdown
import jinja2
from markupsafe import Markup

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the SustainableFarmingSystem
from models.multi_agent_system import SustainableFarmingSystem

# Define a fake agent class to use for web interface communication
class FakeAgent:
    """A simple class to represent the web user when communicating with agents."""
    def __init__(self, name="Web User"):
        self.name = name

app = Flask(__name__)
app.secret_key = 'agroinsight-ai-secret-key'  # For flash messages

# Create a markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text, extensions=['nl2br', 'fenced_code'])

# Create a nl2br filter
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text is None:
        return ""
    text = str(text)
    return Markup(text.replace('\n', '<br>'))

# Add min filter for Jinja2 templates
@app.template_filter('min_value')
def min_value_filter(value, ceiling):
    return min(value, ceiling)

# Helper function to add a prefix to flash messages to make them context-specific
def flash_with_context(message, category, context_prefix):
    flash(f"{context_prefix}: {message}", category)

# Global instance of SustainableFarmingSystem
system = None

def initialize_system(reset_db=True):
    """Initialize the system and optionally reset the database"""
    global system
    try:
        # Initialize the actual SustainableFarmingSystem instead of using mock data
        system = SustainableFarmingSystem()
        
        if reset_db:
            print("Resetting database...")
            system.reset_database()
            print("Database reset complete.")
            
        return True
    except Exception as e:
        logging.error(f"Error initializing system: {str(e)}")
        return False

@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html')

@app.route('/market_data', methods=['GET', 'POST'])
def market_data():
    """Handle market data queries"""
    result = None
    product = None
    time_period = 'recent'
    region = 'local'
    market_data = None
    
    # Get unique products from database for dropdown
    products = []
    try:
        all_market_data = system.db.get_market_data()
        if all_market_data:
            products = sorted(list(set(item["product"] for item in all_market_data)))
    except Exception as e:
        logging.error(f"Error fetching products for dropdown: {str(e)}")
    
    if request.method == 'POST':
        product = request.form.get('product', '')
        time_period = request.form.get('time_period', 'recent')
        region = request.form.get('region', 'local')
        
        try:
            # Convert time_period to time_horizon for system API
            time_horizon = "long-term" if time_period in ["yearly", "seasonal"] else "short-term"
            
            # Handle the general_overview case by passing None as product
            product_param = None if product == "general_overview" else product
            
            # Use the actual system to query market data
            result = system.query_market_data(product=product_param, time_horizon=time_horizon)
            
            if result.get("status") == "success":
                if product and product != "general_overview":
                    # Format specific product data
                    market_analysis = result.get("market_analysis", {})
                    
                    # Create a detailed price trend message
                    price_trend = f"{product} Market Status: {market_analysis.get('market_status', 'Unknown')}\n"
                    price_trend += f"Average Price: ${market_analysis.get('avg_market_price', 0):.2f} per ton\n"
                    price_trend += f"Price Forecast: {market_analysis.get('price_forecast', {}).get('forecast_message', 'No forecast available')}"
                    
                    # Create insights from other available data
                    market_insights = market_analysis.get('analysis_summary', '')
                    if not market_insights and 'supply_demand_analysis' in market_analysis:
                        market_insights = market_analysis.get('supply_demand_analysis', '')
                    
                    # Format recommendations as a list of strings
                    recommendations = []
                    for i, rec in enumerate(market_analysis.get("market_recommendations", [])):
                        if isinstance(rec, dict):
                            # If it's already a dict with focus/action keys
                            rec_text = f"{i+1}. {rec.get('focus', '')}: {rec.get('action', '')}"
                            recommendations.append(rec_text)
                        else:
                            # Just use the string
                            recommendations.append(rec)
                    
                    market_data = {
                        "product": product,
                        "time_period": time_period,
                        "region": region,
                        "is_organic": "organic" in product.lower(),
                        "price_trend": price_trend,
                        "market_insights": market_insights,
                        "demand_forecast": market_analysis.get("demand_forecast", {}).get("forecast_message", ""),
                        "recommendations": recommendations
                    }
                else:
                    # Format general market overview
                    overview = result.get("market_overview", {})
                    
                    market_data = {
                        "product": "General Overview",
                        "time_period": time_period,
                        "region": region,
                        "is_organic": False,
                        "price_trend": overview.get("market_trend", ""),
                        "market_insights": overview.get("summary", ""),
                        "demand_forecast": overview.get("forecast", ""),
                        "recommendations": [
                            rec.get("recommendation", "") for rec in overview.get("top_profit_potential_crops", [])
                        ]
                    }
                
                flash_with_context("Market data analysis completed successfully.", "success", "Market Data")
            else:
                flash_with_context(f"Error in market data analysis: {result.get('message', 'Unknown error')}", "warning", "Market Data")
            
        except Exception as e:
            flash_with_context(f"Error processing market data: {str(e)}", "danger", "Market Data")
            logging.error(f"Market data error: {str(e)}")
    
    return render_template(
        'market_data.html', 
        market_data=market_data,
        product=product,
        time_period=time_period,
        region=region,
        products=products  # Pass products list to template
    )

@app.route('/weather_data', methods=['GET', 'POST'])
def weather_data():
    """Handle weather data queries"""
    weather_data = None
    location = None
    forecast_days = 7  # Default
    include_historical = 'no'  # Default
    
    # Define available regions for the dropdown
    regions = ["north", "central", "south"]
    
    if request.method == 'POST':
        location = request.form.get('location')
        forecast_days = int(request.form.get('forecast_days', 7))
        include_historical = request.form.get('include_historical', 'no')
        
        try:
            if location:
                # Map location to region for system API
                region = location.lower()
                # No need to standardize as we're using a dropdown now
                
                # Convert include_historical to boolean
                include_hist_bool = include_historical != 'no'
                
                # Use the actual system to query weather data
                result = system.query_weather_data(
                    region=region, 
                    forecast_days=forecast_days,
                    include_historical=include_hist_bool
                )
                
                if result.get("status") != "error":
                    # Format for template
                    weather_data = {
                        "location": location.title(), # Capitalize the region name for display
                        "current_weather": result.get("current_weather", {}),
                        "forecast": result.get("forecast", []),
                        "agricultural_impact": result.get("agricultural_impact", {}),
                        "historical_data": result.get("historical_data", []) if include_hist_bool else []
                    }
                    
                    flash_with_context("Weather data retrieved successfully.", "success", "Weather Data")
                else:
                    flash_with_context(f"Error retrieving weather data: {result.get('message', 'Unknown error')}", "warning", "Weather Data")
            else:
                flash_with_context("Please select a region.", "warning", "Weather Data")
                
        except Exception as e:
            flash_with_context(f"Error processing weather data: {str(e)}", "danger", "Weather Data")
            logging.error(f"Weather data error: {str(e)}")
    
    return render_template(
        'weather_data.html',
        weather_data=weather_data,
        location=location,
        forecast_days=forecast_days,
        include_historical=include_historical,
        regions=regions  # Pass regions list to template
    )

@app.route('/analyze_farm', methods=['GET', 'POST'])
def analyze_farm():
    """Analyze farm data based on soil and climate inputs"""
    soil_ph = None
    soil_moisture = None
    temperature = None
    rainfall = None
    region = None
    analysis_results = None
    
    if request.method == 'POST':
        try:
            # Extract form data
            soil_ph = float(request.form.get('soil_ph', 0))
            soil_moisture = float(request.form.get('soil_moisture', 0))
            temperature = float(request.form.get('temperature', 0))
            rainfall = float(request.form.get('rainfall', 0))
            region = request.form.get('region', 'central')
            
            # Validate inputs
            if not all([soil_ph, soil_moisture, temperature, rainfall, region]):
                flash_with_context("Please fill in all required fields.", "warning", "Farm Analysis")
                return render_template(
                    'analyze_farm.html',
                    soil_ph=soil_ph,
                    soil_moisture=soil_moisture,
                    temperature=temperature,
                    rainfall=rainfall,
                    region=region
                )
            
            # Call the system to analyze the farm data
            analysis = system.analyze_new_farm(
                soil_ph=soil_ph,
                soil_moisture=soil_moisture,
                temperature_c=temperature,
                rainfall_mm=rainfall,
                region=region
            )
            
            if analysis.get("status") == "success":
                # Format the response for the template - align with main.py structure
                analysis_results = {
                    "farm_parameters": {
                        "soil_ph": soil_ph,
                        "soil_moisture": soil_moisture,
                        "temperature": temperature,
                        "rainfall": rainfall,
                        "region": region
                    },
                    # Use the exact same keys and structure as in main.py's demo_analyze_new_farm
                    "soil_analysis": analysis.get("initial_analysis", {}).get("soil_analysis", {}),
                    "climate_analysis": analysis.get("initial_analysis", {}).get("climate_analysis", {}),
                    "recommended_crops": analysis.get("recommended_crops", []),
                    "weather_forecast": analysis.get("weather_forecast", []),
                    "agricultural_impact": analysis.get("agricultural_impact", {}),
                    "market_overview": analysis.get("market_overview", {})
                }
                
                # Add formatted data for use in the template
                if "soil_analysis" in analysis.get("initial_analysis", {}):
                    soil = analysis.get("initial_analysis", {}).get("soil_analysis", {})
                    analysis_results["ph_status"] = soil.get("ph_status", "Unknown")
                    analysis_results["moisture_status"] = soil.get("moisture_status", "Unknown")
                    analysis_results["soil_recommendations"] = soil.get("recommendations", [])
                
                if "climate_analysis" in analysis.get("initial_analysis", {}):
                    climate = analysis.get("initial_analysis", {}).get("climate_analysis", {})
                    analysis_results["temperature_category"] = climate.get("temperature_category", "Unknown")
                    analysis_results["rainfall_category"] = climate.get("rainfall_category", "Unknown")
                    analysis_results["suitable_crops"] = climate.get("suitable_crops", [])
                    analysis_results["climate_recommendations"] = climate.get("recommendations", [])
                
                flash_with_context("Farm analysis completed successfully!", "success", "Farm Analysis")
            else:
                flash_with_context(f"Error in farm analysis: {analysis.get('message', 'Unknown error')}", "danger", "Farm Analysis")
                
        except ValueError:
            flash_with_context("Please enter valid numeric values for all fields.", "danger", "Farm Analysis")
        except Exception as e:
            flash_with_context(f"Error processing farm analysis: {str(e)}", "danger", "Farm Analysis")
            logging.error(f"Farm analysis error: {str(e)}")
    
    return render_template(
        'analyze_farm.html',
        soil_ph=soil_ph,
        soil_moisture=soil_moisture,
        temperature=temperature,
        rainfall=rainfall,
        region=region,
        analysis_results=analysis_results
    )

@app.route('/farm_recommendations', methods=['GET', 'POST'])
def farm_recommendations():
    """Generate farm-specific recommendations"""
    farm_id = None
    region = None
    financial_goal = None
    sustainability_preference = None
    recommendations = None
    
    if request.method == 'POST':
        try:
            # Get form data
            farm_id = int(request.form.get('farm_id', 0))
            region = request.form.get('region', 'central')
            financial_goal = request.form.get('financial_goal', 'balance')
            sustainability_preference = int(request.form.get('sustainability_preference', 5))
            
            # Call the system to generate recommendations
            result = system.generate_farm_recommendations(
                farm_id=farm_id,
                region=region,
                financial_goal=financial_goal,
                sustainability_preference=sustainability_preference
            )
            
            if result.get("status") != "error":
                recommendations = result
                flash_with_context("Recommendations generated successfully.", "success", "Recommendations")
            else:
                flash_with_context(f"Error generating recommendations: {result.get('message', 'Unknown error')}", "danger", "Recommendations")
                
        except ValueError:
            flash_with_context("Please enter a valid farm ID.", "danger", "Recommendations")
        except Exception as e:
            flash_with_context(f"Error processing recommendations: {str(e)}", "danger", "Recommendations")
            logging.error(f"Recommendations error: {str(e)}")
    
    # Get list of farm IDs for the dropdown
    farm_data = system.db.get_farm_data() if hasattr(system, 'db') else []
    farm_choices = []
    
    if isinstance(farm_data, list):
        farm_choices = [(farm.get('farm_id', 0), f"Farm #{farm.get('farm_id', 0)} - {farm.get('crop_type', 'Unknown')}") 
                        for farm in farm_data if 'farm_id' in farm]
    elif isinstance(farm_data, dict) and 'farm_id' in farm_data:
        # Single farm returned
        farm_choices = [(farm_data.get('farm_id', 0), f"Farm #{farm_data.get('farm_id', 0)} - {farm_data.get('crop_type', 'Unknown')}")]
    
    return render_template(
        'farm_recommendations.html',
        farm_id=farm_id,
        region=region,
        financial_goal=financial_goal,
        sustainability_preference=sustainability_preference,
        recommendations=recommendations,
        farm_choices=farm_choices
    )

@app.route('/sustainability_comparison')
def sustainability_comparison():
    """Display sustainability comparison data across farms"""
    try:
        # Get comparison data from the system
        comparison_data = system.get_sustainability_comparison()
        
        if comparison_data.get("status") == "success":
            # Format the data for the template
            comparison = {
                "overall_stats": comparison_data.get("sustainability_stats", {}),
                "efficiency_stats": comparison_data.get("efficiency_stats", {}),
                "crop_comparison": comparison_data.get("sustainability_stats", {}).get("crop_comparison", []),
                "top_practices": comparison_data.get("top_practices", []),
                "regional_comparison": comparison_data.get("regional_comparison", []),
                "improvement_potential": comparison_data.get("improvement_potential", {})
            }
            
            flash_with_context("Sustainability comparison data loaded successfully.", "success", "Sustainability")
            return render_template('sustainability_comparison.html', comparison=comparison)
        else:
            flash_with_context(f"Error retrieving sustainability data: {comparison_data.get('message', 'Unknown error')}", "warning", "Sustainability")
            return render_template('sustainability_comparison.html')
    
    except Exception as e:
        flash_with_context(f"Error loading sustainability comparison: {str(e)}", "danger", "Sustainability")
        logging.error(f"Sustainability comparison error: {str(e)}")
        return render_template('sustainability_comparison.html')

@app.route('/agent_communication', methods=['GET', 'POST'])
def agent_communication():
    """Handle agent communication test"""
    if 'agent_conversation' not in session:
        session['agent_conversation'] = []
    
    selected_agent = request.args.get('agent', None)
    
    # Define the list of available agents
    agents_list = [
        {
            "id": "farmer_advisor",
            "name": "Farmer Advisor",
            "type": "advisor",
            "description": "Expert in sustainable farming practices and crop management"
        },
        {
            "id": "weather_station",
            "name": "Weather Station",
            "type": "weather",
            "description": "Regional weather data and agricultural impact analysis"
        },
        {
            "id": "market_researcher",
            "name": "Market Researcher",
            "type": "market",
            "description": "Market trends, pricing, and crop profitability analysis"
        }
    ]
    
    if request.method == 'POST':
        # Clear conversation if requested
        if request.form.get('clear_conversation'):
            session['agent_conversation'] = []
            flash_with_context("Conversation cleared.", "info", "Agent Communication")
            return redirect(url_for('agent_communication'))
        
        # Process a new message
        user_message = request.form.get('message')
        selected_agent = request.form.get('selected_agent')
        
        if not user_message:
            flash_with_context("Please enter a message.", "warning", "Agent Communication")
            return redirect(url_for('agent_communication'))
        
        try:
            # Add user message to conversation
            session['agent_conversation'].append({
                "sender": "User",
                "message": user_message,
                "timestamp": time.time()
            })
            
            # If we have a selected agent, send to that one
            if selected_agent and selected_agent in system.agents:
                # Create a fake agent to represent the web user
                web_user = FakeAgent("Web User")
                
                # Create the appropriate request based on agent type
                if selected_agent == "weather_station":
                    request_data = {
                        "request_type": "weather_forecast", 
                        "region": "central",  # Default to central region
                        "days": 7,
                        "message": user_message  # Pass the user message as well
                    }
                elif selected_agent == "market_researcher":
                    # Extract potential crop type from message but let the agent handle it
                    request_data = {
                        "message": user_message  # Just pass the message directly
                    }
                elif selected_agent == "farmer_advisor":
                    request_data = {
                        "request_type": "farming_advice",
                        "message": user_message
                    }
                else:
                    request_data = {"message": user_message}
                
                # Send the message to the selected agent using our fake agent
                response = system.agents[selected_agent].receive_message(web_user, request_data)
                
                # Add agent response to conversation
                agent_name = None
                for agent in agents_list:
                    if agent["id"] == selected_agent:
                        agent_name = agent["name"]
                        break
                        
                if not agent_name:
                    agent_name = selected_agent.replace('_', ' ').title()
                
                # Extract the response content based on the response structure
                if isinstance(response, dict):
                    # Try different possible response formats
                    if "response" in response:
                        response_content = response["response"]
                    elif "message" in response:
                        response_content = response["message"]
                    elif "forecast" in response:
                        # Format weather forecast data
                        forecast = response.get("forecast", [])
                        forecast_str = "Weather Forecast:\n"
                        for day in forecast:
                            forecast_str += f"• {day.get('date', 'Unknown')}: {day.get('condition', 'Unknown')}, " + \
                                            f"High: {day.get('temp_high_c', 'N/A')}°C, " + \
                                            f"Low: {day.get('temp_low_c', 'N/A')}°C\n"
                        response_content = forecast_str
                    elif "market_analysis" in response:
                        # Format market analysis data
                        market = response.get("market_analysis", {})
                        market_str = f"Market Analysis for {response.get('crop_type', 'crops')}:\n"
                        market_str += f"• Price Trend: {market.get('price_trend', 'Unknown')}\n"
                        market_str += f"• Analysis: {market.get('analysis_summary', 'No analysis available')}\n"
                        if "market_recommendations" in market:
                            market_str += "\nRecommendations:\n"
                            for rec in market.get("market_recommendations", []):
                                if isinstance(rec, dict) and "action" in rec:
                                    market_str += f"• {rec.get('action', '')}\n"
                                else:
                                    market_str += f"• {rec}\n"
                        response_content = market_str
                    else:
                        # Fall back to string representation for unknown formats
                        response_content = str(response)
                else:
                    response_content = str(response)
                
                session['agent_conversation'].append({
                    "sender": agent_name,
                    "message": response_content,
                    "timestamp": time.time()
                })
                
                # Save the conversation
                session.modified = True
                flash_with_context(f"{agent_name} responded to your message.", "success", "Agent Communication")
            else:
                flash_with_context("Please select an agent to communicate with.", "warning", "Agent Communication")
        except Exception as e:
            flash_with_context(f"Error processing agent communication: {str(e)}", "danger", "Agent Communication")
            logging.error(f"Agent communication error: {str(e)}")
    
    # Determining if we should show a selected agent in the chat header
    agent_name = "Select an Agent"
    if selected_agent:
        for agent in agents_list:
            if agent["id"] == selected_agent:
                agent_name = agent["name"]
                break
    
    return render_template(
        'agent_communication.html',
        conversation=session['agent_conversation'],
        agents=agents_list,
        selected_agent=selected_agent,
        agent_name=agent_name
    )

# Helper functions for agent communication
def extract_location(message):
    """Extract location from a message"""
    import re
    
    # Common location prepositions
    location_patterns = [
        r"in ([A-Za-z\s]+?)(?:\s|$|\.|\?|,)",
        r"for ([A-Za-z\s]+?)(?:\s|$|\.|\?|,)",
        r"at ([A-Za-z\s]+?)(?:\s|$|\.|\?|,)",
        r"near ([A-Za-z\s]+?)(?:\s|$|\.|\?|,)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message)
        if match:
            location = match.group(1).strip()
            # Filter out common non-location words
            non_locations = ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'forecast', 'weather', 'tomorrow', 'today']
            if location.lower() not in non_locations and len(location) > 2:
                return location
    
    return None

def extract_days(message):
    """Extract number of days from a message"""
    import re
    
    # Patterns for day/days mentions
    days_patterns = [
        r"(\d+)[\s-]*day(?:s)?",
        r"next (\d+) day(?:s)?",
        r"(\d+)[\s-]*day forecast"
    ]
    
    for pattern in days_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            try:
                days = int(match.group(1))
                return min(days, 10)  # Cap at 10 days
            except ValueError:
                pass
    
    return None

@app.route('/ollama_llm', methods=['GET', 'POST'])
def ollama_llm():
    """Test interactions with Ollama LLM integration"""
    prompt = ""  # Default to empty string instead of None
    response = None  # Changed from llm_response to response to match template
    llm_available = False
    
    # Check if LLM is available in the system
    if system and hasattr(system, 'use_llm') and system.use_llm and hasattr(system, 'llm'):
        llm_available = system.llm.is_available
    
    if request.method == 'POST':
        prompt = request.form.get('prompt', '').strip()
        
        if not prompt:
            flash_with_context("Please enter a prompt.", "warning", "Ollama LLM")
            return render_template('ollama_llm.html', llm_available=llm_available, prompt=prompt)
        
        if llm_available:
            try:
                # Use the system's LLM to generate a response
                result = system.llm.generate(prompt)
                
                if result.get("status") == "success":
                    response = result.get("generated_text", "No response generated.")
                    flash_with_context("LLM response generated successfully!", "success", "Ollama LLM")
                else:
                    response = f"Error: {result.get('message', 'Unknown error')}"
                    flash_with_context("Error in LLM response generation.", "danger", "Ollama LLM")
            
            except Exception as e:
                response = f"Error: {str(e)}"
                flash_with_context(f"Error processing LLM request: {str(e)}", "danger", "Ollama LLM")
                logging.error(f"Ollama LLM error: {str(e)}")
        else:
            response = "Ollama LLM integration is not available. Please make sure Ollama is running and the API is accessible."
            flash_with_context("Ollama LLM integration is not available.", "warning", "Ollama LLM")
    
    return render_template('ollama_llm.html', 
                          prompt=prompt, 
                          response=response,  # Changed from llm_response to response
                          llm_available=llm_available)

@app.route('/run_all_demos')
def run_all_demos():
    """Run all available demos to showcase system functionality"""
    try:
        if system:
            # Import the run_all_demos function from main.py
            from main import run_all_demos
            
            # Capture stdout to get the output
            import io
            import sys
            from contextlib import redirect_stdout
            
            # Redirect stdout to capture the output
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                # Call run_all_demos with the system instance
                run_all_demos(system, reset_db=False)
            
            # Get the captured output
            output = output_buffer.getvalue()
            
            # Format for HTML display (replace newlines with <br>)
            formatted_output = output.replace('\n', '<br>')
            
            return render_template('demo_results.html', 
                                  demo_output=formatted_output,
                                  title="All Demos")
        else:
            flash_with_context("System is not initialized properly.", "danger", "Demos")
            return redirect(url_for('index'))
    
    except Exception as e:
        flash_with_context(f"Error running demos: {str(e)}", "danger", "Demos")
        logging.error(f"Demo execution error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/api/reset_database', methods=['POST'])
def reset_database():
    """Reset the database to its initial state"""
    try:
        if system:
            system.reset_database()
            flash_with_context("Database reset successfully.", "success", "Database")
        else:
            flash_with_context("System is not initialized properly.", "danger", "Database")
        
        # Redirect to the referring page or home page
        referrer = request.referrer or url_for('index')
        return redirect(referrer)
    
    except Exception as e:
        flash_with_context(f"Error resetting database: {str(e)}", "danger", "Database")
        logging.error(f"Database reset error: {str(e)}")
        return redirect(url_for('index'))

# Create a placeholder template route
@app.route('/coming_soon')
def coming_soon():
    feature = request.args.get('feature', 'This feature')
    return render_template('coming_soon.html', feature=feature)

@app.route('/clear_agent_conversation')
def clear_agent_conversation():
    """Clear the agent conversation history"""
    # Clear the conversation history from the session
    if 'agent_conversation' in session:
        session['agent_conversation'] = []
    
    flash_with_context("Conversation history cleared", "info", "Agent Communication")
    return redirect(url_for('agent_communication'))

if __name__ == '__main__':
    if initialize_system(reset_db=True):
        # In development mode, use only one worker thread to avoid SQLite threading issues
        app.run(debug=True, threaded=False)
    else:
        print("Failed to initialize system. Exiting.")
        sys.exit(1) 