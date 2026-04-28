# Horizon Cinemas Booking System (HCBS)
## Manual Test Cases & Execution Report

| Test Case # | Category | Description | Test Dataset / Input | Expected Output | Actual Output | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Auth | Valid manager login | Username: `manager1`, Password: `password123` | Login succeeds, routes to Manager Window | As Expected | Pass |
| **TC-02** | Auth | Valid admin login | Username: `admin1`, Password: `password123` | Login succeeds, routes to Admin Window | As Expected | Pass |
| **TC-03** | Auth | Valid booking staff login | Username: `staff1`, Password: `password123` | Login succeeds, routes to Staff / Film Listing Window | As Expected | Pass |
| **TC-04** | Auth | Invalid password login attempt | Username: `staff1`, Password: `wrongpassword` | Login fails, error "Authentication failed" displayed | As Expected | Pass |
| **TC-05** | Auth | Booking staff tries to access Admin GUI | `staff1` session active, attempts to load `AdminWindow` | Access denied via RBAC, error dialog shown | As Expected | Pass |
| **TC-06** | Auth | Admin tries to access Manager GUI | `admin1` session active, attempts to load `ManagerWindow` | Access denied via RBAC, error dialog shown | As Expected | Pass |
| **TC-07** | Film Listing | View film listings for today | Select current date in calendar | Films scheduled for today appear in the list | As Expected | Pass |
| **TC-08** | Film Listing | Filter films by genre | Select 'Sci-Fi' from genre dropdown | Only Sci-Fi films are displayed in the view | As Expected | Pass |
| **TC-09** | Film Listing | Filter films by age rating | Select '15' from rating dropdown | Only films rated 15 or below are displayed | As Expected | Pass |
| **TC-10** | Booking | Book 2 lower hall tickets for Birmingham morning show | City: Birmingham, Type: Morning, Tier: Lower Hall, Qty: 2 | Total cost calculated exactly as £10.00 | As Expected | Pass |
| **TC-11** | Booking | Book 1 VIP ticket for London evening show | City: London, Type: Evening, Tier: VIP, Qty: 1 | Total cost calculated exactly as £17.28 | As Expected | Pass |
| **TC-12** | Booking | Check availability when show is fully booked | Select a showing with 0 seats remaining | Showing highlighted as 'Sold Out', booking button blocked | As Expected | Pass |
| **TC-13** | Booking | Attempt to book more than 7 days in advance | Select showing date 8+ days in future | Error message "Advance booking limit is 7 days" | As Expected | Pass |
| **TC-14** | Booking | Duplicate booking detection | Same customer_email, film_id, and date submitted | Error "Booking already exists for this customer" | As Expected | Pass |
| **TC-15** | Booking | Admin books for a different cinema (cross-cinema booking) | Admin role selects showing at a non-home cinema | Booking successful (Admins bypass home-cinema check) | As Expected | Pass |
| **TC-16** | Cancellation | Cancel a booking with >1 day notice | Cancel booking ref 2 days prior to show_date | Booking cancelled, 50% cancellation fee applied | As Expected | Pass |
| **TC-17** | Cancellation | Attempt same-day cancellation | Cancel booking ref on show_date | Cancellation blocked, error message displayed | As Expected | Pass |
| **TC-18** | Admin/Mgr | Admin adds a new film listing with show times | Title: "Dune", Genre: Sci-Fi, Screen: 1, Time: 19:00 | Film and showing successfully saved to database | As Expected | Pass |
| **TC-19** | Admin/Mgr | Manager adds a new cinema in a new city | City: "Manchester", Name: "Horizon Central" | Cinema successfully added and visible in cinema lists | As Expected | Pass |
| **TC-20** | Admin/Mgr | Admin generates monthly revenue report | Select past month for revenue report generation | Report generated showing revenue breakdowns | As Expected | Pass |
| **TC-21** | Security | SQL injection attempt in login username field | Username: `admin' OR 1=1;--` | Login fails securely, no DB compromise | As Expected | Pass |
| **TC-22** | Security | Session timeout after inactivity | Leave GUI completely idle for 15+ minutes | Auto-logout triggered, returns to Login Screen | As Expected | Pass |
| **TC-23** | Extra | Join waitlist when show is fully booked | Select 'Join Waitlist' on sold-out show, Input Name/Email | Customer successfully added to the waitlist | As Expected | Pass |
| **TC-24** | Extra | Generate PDF ticket with QR code | Complete a booking, select 'Print Ticket' | PDF generated securely with booking reference QR code | As Expected | Pass |
| **Summary** | | **Overall Execution Results** | | | | **24/24 Passed** |
