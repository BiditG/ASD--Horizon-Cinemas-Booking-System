"""
src/utils/noshow_predictor.py
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
import joblib
import os

MODEL_PATH = "noshow_model.pkl"

def generate_mock_noshow_data(n=500):
    """
    Generate a synthetic DataFrame with features and a 'no_show' binary label.
    Realistic patterns:
    - Long lead time increases no-show risk.
    - Weekend evening shows have higher no-show risk.
    - Larger groups have slightly higher no-show risk.
    - VIP tickets have lower no-show risk.
    """
    np.random.seed(42)
    
    booking_lead_days = np.random.randint(0, 30, n)
    show_time_hour = np.random.randint(8, 24, n)
    day_of_week = np.random.randint(0, 7, n)
    ticket_type = np.random.randint(0, 3, n) # 0: lower, 1: upper, 2: vip
    num_tickets = np.random.randint(1, 10, n)
    cinema_city = np.random.randint(0, 5, n)
    month = np.random.randint(1, 13, n)
    
    # Base logits (negative means default mostly show up)
    logits = -2.0 
    logits += booking_lead_days * 0.05
    
    is_weekend = (day_of_week >= 4).astype(int)
    is_evening = (show_time_hour >= 18).astype(int)
    logits += is_weekend * is_evening * 1.5
    
    logits += num_tickets * 0.1
    logits -= (ticket_type == 2).astype(int) * 1.0
    
    # Sigmoid function to get probabilities
    probs = 1 / (1 + np.exp(-logits))
    no_show = np.random.binomial(1, probs)
    
    df = pd.DataFrame({
        "booking_lead_days": booking_lead_days,
        "show_time_hour": show_time_hour,
        "day_of_week": day_of_week,
        "ticket_type": ticket_type,
        "num_tickets": num_tickets,
        "cinema_city": cinema_city,
        "month": month,
        "no_show": no_show
    })
    return df

def train_noshow_model():
    """Train the logistic regression model on mock data and save to file."""
    df = generate_mock_noshow_data(500)
    
    X = df.drop(columns=["no_show"])
    y = df["no_show"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    print("--- No-Show Predictor Training Results ---")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.2f}")
    print(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.2f}")
    print(f"Recall:    {recall_score(y_test, y_pred, zero_division=0):.2f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))
    
    joblib.dump(model, MODEL_PATH)
    return model

def predict_noshow(booking: dict) -> float:
    """
    Returns the probability (0.0 to 1.0) of a no-show.
    """
    if not os.path.exists(MODEL_PATH):
        train_noshow_model()
        
    model = joblib.load(MODEL_PATH)
    
    df = pd.DataFrame([{
        "booking_lead_days": booking.get("booking_lead_days", 0),
        "show_time_hour": booking.get("show_time_hour", 12),
        "day_of_week": booking.get("day_of_week", 0),
        "ticket_type": booking.get("ticket_type", 0),
        "num_tickets": booking.get("num_tickets", 1),
        "cinema_city": booking.get("cinema_city", 0),
        "month": booking.get("month", 1)
    }])
    
    prob = model.predict_proba(df)[0][1]
    return float(prob)
