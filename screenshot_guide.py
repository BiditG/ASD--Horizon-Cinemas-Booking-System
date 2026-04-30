"""
screenshot_guide.py
===================
Portfolio Submission Guide: Test Evidence Screenshots

This document serves as a guide/script for the screenshots you need to capture 
for the Element 3 PDF submission. Follow these steps to generate the required 
evidence of both passing and failing test scenarios.

Required Screenshots:
-------------------
a) Full passing test run:
   - Run `python capture_test_output.py` or just `pytest` in your terminal.
   - Take a screenshot of the terminal showing all tests passing (green).

b) Individual test failures (At least 3):
   - Deliberately break a test to show failure output:
     1. Change a mathematical expectation (e.g. in `test_models.py` change `10.0` to `99.0` for a price test).
     2. Run `pytest` and take a screenshot of the specific failure traceback showing expected vs actual.
     3. Repeat for 2 other tests (e.g., change an expected Exception string).
   - *Crucial: Remember to restore the correct code afterwards!*

c) HTML Report:
   - Ensure you run the `run_tests.sh` script or run `pytest` (the pytest.ini handles generation).
   - Open `test_report.html` in your web browser.
   - Take a screenshot of the generated report page showing the summary table.

d) Application GUI Validation:
   - Launch `main.py` and log in as staff.
   - Take a screenshot of a successful booking confirmation.
   - Take a screenshot of a failed booking attempt (e.g., attempt to select a 'Sold Out' show).
   - Take a screenshot of a blocked cancellation (e.g., attempting to cancel on the same day).

e) Admin/Manager Report Data:
   - Log in as Manager.
   - Generate the monthly revenue report.
   - Take a screenshot of the generated report window showing the populated data table/graphs.

f) Security (SQL Injection Blocked):
   - Launch the application to the login screen.
   - Enter exactly `admin' OR 1=1;--` into the username field.
   - Take a screenshot of the application gracefully blocking the attempt (showing the standard
     "Authentication failed" error dialog rather than allowing unauthorized access).
"""
