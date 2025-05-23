"""
Configuration settings for ProlabDep package
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the ProlabDep package"""

    DEFAULT_SETTINGS = {
        'date_formats': [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d'
        ],
        'param_dict_path': 'param_dict.json',
        'detection_limit_fraction': 2,
        'database': {
            'type': 'sqlite',
            'path': 'prolabdep.db'
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': None
        },
        'export': {
            'default_format': 'excel',
            'pdf': {
                'page_size': 'A4',
                'orientation': 'portrait'
            }
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration with optional custom settings file
        
        Parameters
        ----------
        config_path : str, optional
            Path to a JSON configuration file
        """
        self._settings = self.DEFAULT_SETTINGS.copy()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_settings = json.load(f)
                    self._update_settings(custom_settings)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        
        # Set up logging based on configuration
        self._setup_logging()
    
    def _update_settings(self, custom_settings: Dict[str, Any]) -> None:
        """
        Update settings with custom values
        
        Parameters
        ----------
        custom_settings : Dict[str, Any]
            Dictionary with custom configuration values
        """
        for key, value in custom_settings.items():
            if isinstance(value, dict) and key in self._settings and isinstance(self._settings[key], dict):
                self._settings[key].update(value)
            else:
                self._settings[key] = value
    
    def _setup_logging(self) -> None:
        """Set up logging based on configuration"""
        log_config = self._settings.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = log_config.get('file')
        
        handlers = []
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            handlers.append(logging.FileHandler(log_file))
        
        # Always add console handler
        handlers.append(logging.StreamHandler())
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=log_format,
            handlers=handlers
        )
    
    @property
    def date_formats(self) -> List[str]:
        """List of date formats to try when parsing dates"""
        return self._settings['date_formats']
    
    @property
    def param_dict_path(self) -> str:
        """Path to the parameter dictionary JSON file"""
        return self._settings['param_dict_path']
    
    @property
    def detection_limit_fraction(self) -> int:
        """Fraction to divide detection limit values by"""
        return self._settings['detection_limit_fraction']
    
    @property
    def database_config(self) -> Dict[str, str]:
        """Database configuration settings"""
        return self._settings['database']
    
    @property
    def export_config(self) -> Dict[str, Any]:
        """Export configuration settings"""
        return self._settings['export']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Parameters
        ----------
        key : str
            Configuration key
        default : Any, optional
            Default value if key not found
            
        Returns
        -------
        Any
            Configuration value
        """
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Parameters
        ----------
        key : str
            Configuration key
        value : Any
            Value to set
        """
        self._settings[key] = value
    
    def save(self, config_path: str) -> None:
        """
        Save configuration to a file
        
        Parameters
        ----------
        config_path : str
            Path to save the configuration
        """
        try:
            # Create directory if it doesn't exist
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(config_path, 'w') as f:
                json.dump(self._settings, f, indent=2)
            logger.info(f"Saved configuration to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {str(e)}")
            raise


# Default configuration instance
config = Config() 