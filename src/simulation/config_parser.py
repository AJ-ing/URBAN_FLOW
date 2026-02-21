import json
import jsonschema
import os

class ConfigParser:
    """
    Parses and validates network configuration files.
    """
    
    def __init__(self, schema_path="docs/api/config_schema.json"):
        """Load JSON schema for validation"""
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def load_config(self, filepath):
        """
        Load configuration from JSON file.
        
        Args:
            filepath (str): Path to config file
            
        Returns:
            dict: Configuration data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If config is invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        # Validate against schema
        if not self.validate_config(config):
            raise ValueError("Invalid configuration")
        
        return config
    
    def validate_config(self, config):
        """
        Validate configuration against schema.
        
        Args:
            config (dict): Configuration to validate
            
        Returns:
            bool: True if valid
        """
        try:
            jsonschema.validate(instance=config, schema=self.schema)
            
            # Additional custom validations
            self._validate_no_orphans(config)
            self._validate_connections(config)
            
            return True
        except jsonschema.ValidationError as e:
            print(f"Schema validation error: {e}")
            return False
    
    def _validate_no_orphans(self, config):
        """Ensure no disconnected intersections"""
        intersection_ids = {i['id'] for i in config['network']['intersections']}
        connected_ids = set()
        
        for conn in config['network']['connections']:
            connected_ids.add(conn['from'].split('_')[0])
            connected_ids.add(conn['to'].split('_')[0])
        
        orphans = intersection_ids - connected_ids
        if orphans:
            raise ValueError(f"Orphaned intersections: {orphans}")
    
    def _validate_connections(self, config):
        """Ensure connections reference valid intersections"""
        valid_ids = {i['id'] for i in config['network']['intersections']}
        
        for conn in config['network']['connections']:
            from_id = conn['from'].split('_')[0]
            to_id = conn['to'].split('_')[0]
            
            if from_id not in valid_ids:
                raise ValueError(f"Invalid connection from: {from_id}")
            if to_id not in valid_ids:
                raise ValueError(f"Invalid connection to: {to_id}")
    
    def save_config(self, config, filepath):
        """
        Save configuration to JSON file.
        
        Args:
            config (dict): Configuration data
            filepath (str): Where to save
        """
        # Validate before saving
        if not self.validate_config(config):
            raise ValueError("Cannot save invalid config")
        
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write with nice formatting
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Configuration saved to {filepath}")