#!/bin/bash

echo "Running Unit tests"

pytest --random-order --cov=kommunitas --cov-config=.coveragerc tests/
