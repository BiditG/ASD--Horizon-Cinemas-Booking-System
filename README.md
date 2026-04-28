# Horizon Cinemas Booking System (HCBS)

HCBS is a comprehensive Python-based cinema booking system designed to streamline movie scheduling, seat reservations, and staff management. The system features a graphical user interface built with Tkinter and a persistent SQLite database.

## 🚀 Setup Instructions

Follow these steps to set up the project locally:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ASD--Horizon-Cinemas-Booking-System
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

### 🔐 Credentials

The following accounts are available for testing various access levels within the system:

| Role    | Username | Password   |
| :------ | :------- | :--------- |
| Manager | manager1 | password123 |
| Admin   | admin1   | password123 |
| Admin   | admin2   | password123 |
| Staff   | staff1   | password123 |
| Staff   | staff2   | password123 |
| Staff   | staff3   | password123 |

## 📦 Bulk Booking Feature

- **Group Booking Mode** automatically activates when the user selects a quantity of **10 or more** seats.
- Seats are auto‑selected using a best‑available algorithm that fills whole rows first and splits across the fewest rows when necessary.
- A banner appears in the booking UI indicating *Group Booking Mode* and the selected seats are highlighted in a distinct colour.
- The receipt displays a *Group Booking* summary with per‑seat cost.
- If insufficient contiguous seats are available, the system suggests the maximum possible group size.

## 🎨 Dark Mode

A persistent dark‑mode toggle is available on the admin and manager dashboards. The UI theme is saved per‑user in `user_prefs.json` and applied automatically on login.

## 🎁 Loyalty Points

Customers earn 1 point per £1 spent. Points are tracked per email and displayed via a loyalty popup. Tier badges (Bronze, Silver, Gold) are shown on the receipt.


The following accounts are available for testing various access levels within the system:

| Role    | Username | Password   |
| :------ | :------- | :--------- |
| Manager | manager1 | admin123   |
| Admin   | admin1   | admin123   |
| Staff   | staff1   | staff123   |

## 👥 Team Members

| Name | Student ID | Role |
| :--- | :--------- | :--- |
| Member 1 | [ID] | Project Lead / Backend |
| Member 2 | [ID] | GUI Developer |
| Member 3 | [ID] | Database Administrator |
| Member 4 | [ID] | AI Integration |
| Member 5 | [ID] | QA / Documentation |

## 📁 Project Structure

- `src/models/`: Data models and business logic.
- `src/gui/`: Tkinter interface components.
- `src/database/`: SQLite database scripts and connection logic.
- `src/utils/`: Helper functions and utilities.
- `src/ai/`: Artificial Intelligence modules.
- `tests/`: Unit and integration tests.
- `docs/`: Project documentation and user guides.
- `assets/`: Images, icons, and other static files.
