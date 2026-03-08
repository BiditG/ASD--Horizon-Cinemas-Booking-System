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

## 🔐 Credentials

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
