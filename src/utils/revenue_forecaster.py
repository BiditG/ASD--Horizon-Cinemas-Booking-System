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
    - display_df: DataFrame of last 6 months (ACTUAL data only for display)
    - predictions: List of (month_label, predicted_revenue) for next 3 months
    
    Implementation: Uses actuals for display but backfills with synthetic 
    internally to allow the LinearRegression model to function for new cinemas.
    """
    df_all = get_actual_revenue_data()
    actuals_df = pd.DataFrame()
    
    if not df_all.empty:
        actuals_df = df_all[df_all["cinema_id"] == cinema_id].copy()
        
    if actuals_df.empty:
        # No actual data at all
        return pd.DataFrame(columns=["cinema_id", "year", "month", "total_revenue", "label"]), []
            
    # For display: last 6 actual months
    display_df = actuals_df.sort_values(by=["year", "month"]).tail(6).copy()
    display_df["label"] = display_df.apply(lambda r: datetime.date(int(r["year"]), int(r["month"]), 1).strftime("%b %Y"), axis=1)

    # For the model: we need multiple points for regression. 
    # We backfill with synthetic data internally if we have < 6 points.
    model_df = actuals_df.sort_values(by=["year", "month"]).copy()
    if len(model_df) < 6:
        # Generate enough to have 6 months total
        syn_count = 6 - len(model_df)
        syn_df = generate_synthetic_history(cinema_id, syn_count)
        model_df = pd.concat([syn_df, model_df], ignore_index=True)
    
    # Take last 6 for the model
    model_df = model_df.sort_values(by=["year", "month"]).tail(6).copy()
    model_df["time_idx"] = np.arange(len(model_df))
    
    X = model_df[["time_idx"]].values
    y = model_df["total_revenue"].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_year = int(model_df["year"].iloc[-1])
    last_month = int(model_df["month"].iloc[-1])
    last_idx = int(model_df["time_idx"].iloc[-1])
    
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
        
    return display_df, predictions
