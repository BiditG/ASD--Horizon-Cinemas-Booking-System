# HCBS Project Architecture Document

This document outlines the architectural standards and technology stack for the Horizon Cinemas Booking System (HCBS).

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.11+ |
| **GUI Framework** | Tkinter (Primary) / PyQt5 |
| **Development Database** | SQLite (File-based) |
| **Production Database** | MySQL (Server-based) |
| **Security** | `bcrypt` (Password hashing) |
| **Ticketing** | `ReportLab` (PDF generation) |
| **QR Codes** | `qrcode` (Ticket validation) |

## 📁 Folder Structure

The project follows a modular structure to ensure maintainability and scalability:

- **`src/models/`**: Contains Data Transfer Objects (DTOs) and Object-Relational Mapping (ORM) classes representing database entities (e.g., `User`, `Movie`, `Booking`).
- **`src/gui/`**: Houses all graphical interface components, including windows, frames, and custom widgets built using Tkinter or PyQt5.
- **`src/database/`**: Contains database connection logic, configuration files, and initialization/seed scripts for both SQLite and MySQL.
- **`src/utils/`**: General-purpose helper functions, including the system's core pricing engine and data validators.
- **`src/ai/`**: Dedicated space for Machine Learning models and the integration of LLM agents for customer assistance.
- **`tests/`**: Contains unit and integration tests using the `pytest` framework.
- **`docs/`**: Project documentation, diagrams, and API references.
- **`assets/`**: Static assets such as images, logos, and fonts.

## 📏 Naming Conventions

To ensure code consistency across the team, the following naming conventions must be followed:

- **Files & Variables**: Use `snake_case` (e.g., `booking_manager.py`, `total_price`).
- **Classes**: Use `PascalCase` (e.g., `CinemaApp`, `UserSession`).
- **Constants**: Use `UPPER_CASE` (e.g., `MAX_SEATS`, `DB_CONNECTION_STRING`).
- **Functions/Methods**: Use `snake_case` (e.g., `calculate_discount()`).

## 🗄️ Database Strategy: SQLite vs. MySQL

The system is designed to support multiple database backends to accommodate different environments:

### SQLite (Development & Testing)
- **Usage**: Local development, CI/CD pipelines, and unit testing.
- **Why**: Zero configuration, file-based, and easy to reset. No external server requirement makes it ideal for individual developers.

### MySQL (Production)
- **Usage**: Staging and Production environments.
- **Why**: Handles concurrent connections, provides robust user access control, and offers better performance for large datasets and multiple simultaneous users in a real cinema environment.

> **Note**: All database interactions should be abstracted via the `models` and `database` modules to ensure the application logic remains database-agnostic.
