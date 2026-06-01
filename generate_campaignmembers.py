"""
Salesforce CampaignMember Data Generator Wrapper.

This root-level script serves as the CLI entry point. It imports the core generator 
implementation from the generators package and executes it.

Author: Senior Data Engineer
"""

import sys
import os

# Ensure the generators package is importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "generators"))

from generators.generate_campaignmembers import main

if __name__ == "__main__":
    main()
