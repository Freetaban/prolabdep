"""
Tests for the standardization utilities
"""
import pytest
from prolabdep.utils.standardization import StandardizationMappings, default_mappings, standardize_location_info


class TestStandardizationMappings:
    """Test the StandardizationMappings class"""
    
    def test_default_mappings(self):
        """Test that default mappings are initialized correctly"""
        mappings = StandardizationMappings()
        
        # Check that default mappings are loaded
        assert "dep. s. giusto" in mappings.site_mappings
        assert "ingresso" in mappings.sampling_point_mappings
        assert "cod" in mappings.parameter_mappings
        
        # Check specific mappings
        assert mappings.site_mappings["dep. s. giusto"] == "San Giusto"
        assert mappings.sampling_point_mappings["ingresso"] == "inlet"
        assert mappings.parameter_mappings["cod"] == "COD"
    
    def test_custom_mappings(self):
        """Test that custom mappings are applied correctly"""
        custom_sites = {"custom site": "Custom Site"}
        custom_points = {"custom point": "Custom Point"}
        custom_params = {"custom param": "Custom Param"}
        
        mappings = StandardizationMappings(
            site_mappings=custom_sites,
            sampling_point_mappings=custom_points,
            parameter_mappings=custom_params
        )
        
        # Check that custom mappings are added to defaults
        assert "custom site" in mappings.site_mappings
        assert "custom point" in mappings.sampling_point_mappings
        assert "custom param" in mappings.parameter_mappings
        
        # Check that default mappings are still present
        assert "dep. s. giusto" in mappings.site_mappings
        assert "ingresso" in mappings.sampling_point_mappings
        assert "cod" in mappings.parameter_mappings
    
    def test_standardize_site(self):
        """Test standardization of site names"""
        mappings = StandardizationMappings()
        
        # Test exact match
        assert mappings.standardize_site("dep. s. giusto") == "San Giusto"
        
        # Test case insensitivity
        assert mappings.standardize_site("DEP. S. GIUSTO") == "San Giusto"
        
        # Test partial match
        assert mappings.standardize_site("Impianto dep. s. giusto") == "San Giusto"
        
        # Test no match
        assert mappings.standardize_site("Unknown Site") == "Unknown Site"
        
        # Test empty input
        assert mappings.standardize_site("") == ""
        assert mappings.standardize_site(None) == ""
    
    def test_standardize_sampling_point(self):
        """Test standardization of sampling points"""
        mappings = StandardizationMappings()
        
        # Test exact match
        assert mappings.standardize_sampling_point("ingresso") == "inlet"
        
        # Test case insensitivity
        assert mappings.standardize_sampling_point("INGRESSO") == "inlet"
        
        # Test partial match
        assert mappings.standardize_sampling_point("punto ingresso") == "inlet"
        
        # Test no match
        assert mappings.standardize_sampling_point("Unknown Point") == "Unknown Point"
        
        # Test empty input
        assert mappings.standardize_sampling_point("") == ""
        assert mappings.standardize_sampling_point(None) == ""
    
    def test_standardize_parameter(self):
        """Test standardization of parameter names"""
        mappings = StandardizationMappings()
        
        # Test exact match
        assert mappings.standardize_parameter("cod") == "COD"
        
        # Test case insensitivity
        assert mappings.standardize_parameter("COD") == "COD"
        
        # Test partial match
        assert mappings.standardize_parameter("parameter cod") == "COD"
        
        # Test no match
        assert mappings.standardize_parameter("Unknown Parameter") == "Unknown Parameter"
        
        # Test empty input
        assert mappings.standardize_parameter("") == ""
        assert mappings.standardize_parameter(None) == ""
    
    def test_find_similar_sites(self):
        """Test finding similar site names"""
        mappings = StandardizationMappings()
        
        # Test exact match
        similar = mappings.find_similar_sites("dep. s. giusto")
        assert "San Giusto" in similar
        
        # Test fuzzy match
        similar = mappings.find_similar_sites("s. giusto")
        assert len(similar) > 0
        
        # Test no match
        similar = mappings.find_similar_sites("xxxxxxx")
        assert len(similar) == 0
        
        # Test empty input
        assert mappings.find_similar_sites("") == []
        assert mappings.find_similar_sites(None) == []
    
    def test_find_similar_sampling_points(self):
        """Test finding similar sampling point names"""
        mappings = StandardizationMappings()
        
        # Test exact match
        similar = mappings.find_similar_sampling_points("ingresso")
        assert "inlet" in similar
        
        # Test fuzzy match
        similar = mappings.find_similar_sampling_points("ingres")
        assert len(similar) > 0
        
        # Test no match
        similar = mappings.find_similar_sampling_points("xxxxxxx")
        assert len(similar) == 0
        
        # Test empty input
        assert mappings.find_similar_sampling_points("") == []
        assert mappings.find_similar_sampling_points(None) == []
    
    def test_find_similar_parameters(self):
        """Test finding similar parameter names"""
        mappings = StandardizationMappings()
        
        # Test exact match
        similar = mappings.find_similar_parameters("cod")
        assert "COD" in similar
        
        # Test fuzzy match
        similar = mappings.find_similar_parameters("co")
        assert len(similar) > 0
        
        # Test no match
        similar = mappings.find_similar_parameters("xxxxxxx")
        assert len(similar) == 0
        
        # Test empty input
        assert mappings.find_similar_parameters("") == []
        assert mappings.find_similar_parameters(None) == []
    
    def test_add_mappings(self):
        """Test adding new mappings"""
        mappings = StandardizationMappings()
        
        # Add new mappings
        mappings.add_site_mapping("new site", "New Site")
        mappings.add_sampling_point_mapping("new point", "New Point")
        mappings.add_parameter_mapping("new param", "New Param")
        
        # Check that new mappings are added
        assert "new site" in mappings.site_mappings
        assert "new point" in mappings.sampling_point_mappings
        assert "new param" in mappings.parameter_mappings
        
        # Check that standardization works with new mappings
        assert mappings.standardize_site("new site") == "New Site"
        assert mappings.standardize_sampling_point("new point") == "New Point"
        assert mappings.standardize_parameter("new param") == "New Param"


def test_default_mappings_singleton():
    """Test that default_mappings is a singleton"""
    # Modify the default mappings
    default_mappings.add_site_mapping("test site", "Test Site")
    
    # Create a new instance and check that the mapping is present
    mappings = StandardizationMappings()
    assert "test site" not in mappings.site_mappings


def test_standardize_location_info():
    """Test standardization of location information"""
    # Create test data
    location_info = {
        "site": "dep. s. giusto",
        "sampling_point": "ingresso",
        "other_field": "value"
    }
    
    # Standardize
    result = standardize_location_info(location_info)
    
    # Check that site and sampling point are standardized
    assert result["site"] == "San Giusto"
    assert result["sampling_point"] == "inlet"
    
    # Check that other fields are preserved
    assert result["other_field"] == "value"
    
    # Test with missing fields
    location_info = {"other_field": "value"}
    result = standardize_location_info(location_info)
    assert "site" not in result
    assert "sampling_point" not in result
    assert result["other_field"] == "value" 