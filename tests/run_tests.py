"""
Simple script to run the test suite
"""
import os
import sys
import pytest

def main():
    """Run the test suite."""
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the project root directory
    project_dir = os.path.dirname(test_dir)
    
    # Add the project directory to the Python path
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Run the tests
    exit_code = pytest.main([
        test_dir,
        '-v',  # Verbose output
        '--tb=short',  # Short traceback
        '--no-header',  # No header
        '--no-summary',  # No summary
    ])
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 