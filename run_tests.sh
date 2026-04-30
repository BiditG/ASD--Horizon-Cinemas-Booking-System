#!/bin/bash
# run_tests.sh
# Script to install dependencies, run test suites, and generate all reports for HCBS.

echo "=========================================="
echo "    HCBS Test Execution & Report Gen      "
echo "=========================================="

echo "1. Installing pytest and reporting plugins..."
pip install pytest pytest-html

echo "------------------------------------------"
echo "2. Executing pytest suite and generating reports..."
# The options (--html, --junitxml, -v, -s) are automatically pulled from pytest.ini
python -m pytest tests/

echo "------------------------------------------"
echo "3. Running programmatic capture script..."
python capture_test_output.py

echo "=========================================="
echo "                   DONE                   "
echo "=========================================="
echo "The following evidence files have been generated:"
echo "- test_report.html (Open in browser for Screenshot C)"
echo "- test_results.xml (JUnit XML report format)"
echo "- test_output_YYYY-MM-DD.txt (Terminal output text file)"
