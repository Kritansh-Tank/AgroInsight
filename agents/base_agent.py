class BaseAgent:
    """Base class for all agents in the sustainable farming multi-agent system."""
    
    def __init__(self, name, db_connection):
        """Initialize the base agent.
        
        Args:
            name (str): Name of the agent
            db_connection: Connection to the SQLite database
        """
        self.name = name
        self.db = db_connection
        self.state = {}
        self.log_creation()
    
    def log_creation(self):
        """Log the creation of this agent in the database."""
        self.db.log_agent_interaction(
            agent_name=self.name,
            action_type="creation",
            action_details=f"Agent {self.name} was initialized"
        )
    
    def log_action(self, action_type, action_details):
        """Log an action taken by this agent in the database.
        
        Args:
            action_type (str): Type of action taken
            action_details (str): Details about the action
        """
        self.db.log_agent_interaction(
            agent_name=self.name,
            action_type=action_type,
            action_details=action_details
        )
    
    def update_state(self, key, value):
        """Update the agent's internal state.
        
        Args:
            key (str): State variable name
            value: Value to set
        """
        self.state[key] = value
        
    def get_state(self, key, default=None):
        """Get a value from the agent's internal state.
        
        Args:
            key (str): State variable name
            default: Default value if key doesn't exist
            
        Returns:
            The value or default if key doesn't exist
        """
        return self.state.get(key, default)
    
    def process_input(self, input_data):
        """Process input data - to be implemented by subclasses.
        
        Args:
            input_data: Data to process
            
        Returns:
            Processed output
        """
        raise NotImplementedError("Subclasses must implement process_input method")
    
    def generate_recommendations(self, context):
        """Generate recommendations based on context - to be implemented by subclasses.
        
        Args:
            context: Context data for generating recommendations
            
        Returns:
            List of recommendations
        """
        raise NotImplementedError("Subclasses must implement generate_recommendations method")
    
    def communicate(self, target_agent, message):
        """Send a message to another agent.
        
        Args:
            target_agent: The agent to communicate with
            message: The message to send
            
        Returns:
            Response from the target agent
        """
        self.log_action(
            action_type="communication",
            action_details=f"Sent message to {target_agent.name}: {message[:100]}..."
        )
        return target_agent.receive_message(self, message)
    
    def receive_message(self, sender_agent, message):
        """Receive a message from another agent.
        
        Args:
            sender_agent: The agent that sent the message
            message: The received message
            
        Returns:
            Response to the sender
        """
        self.log_action(
            action_type="communication",
            action_details=f"Received message from {sender_agent.name}: {message[:100]}..."
        )
        # Default implementation just acknowledges receipt
        return {"status": "received", "message": "Message received"} 
