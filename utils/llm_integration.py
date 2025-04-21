import requests
import json
import os
import time

class OllamaLLM:
    """
    Integration with Ollama LLM service for enhanced agricultural recommendations
    and natural language processing capabilities.
    """
    
    def __init__(self, base_url="http://35.154.211.247:11434", model="qwen2.5:0.5b"):
        """Initialize the Ollama LLM connector with the specified model and URL."""
        self.base_url = base_url
        self.model = model
        self.api_endpoint = f"{self.base_url}/api/generate"
        self.completion_endpoint = f"{self.base_url}/api/completion"
        self.direct_endpoint = f"{self.base_url}/api"
        
        # Verify connection on initialization
        self.is_available = self._check_connection()
        if self.is_available:
            print(f"Successfully connected to Ollama at {self.base_url}")
            # Try to identify the best API endpoint
            self.api_version = self._detect_api_version()
            print(f"Using Ollama model: {self.model}")
            print(f"API endpoint: {self.api_version}")
        else:
            print(f"Warning: Could not connect to Ollama at {self.base_url}")
            self.api_version = "unknown"
    
    def _check_connection(self):
        """Check if the Ollama service is available."""
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            return False
            
    def _detect_api_version(self):
        """Detect which Ollama API version/format to use."""
        if not self.is_available:
            return "unknown"
            
        # Try the direct endpoint first (simple text response format)
        try:
            test_payload = {"prompt": "Hello", "model": self.model}
            response = requests.post(self.direct_endpoint, json=test_payload, timeout=2)
            if response.status_code == 200:
                # If this works and returns text directly, use this simplest approach
                return "direct"
        except:
            pass
            
        # Try the completion endpoint next (newer Ollama versions)
        try:
            test_payload = {
                "model": self.model,
                "prompt": "Hello",
                "stream": False
            }
            response = requests.post(self.completion_endpoint, json=test_payload, timeout=2)
            if response.status_code == 200:
                return "completion"
        except:
            pass
            
        # Fallback to generate endpoint
        return "generate"
    
    def generate(self, prompt, temperature=0.7, max_tokens=500):
        """
        Generate a response from the LLM.
        
        Args:
            prompt (str): Input prompt for the model
            temperature (float): Creativity parameter (0.0-1.0)
            max_tokens (int): Maximum number of tokens to generate
            
        Returns:
            dict: Response containing the generated text or error message
        """
        if not self.is_available:
            return {"status": "error", "message": "Ollama service is not available"}
        
        # Try the preferred API format based on detection
        if self.api_version == "direct":
            result = self._generate_direct(prompt, temperature, max_tokens)
            if result["status"] == "success":
                return result
        elif self.api_version == "completion":
            result = self._generate_completion(prompt, temperature, max_tokens)
            if result["status"] == "success":
                return result
        elif self.api_version == "generate":
            result = self._generate_with_fallback(prompt, temperature, max_tokens)
            if result["status"] == "success":
                return result
                
        # If the preferred method failed or we don't know the version,
        # try all endpoints in sequence
        return self._try_all_endpoints(prompt, temperature, max_tokens)
    
    def _generate_completion(self, prompt, temperature, max_tokens):
        """Use the completion API endpoint (newer Ollama versions)."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(self.completion_endpoint, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "generated_text": result.get("response", ""),
                    "model_info": f"{self.model} via Ollama (completion API)"
                }
            else:
                return {"status": "error", "message": f"Completion API failed with status {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error with completion API: {str(e)}"}
    
    def _generate_with_fallback(self, prompt, temperature, max_tokens):
        """Use the generate API endpoint with fallbacks for various response formats."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(self.api_endpoint, json=payload)
            
            if response.status_code == 200:
                # Try multiple parsing approaches
                try:
                    # Approach 1: Standard JSON response
                    result = response.json()
                    return {
                        "status": "success", 
                        "generated_text": result.get("response", ""),
                        "model_info": f"{self.model} via Ollama"
                    }
                except json.JSONDecodeError:
                    # Approach 2: Try parsing the first line as JSON
                    try:
                        first_line = response.text.strip().split('\n')[0]
                        result = json.loads(first_line)
                        return {
                            "status": "success",
                            "generated_text": result.get("response", ""),
                            "model_info": f"{self.model} via Ollama"
                        }
                    except (json.JSONDecodeError, IndexError):
                        # Approach 3: Try the streaming format (concatenate multiple responses)
                        try:
                            lines = response.text.strip().split('\n')
                            full_text = ""
                            for line in lines:
                                if line.strip():
                                    try:
                                        resp = json.loads(line)
                                        full_text += resp.get("response", "")
                                    except:
                                        pass
                            
                            if full_text:
                                return {
                                    "status": "success",
                                    "generated_text": full_text,
                                    "model_info": f"{self.model} via Ollama (stream)"
                                }
                            else:
                                # Approach 4: Just return the raw text as a last resort
                                return {
                                    "status": "success",
                                    "generated_text": response.text.strip(),
                                    "model_info": f"{self.model} via Ollama (raw)"
                                }
                        except:
                            # Final fallback
                            return {
                                "status": "success",
                                "generated_text": response.text.strip(),
                                "model_info": f"{self.model} via Ollama (raw fallback)"
                            }
            else:
                return {
                    "status": "error",
                    "message": f"API request failed with status code {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Error generating response: {str(e)}"}
    
    def _generate_direct(self, prompt, temperature, max_tokens):
        """Use the direct API endpoint (simplest Ollama API format)."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_length": max_tokens,  # Some versions use max_length instead of max_tokens
                "raw": True  # Get raw output without formatting
            }
            
            response = requests.post(self.direct_endpoint, json=payload)
            
            if response.status_code == 200:
                # This endpoint typically returns the text directly
                return {
                    "status": "success",
                    "generated_text": response.text.strip(),
                    "model_info": f"{self.model} via Ollama (direct API)"
                }
            else:
                return {"status": "error", "message": f"Direct API failed with status {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error with direct API: {str(e)}"}
    
    def _try_all_endpoints(self, prompt, temperature, max_tokens):
        """Try all API endpoints one after another until one works."""
        # Try direct endpoint first (simplest)
        result = self._generate_direct(prompt, temperature, max_tokens)
        if result["status"] == "success" and result["generated_text"].strip():
            self.api_version = "direct"  # Update for future calls
            return result
            
        # Try completion endpoint next (newer versions)
        result = self._generate_completion(prompt, temperature, max_tokens)
        if result["status"] == "success" and result["generated_text"].strip():
            self.api_version = "completion"  # Update for future calls
            return result
            
        # Try generate endpoint with fallbacks (most complex but versatile)
        result = self._generate_with_fallback(prompt, temperature, max_tokens)
        if result["status"] == "success" and result["generated_text"].strip():
            self.api_version = "generate"  # Update for future calls
            return result
            
        # If all approaches failed, return the last error
        return {"status": "error", "message": "All Ollama API endpoints failed to generate a response"}
    
    def analyze_farm_data(self, farm_data):
        """
        Analyze farm data using LLM to generate insights.
        
        Args:
            farm_data (dict): Farm data dictionary with metrics
            
        Returns:
            dict: LLM analysis of the farm data
        """
        prompt = f"""
        Analyze this farm data and provide 3-5 key insights and recommendations:
        
        Soil pH: {farm_data.get('soil_ph', 'N/A')}
        Soil Moisture: {farm_data.get('soil_moisture', 'N/A')}%
        Temperature: {farm_data.get('temperature_c', 'N/A')}°C
        Rainfall: {farm_data.get('rainfall_mm', 'N/A')} mm
        Crop Type: {farm_data.get('crop_type', 'N/A')}
        Fertilizer Usage: {farm_data.get('fertilizer_usage_kg', 'N/A')} kg
        Pesticide Usage: {farm_data.get('pesticide_usage_kg', 'N/A')} kg
        Crop Yield: {farm_data.get('crop_yield_ton', 'N/A')} tons
        Sustainability Score: {farm_data.get('sustainability_score', 'N/A')}
        
        Focus on sustainability, resource optimization, and yield improvement.
        """
        
        return self.generate(prompt, temperature=0.3)
    
    def generate_market_insights(self, market_data, crop_type):
        """
        Generate market insights for a specific crop.
        
        Args:
            market_data (list): List of market data entries
            crop_type (str): Type of crop to analyze
            
        Returns:
            dict: LLM analysis of market opportunities
        """
        # Filter market data for the specific crop
        crop_market_data = next((item for item in market_data if item.get("product", "").lower() == crop_type.lower()), None)
        
        if not crop_market_data:
            return {"status": "error", "message": f"No market data found for {crop_type}"}
        
        prompt = f"""
        Generate strategic market insights for {crop_type} based on this data:
        
        Current Market Price: ${crop_market_data.get('market_price_per_ton', 'N/A')} per ton
        Demand Index: {crop_market_data.get('demand_index', 'N/A')} (higher is stronger demand)
        Supply Index: {crop_market_data.get('supply_index', 'N/A')} (higher is more supply)
        Competitor Price: ${crop_market_data.get('competitor_price_per_ton', 'N/A')} per ton
        Economic Indicator: {crop_market_data.get('economic_indicator', 'N/A')}
        Weather Impact: {crop_market_data.get('weather_impact_score', 'N/A')}
        Seasonal Factor: {crop_market_data.get('seasonal_factor', 'N/A')}
        Consumer Trend: {crop_market_data.get('consumer_trend_index', 'N/A')}
        
        Provide specific recommendations on:
        1. Optimal timing for selling
        2. Pricing strategy
        3. Market opportunity assessment
        4. Risk factors to consider
        """
        
        return self.generate(prompt, temperature=0.4)
    
    def enhance_weather_recommendations(self, weather_data, recommendations, crop_type):
        """
        Enhance weather-based recommendations using LLM.
        
        Args:
            weather_data (dict): Weather forecast data
            recommendations (list): Current recommendations
            crop_type (str): Type of crop
            
        Returns:
            dict: Enhanced recommendations with LLM insights
        """
        # Extract key weather points
        forecast_summary = []
        for i, day in enumerate(weather_data[:5]):  # First 5 days
            forecast_summary.append(
                f"Day {day.get('day', i+1)}: {day.get('condition', 'Unknown')}, " +
                f"High: {day.get('temperature_high_c', 'N/A')}°C, " +
                f"Rainfall: {day.get('rainfall_mm', 'N/A')} mm"
            )
        
        # Combine existing recommendations
        existing_recs = []
        for rec in recommendations:
            if "recommendations" in rec:
                for item in rec["recommendations"]:
                    existing_recs.append(f"- {item.get('focus', 'Recommendation')}: {item.get('action', '')}")
        
        prompt = f"""
        Enhance these weather-based farming recommendations for {crop_type} crops:
        
        WEATHER FORECAST:
        {chr(10).join(forecast_summary)}
        
        CURRENT RECOMMENDATIONS:
        {chr(10).join(existing_recs)}
        
        Provide 3 specific and detailed enhancements to these recommendations that are:
        1. More precise and actionable
        2. Focused on sustainability
        3. Tailored specifically for {crop_type} farming
        
        Format each enhancement as: "Enhancement: [brief title] - [detailed explanation]"
        """
        
        return self.generate(prompt, temperature=0.4) 