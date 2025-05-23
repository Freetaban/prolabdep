"""
Tests for the Config class in the core module
"""
import os
import json
import tempfile
import pytest

from prolabdep.core.config import Config


@pytest.fixture
def temp_config_path():
    """Create a temporary config file for testing."""
    temp_config = {
        'date_formats': ['%Y-%m-%d', '%d/%m/%Y'],
        'detection_limit_fraction': 3,
        'database': {
            'type': 'sqlite',
            'path': 'test_db.db'
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(levelname)s: %(message)s'
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tmp:
        json.dump(temp_config, tmp)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up after test
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def test_default_config():
    """Test that default configuration is loaded correctly."""
    config = Config()
    
    # Check default values
    assert '%d/%m/%Y' in config.date_formats
    assert '%Y-%m-%d' in config.date_formats
    assert config.detection_limit_fraction == 2
    assert config.database_config['type'] == 'sqlite'
    assert config.database_config['path'] == 'prolabdep.db'


def test_custom_config(temp_config_path):
    """Test that custom configuration is loaded correctly."""
    config = Config(temp_config_path)
    
    # Check custom values
    assert config.date_formats == ['%Y-%m-%d', '%d/%m/%Y']
    assert config.detection_limit_fraction == 3
    assert config.database_config['type'] == 'sqlite'
    assert config.database_config['path'] == 'test_db.db'
    assert config.get('logging')['level'] == 'DEBUG'
    assert config.get('logging')['format'] == '%(levelname)s: %(message)s'


def test_get_set_methods():
    """Test getting and setting configuration values."""
    config = Config()
    
    # Test get method with default value
    assert config.get('non_existent_key', 'default_value') == 'default_value'
    
    # Test set method
    config.set('custom_key', 'custom_value')
    assert config.get('custom_key') == 'custom_value'
    
    # Test nested set
    config.set('nested', {'key1': 'value1', 'key2': 'value2'})
    assert config.get('nested')['key1'] == 'value1'
    assert config.get('nested')['key2'] == 'value2'


def test_save_config():
    """Test saving configuration to file."""
    config = Config()
    
    # Set a custom value
    config.set('test_key', 'test_value')
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        config.save(tmp_path)
        
        # Load the saved config
        with open(tmp_path, 'r') as f:
            saved_config = json.load(f)
        
        # Verify saved value
        assert saved_config['test_key'] == 'test_value'
        
        # Verify other keys are preserved
        assert 'date_formats' in saved_config
        assert 'database' in saved_config
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path) 