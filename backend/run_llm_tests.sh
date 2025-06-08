#!/bin/bash

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run tests with detailed logging
python3 -m pytest tests/test_llm_plan.py -v --log-cli-level=INFO 