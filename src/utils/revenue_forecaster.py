"""
src/utils/revenue_forecaster.py
"""

import pandas as pd
import numpy as np
import datetime
from src.database.db_connection import get_connection
from sklearn.linear_model import LinearRegression

def get_actual_revenue_data() -> pd.DataFrame:
    """Fetch aggregated actual monthly revenue per cinema."""
    conn = get_connection()
    query = """
        SELECT sc.cinema_id, 
               strftime('%Y', b.booking_time) as year,
               strftime('%m', b.booking_time) as month,
               SUM(b.total_cost) as total_revenue
        FROM bookings b
        JOIN showings sh ON b.showing_id = sh.showing_id
        JOIN screens sc ON sh.screen_id = sc.screen_id
        WHERE b.booking_status != 'Cancelled' AND b.booking_time IS NOT NULL
        GROUP BY sc.cinema_id, year, month
    """
    rows = conn.execute(query).fetchall()
    
    data = []
    for r in rows:
        if r["year"] and r["month"]:
            data.append({
                "cinema_id": r["cinema_id"],
                "year": int(r["year"]),
                "month": int(r["month"]),
                "total_revenue": float(r["total_revenue"])
            })
    return pd.DataFrame(data)

def generate_synthetic_history(cinema_id: int, num_months: int = 6) -> pd.DataFrame:
    """Generate synthetic historical data if we lack 6 months of actuals."""
    np.random.seed(42 + cinema_id)
    today = datetime.date.today()
    
    data = []
    for i in range(num_months):
        target_date = today - datetime.timedelta(days=30 * (num_months - i))
        y, m = target_date.year, target_date.month
        
        # Seasonality: Dec/Jan (12, 1) high, Feb/Mar (2, 3) low
        base_rev = np.random.uniform(5000, 15000)
        if m in [12, 1]:
            base_rev *= 1.5
        elif m in [2, 3]:
            base_rev *= 0.7
            
        data.append({
            "cinema_id": cinema_id,
            "year": y,
            "month": m,
            "total_revenue": round(base_rev, 2)
        })
    return pd.DataFrame(data)

def forecast_revenue(cinema_id: int) -> tuple[pd.DataFrame, list[tuple[str, float]]]:
    """
    Returns:
    - actuals_df: DataFrame of last 6 months (actual or synthetic)
    - predictions: List of (month_label, predicted_revenue) for next 3 months
    
    Implementation: Option A (scikit-learn LinearRegression)
    Predicts next 3 months using linear regression on a time index.
    """
    df = get_actual_revenue_data()
    
    if not df.empty:
        df = df[df["cinema_id"] == cinema_id]
        
    if len(df) < 6:
        syn_df = generate_synthetic_history(cinema_id, 6 - len(df))
        if df.empty:
            df = syn_df
        else:
            df = pd.concat([syn_df, df], ignore_index=True)
            
    # Sort chronologically and take last 6
    df = df.sort_values(by=["year", "month"]).tail(6).copy()
    
    # Create time index
    df["time_idx"] = np.arange(len(df))
    
    X = df[["time_idx"]]
    y = df["total_revenue"]
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_year = int(df["year"].iloc[-1])
    last_month = int(df["month"].iloc[-1])
    last_idx = int(df["time_idx"].iloc[-1])
    
    predictions = []
    for i in range(1, 4):
        pred_idx = last_idx + i
        pred_rev = max(0, model.predict([[pred_idx]])[0]) 
        
        nm = last_month + i
        ny = last_year
        if nm > 12:
            nm -= 12
            ny += 1
            
        label = datetime.date(ny, nm, 1).strftime("%b %Y")
        predictions.append((label, round(float(pred_rev), 2)))
        
    # Format actuals df labels
    df["label"] = df.apply(lambda r: datetime.date(int(r["year"]), int(r["month"]), 1).strftime("%b %Y"), axis=1)
    
    return df, predictions
