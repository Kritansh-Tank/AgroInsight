import json
import sys
import argparse
from models.multi_agent_system import SustainableFarmingSystem

def display_section(title):
    """Display a section title."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)

def pretty_print(data):
    """Pretty print dictionary data."""
    if isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=2))
    else:
        print(data)

def demo_query_market_data(system):
    """Demonstrate querying market data."""
    display_section("MARKET DATA QUERY")
    
    # Query general market overview
    print("\n[1] General Market Overview:")
    market_overview = system.query_market_data()
    
    # Print top 3 profitable crops
    if market_overview.get("status") == "success" and "market_overview" in market_overview:
        top_crops = market_overview["market_overview"]["top_profit_potential_crops"]
        print("\nTop 3 Profitable Crops:")
        for i, crop in enumerate(top_crops):
            print(f"  {i+1}. {crop['product']}: {crop['recommendation']}")
    
    # Query specific crop data
    print("\n[2] Specific Crop Analysis (Rice):")
    rice_analysis = system.query_market_data(product="Rice")
    
    if rice_analysis.get("status") == "success" and "market_analysis" in rice_analysis:
        analysis = rice_analysis["market_analysis"]
        print(f"\nRice Market Status: {analysis['market_status']}")
        print(f"Average Price: ${analysis['avg_market_price']:.2f} per ton")
        print(f"Price Forecast: {analysis['price_forecast']['forecast_message']}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(analysis['market_recommendations']):
            print(f"  {i+1}. {rec['focus']}: {rec['action']}")

def demo_query_weather_data(system):
    """Demonstrate querying weather data."""
    display_section("WEATHER DATA QUERY")
    
    # Query weather data for central region
    print("\n[1] Central Region 7-Day Forecast:")
    weather_data = system.query_weather_data(region="central")
    
    if weather_data.get("status") == "success":
        print("\nCurrent Weather:")
        current = weather_data["current_weather"]
        print(f"  Condition: {current['condition']}")
        print(f"  Temperature: {current['temperature_c']}°C")
        print(f"  Rainfall: {current['rainfall_mm']} mm")
        
        print("\n7-Day Forecast Summary:")
        for i, day in enumerate(weather_data["forecast"][:5]):  # Show first 5 days
            print(f"  Day {day['day']} ({day['date']}): {day['condition']}, " +
                  f"High: {day['temperature_high_c']}°C, Low: {day['temperature_low_c']}°C, " +
                  f"Rainfall: {day['rainfall_mm']} mm")
    
    # Query agricultural impact
    print("\n[2] Agricultural Impact Assessment:")
    if "agricultural_impact" in weather_data:
        impact = weather_data["agricultural_impact"]
        print(f"  Overall Impact: {impact['overall_impact']}")
        print(f"  Temperature Impact: {impact['temperature_impact']}")
        print(f"  Rainfall Impact: {impact['rainfall_impact']}")
        
        print("\n  Key Recommendations:")
        for i, rec in enumerate(impact['recommendations'][:2]):
            print(f"    {i+1}. {rec['issue']}: {rec['action']}")

def demo_analyze_new_farm(system):
    """Demonstrate analyzing a new farm."""
    display_section("NEW FARM ANALYSIS")
    
    # Define farm parameters
    soil_ph = 6.7
    soil_moisture = 28.5
    temperature_c = 24.2
    rainfall_mm = 180.5
    region = "central"
    
    print(f"\nAnalyzing New Farm with Parameters:")
    print(f"  Soil pH: {soil_ph}")
    print(f"  Soil Moisture: {soil_moisture}%")
    print(f"  Average Temperature: {temperature_c}°C")
    print(f"  Average Rainfall: {rainfall_mm} mm")
    print(f"  Region: {region}")
    
    analysis = system.analyze_new_farm(
        soil_ph=soil_ph,
        soil_moisture=soil_moisture,
        temperature_c=temperature_c,
        rainfall_mm=rainfall_mm,
        region=region
    )
    
    if analysis.get("status") == "success":
        # Display soil analysis
        if "soil_analysis" in analysis["initial_analysis"]:
            soil = analysis["initial_analysis"]["soil_analysis"]
            print("\n[1] Soil Analysis:")
            print(f"  pH Status: {soil.get('ph_status', 'Unknown')}")
            print(f"  Moisture Status: {soil.get('moisture_status', 'Unknown')}")
            
            if "recommendations" in soil and soil["recommendations"]:
                print("\n  Soil Recommendations:")
                for i, rec in enumerate(soil["recommendations"]):
                    print(f"    {i+1}. {rec['issue']}: {rec['action']}")
        
        # Display climate analysis
        if "climate_analysis" in analysis["initial_analysis"]:
            climate = analysis["initial_analysis"]["climate_analysis"]
            print("\n[2] Climate Analysis:")
            print(f"  Temperature Category: {climate.get('temperature_category', 'Unknown')}")
            print(f"  Rainfall Category: {climate.get('rainfall_category', 'Unknown')}")
            
            if "suitable_crops" in climate:
                print("\n  Suitable Crops Based on Climate:")
                print(f"    {', '.join(climate['suitable_crops'])}")
            
            if "recommendations" in climate and climate["recommendations"]:
                print("\n  Climate Recommendations:")
                for i, rec in enumerate(climate["recommendations"]):
                    print(f"    {i+1}. {rec['issue']}: {rec['action']}")
        
        # Display recommended crops
        if "recommended_crops" in analysis:
            print("\n[3] Recommended Crops (Market & Climate Matched):")
            for i, crop in enumerate(analysis["recommended_crops"]):
                print(f"  {i+1}. {crop['crop']} - Economic Potential: {crop['economic_potential']}")
                print(f"     {crop['market_recommendation']}")

def demo_farm_recommendations(system):
    """Demonstrate comprehensive farm recommendations."""
    display_section("COMPREHENSIVE FARM RECOMMENDATIONS")
    
    # Choose a random farm ID (1-100)
    farm_id = 42
    region = "central"
    sustainability_preference = 7  # Higher sustainability preference
    
    print(f"\nGenerating recommendations for Farm #{farm_id}:")
    print(f"  Region: {region}")
    print(f"  Sustainability Preference: {sustainability_preference}/10")
    
    recommendations = system.generate_farm_recommendations(
        farm_id=farm_id,
        region=region,
        financial_goal="balance",
        sustainability_preference=sustainability_preference
    )
    
    if recommendations.get("status") != "error":
        # Display farm data
        farm_data = recommendations["farm_data"]
        print("\n[1] Farm Information:")
        print(f"  Crop Type: {farm_data['crop_type']}")
        print(f"  Current Sustainability Score: {farm_data['sustainability_score']:.2f}")
        print(f"  Soil pH: {farm_data['soil_ph']}")
        print(f"  Current Yield: {farm_data['crop_yield_ton']:.2f} tons")
        
        # Display sustainability summary
        summary = recommendations["sustainability_summary"]
        print("\n[2] Sustainability Impact Summary:")
        print(f"  Current Score: {summary['current_score']:.2f}")
        print(f"  Potential Score: {summary['potential_score']:.2f}")
        print(f"  Potential Improvement: {summary['improvement_percentage']:.2f}%")
        
        # Display high priority actions
        print("\n[3] High Priority Actions (Top 5):")
        for i, action in enumerate(recommendations["high_priority_actions"]):
            print(f"  {i+1}. [{action['category']}] {action.get('focus', '')}")
            print(f"     Action: {action['action']}")
            print(f"     Sustainability Impact: +{action['sustainability_impact']:.2f}")
            print(f"     Economic Impact: {action['economic_impact']:+.2f}")
            print(f"     Confidence: {action['confidence']:.2f}")
            print()
        
        # Display a sample of detailed recommendations from each category
        print("\n[4] Sample Detailed Recommendations by Category:")
        
        # Sample from farming recommendations
        if recommendations["farming_recommendations"]:
            category = recommendations["farming_recommendations"][0]
            print(f"\n  {category['category']} - {category['explanation']}")
            for i, rec in enumerate(category["recommendations"][:2]):
                print(f"    {i+1}. {rec.get('focus', '')}: {rec['action']}")
        
        # Sample from market recommendations
        if recommendations["market_recommendations"]:
            category = recommendations["market_recommendations"][0]
            print(f"\n  {category['category']} - {category['explanation']}")
            for i, rec in enumerate(category["recommendations"][:2]):
                print(f"    {i+1}. {rec.get('focus', '')}: {rec['action']}")
        
        # Sample from weather recommendations
        if recommendations["weather_recommendations"]:
            category = recommendations["weather_recommendations"][0]
            print(f"\n  {category['category']} - {category['explanation']}")
            for i, rec in enumerate(category["recommendations"][:2]):
                print(f"    {i+1}. {rec.get('focus', '')}: {rec['action']}")
        
        # Display LLM-enhanced recommendations if available
        if "llm_farm_analysis" in recommendations:
            print("\n[5] AI-Enhanced Farm Analysis (via Ollama):")
            print(recommendations["llm_farm_analysis"])
        
        if "llm_market_insights" in recommendations:
            print("\n[6] AI-Enhanced Market Insights (via Ollama):")
            print(recommendations["llm_market_insights"])
        
        if "llm_weather_insights" in recommendations:
            print("\n[7] AI-Enhanced Weather Recommendations (via Ollama):")
            print(recommendations["llm_weather_insights"])
    else:
        print(f"Error: {recommendations.get('message', 'Unknown error')}")

def demo_sustainability_comparison(system):
    """Demonstrate sustainability comparison across farms."""
    display_section("SUSTAINABILITY COMPARISON")
    
    # Get overall sustainability comparison
    print("\n[1] Overall Sustainability Comparison:")
    comparison = system.get_sustainability_comparison()
    
    if comparison.get("status") == "success":
        stats = comparison["sustainability_stats"]
        print(f"\n  Average Sustainability Score: {stats['avg_sustainability_score']:.2f}")
        print(f"  Range: {stats['min_sustainability_score']:.2f} - {stats['max_sustainability_score']:.2f}")
        print(f"  Total Farms: {stats['count']}")
        
        # Display crop comparison
        if "crop_comparison" in stats:
            print("\n  Sustainability by Crop Type:")
            for i, crop in enumerate(stats["crop_comparison"]):
                print(f"    {i+1}. {crop['crop_type']}: {crop['avg_sustainability_score']:.2f} " +
                      f"(from {crop['farm_count']} farms)")
        
        # Display efficiency stats
        efficiency = comparison["efficiency_stats"]
        print("\n  Efficiency Metrics:")
        print(f"    Average Fertilizer Efficiency: {efficiency['avg_fertilizer_efficiency']:.4f} tons/kg")
        print(f"    Average Pesticide Efficiency: {efficiency['avg_pesticide_efficiency']:.4f} tons/kg")
        
        # Display best practices
        print("\n  Best Practices from Top Sustainable Farms:")
        for i, farm in enumerate(efficiency["best_practices"][:3]):
            print(f"    Farm #{farm['farm_id']} ({farm['crop_type']}):")
            print(f"      Sustainability Score: {farm['sustainability_score']:.2f}")
            print(f"      Fertilizer Efficiency: {farm['fertilizer_efficiency']:.4f} tons/kg")
            print(f"      Pesticide Efficiency: {farm['pesticide_efficiency']:.4f} tons/kg")
    
    # Get crop-specific comparison
    crop_type = "Rice"
    print(f"\n[2] {crop_type}-Specific Sustainability Comparison:")
    crop_comparison = system.get_sustainability_comparison(crop_type=crop_type)
    
    if crop_comparison.get("status") == "success":
        stats = crop_comparison["sustainability_stats"]
        print(f"\n  {crop_type} Average Sustainability Score: {stats['avg_sustainability_score']:.2f}")
        print(f"  {crop_type} Range: {stats['min_sustainability_score']:.2f} - {stats['max_sustainability_score']:.2f}")
        print(f"  Total {crop_type} Farms: {stats['count']}")
        
        # Display efficiency stats
        efficiency = crop_comparison["efficiency_stats"]
        print(f"\n  {crop_type} Efficiency Metrics:")
        print(f"    Average Fertilizer Efficiency: {efficiency['avg_fertilizer_efficiency']:.4f} tons/kg")
        print(f"    Average Pesticide Efficiency: {efficiency['avg_pesticide_efficiency']:.4f} tons/kg")

def demo_agent_communication(system):
    """Demonstrate inter-agent communication."""
    display_section("AGENT COMMUNICATION DEMONSTRATION")
    
    farm_id = 42
    region = "central"
    
    print(f"\nDemonstrating communication between agents for Farm #{farm_id}:")
    result = system.agent_communication_test(farm_id, region)
    
    if result.get("status") == "success":
        farm_data = result["farm_data"]
        print(f"\n[1] Farm Information:")
        print(f"  Crop Type: {farm_data['crop_type']}")
        
        # Display weather forecast results
        if result["weather_forecast_response"].get("status") == "success":
            print("\n[2] Weather Station Response:")
            print(f"  Forecast Provided: {len(result['weather_forecast_response']['forecast'])} days")
            print(f"  Agricultural Impact Assessed: {result['weather_forecast_response']['agricultural_impact']['overall_impact']}")
        
        # Display market analysis results
        if result["market_analysis_response"].get("status") == "success":
            analysis = result["market_analysis_response"]["market_analysis"]
            print("\n[3] Market Researcher Response:")
            print(f"  Market Status: {analysis['market_status']}")
            print(f"  Price Forecast: {analysis['price_forecast']['forecast_message']}")
            print("  Recommendations:")
            for i, rec in enumerate(analysis['market_recommendations'][:2]):
                print(f"    {i+1}. {rec['focus']}: {rec['action']}")
        
        # Display planting advice
        if result["planting_advice_response"].get("status") == "success":
            advice = result["planting_advice_response"]["planting_advice"]
            print("\n[4] Weather Station Planting Advice:")
            print(f"  Current Season: {advice['current_season']}")
            print("  Recommendations:")
            for i, rec in enumerate(advice['recommendations']):
                print(f"    {i+1}. {rec['issue']}: {rec['action']}")

def demo_ollama_llm(system):
    """Demonstrate Ollama LLM capabilities."""
    display_section("OLLAMA LLM INTEGRATION DEMO")
    
    if not hasattr(system, 'llm') or not system.use_llm:
        print("\nOllama LLM integration is not available. Please check your connection to the Ollama service.")
        return
    
    # Get a specific farm for analysis
    farm_id = 42
    farm_data = system.db.get_farm_data(farm_id)
    if not farm_data:
        print(f"Error: Farm ID {farm_id} not found")
        return
    
    print(f"\n[1] AI Farm Analysis for Farm #{farm_id} (Crop: {farm_data['crop_type']})")
    print("\nSending request to Ollama service...")
    
    # Get LLM farm analysis
    analysis_result = system.llm.analyze_farm_data(farm_data)
    
    if analysis_result.get("status") == "success":
        print("\nAI Analysis:")
        print(analysis_result["generated_text"])
        print(f"\nModel: {analysis_result['model_info']}")
    else:
        print(f"\nError: {analysis_result.get('message', 'Unknown error')}")
    
    # Get crop-specific market analysis
    print("\n[2] AI Market Analysis")
    print("\nSending request to Ollama service...")
    
    market_data = system.db.get_market_data()
    market_result = system.llm.generate_market_insights(market_data, farm_data["crop_type"])
    
    if market_result.get("status") == "success":
        print("\nAI Market Insights:")
        print(market_result["generated_text"])
        print(f"\nModel: {market_result['model_info']}")
    else:
        print(f"\nError: {market_result.get('message', 'Unknown error')}")
    
    # Test custom prompt
    print("\n[3] Custom AI Query")
    custom_prompt = input("\nEnter a custom agriculture-related question: ")
    if custom_prompt:
        print("\nSending request to Ollama service...")
        custom_result = system.llm.generate(custom_prompt, temperature=0.7)
        
        if custom_result.get("status") == "success":
            print("\nAI Response:")
            print(custom_result["generated_text"])
            print(f"\nModel: {custom_result['model_info']}")
        else:
            print(f"\nError: {custom_result.get('message', 'Unknown error')}")
    
def demo_reset_database(system):
    """Demonstrate database reset functionality."""
    display_section("DATABASE RESET")
    
    print("\nWARNING: This will reset the entire database and reload initial data.")
    print("All existing recommendations and agent interactions will be lost.")
    
    confirm = input("\nAre you sure you want to reset the database? (y/n): ")
    
    if confirm.lower() == 'y':
        print("\nResetting database...")
        result = system.reset_database()
        
        if result.get("status") == "success":
            print("\nSuccess: " + result.get("message", "Database reset successfully"))
        else:
            print("\nError: " + result.get("message", "Failed to reset database"))
    else:
        print("\nDatabase reset cancelled.")

def run_all_demos(system, reset_db=False):
    """Run all demo functions in sequence."""
    if reset_db:
        # Reset database before running all demos if requested
        print("\nResetting database before running all demos...")
        result = system.reset_database()
        if result.get("status") != "success":
            print(f"Warning: {result.get('message', 'Database reset failed')}")
            confirm = input("\nContinue with demos anyway? (y/n): ")
            if confirm.lower() != 'y':
                return
    
    demo_query_market_data(system)
    demo_query_weather_data(system)
    demo_analyze_new_farm(system)
    demo_farm_recommendations(system)
    demo_sustainability_comparison(system)
    demo_agent_communication(system)
    
    if system.use_llm:
        demo_ollama_llm(system)

def main():
    """Main function to run the demonstration."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Sustainable Farming Multi-Agent System Demo')
        parser.add_argument('--use-llm', action='store_true', default=True, 
                            help='Enable Ollama LLM integration (default: True)')
        parser.add_argument('--no-llm', action='store_false', dest='use_llm',
                            help='Disable Ollama LLM integration')
        parser.add_argument('--reset-db', action='store_true', 
                            help='Reset database before starting')
        parser.add_argument('--run-all', action='store_true',
                            help='Run all demos automatically and exit')
        args = parser.parse_args()
        
        # Initialize the sustainable farming system
        print("Initializing Sustainable Farming System...")
        print(f"LLM Integration: {'Enabled' if args.use_llm else 'Disabled'}")
        system = SustainableFarmingSystem(use_llm=args.use_llm)
        
        # Reset database if requested via command line
        if args.reset_db:
            result = system.reset_database()
            if result.get("status") != "success":
                print(f"Warning: {result.get('message', 'Database reset failed')}")
        
        # Run all demos if requested and exit
        if args.run_all:
            print("\nRunning all demos with a clean database...")
            run_all_demos(system, reset_db=args.reset_db)
            system.close()
            return 0
        
        # Display menu
        while True:
            display_section("SUSTAINABLE FARMING MULTI-AGENT SYSTEM DEMO")
            print("\nDemo Options:")
            print("1. Query Market Data")
            print("2. Query Weather Data")
            print("3. Analyze New Farm")
            print("4. Generate Comprehensive Farm Recommendations")
            print("5. Sustainability Comparison")
            print("6. Agent Communication Test")
            
            if system.use_llm:
                print("7. Ollama LLM Integration Demo")
                print("8. Reset Database")
                print("9. Run All Demos (with clean database)")
                print("10. Exit")
                valid_choices = set('12345678910')
                max_choice = 10
            else:
                print("7. Reset Database")
                print("8. Run All Demos (with clean database)")
                print("9. Exit")
                valid_choices = set('123456789')
                max_choice = 9
            
            choice = input(f"\nEnter your choice (1-{max_choice}): ")
            
            if choice == '1':
                demo_query_market_data(system)
            elif choice == '2':
                demo_query_weather_data(system)
            elif choice == '3':
                demo_analyze_new_farm(system)
            elif choice == '4':
                demo_farm_recommendations(system)
            elif choice == '5':
                demo_sustainability_comparison(system)
            elif choice == '6':
                demo_agent_communication(system)
            elif choice == '7':
                if system.use_llm:
                    demo_ollama_llm(system)
                else:
                    demo_reset_database(system)
            elif choice == '8':
                if system.use_llm:
                    demo_reset_database(system)
                else:
                    run_all_demos(system, reset_db=True)
            elif choice == '9':
                if system.use_llm:
                    run_all_demos(system, reset_db=True)
                else:
                    break
            elif choice == '10' and system.use_llm:
                break
            elif choice not in valid_choices:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
        
        # Clean up
        system.close()
        print("Thank you for using the Sustainable Farming System Demo!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 