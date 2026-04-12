"""
src/utils/seat_recommender.py
=============================
Smart Seat Recommendation engine using greedy algorithm.
"""

from src.database.db_connection import get_connection

def recommend_seats(showing_id: int, ticket_type: str, quantity: int) -> list[str]:
    """
    Recommend the best available seats for a given showing and ticket type.
    
    Uses a greedy algorithm considering:
    - Contiguity (keeping groups together in the same row)
    - Centrality (closer to middle of the row is better)
    - Avoiding 1-seat gaps (penalised)
    """
    conn = get_connection()
    cursor = conn.execute("""
        SELECT sc.lower_hall_seats, sc.upper_gallery_seats, sc.vip_seats
        FROM showings sh
        JOIN screens sc ON sh.screen_id = sc.screen_id
        WHERE sh.showing_id = ?
    """, (showing_id,))
    layout = cursor.fetchone()
    
    if not layout:
        return []

    # Get booked seats
    cursor = conn.execute("""
        SELECT t.seat_number 
        FROM tickets t
        JOIN bookings b ON t.booking_id = b.booking_id
        WHERE b.showing_id = ? AND b.booking_status = 'Active'
    """, (showing_id,))
    booked_seats = set(r["seat_number"] for r in cursor.fetchall())

    # Build full seat map to understand grid (10 seats per row as per GUI)
    all_seats = []
    for i in range(1, layout["lower_hall_seats"] + 1):
        all_seats.append({"zone": "lower_hall", "num": f"A{i}"})
    for i in range(1, layout["upper_gallery_seats"] + 1):
        all_seats.append({"zone": "upper_gallery", "num": f"B{i}"})
    for i in range(1, layout["vip_seats"] + 1):
        all_seats.append({"zone": "vip", "num": f"V{i}"})

    # Assign grid coordinates
    grid = {}
    for idx, s in enumerate(all_seats):
        r = idx // 10
        c = idx % 10
        s["row"] = r
        s["col"] = c
        s["is_free"] = s["num"] not in booked_seats
        grid[s["num"]] = s

    # Filter seats by requested ticket type
    zone_seats = [s for s in all_seats if s["zone"] == ticket_type and s["is_free"]]
    if len(zone_seats) < quantity:
        return [] # Not enough seats

    best_score = -999999
    best_combo = []

    # Generate all possible combinations of size 'quantity' from available zone seats.
    # To be efficient, we will prioritize contiguous blocks in the same row.
    # Let's find all blocks of size 1 to 'quantity' in each row.
    
    # Actually, a greedy search:
    # First, try to find a contiguous block of size `quantity` in a single row.
    # If not possible, allow splitting across rows but heavily penalize.
    
    import itertools
    
    # We will score candidates. To avoid combinations explosion, we just use a heuristic approach:
    # We group available seats by row.
    rows_dict = {}
    for s in zone_seats:
        rows_dict.setdefault(s["row"], []).append(s)
        
    candidates = []
    
    # 1. Contiguous candidates
    for r_idx, seats in rows_dict.items():
        seats = sorted(seats, key=lambda x: x["col"])
        # Find contiguous subsegments
        for i in range(len(seats) - quantity + 1):
            chunk = seats[i:i+quantity]
            # Check if truly contiguous
            if chunk[-1]["col"] - chunk[0]["col"] == quantity - 1:
                candidates.append(chunk)
                
    # 2. Non-contiguous candidates (same row, but with gaps)
    for r_idx, seats in rows_dict.items():
        if len(seats) >= quantity:
            for combo in itertools.combinations(seats, quantity):
                # Don't add if already added as contiguous
                if combo[-1]["col"] - combo[0]["col"] != quantity - 1:
                    candidates.append(list(combo))
                    
    # 3. If no same-row candidates, fallback to multi-row combinations
    if not candidates:
        # Just pick the best rows first
        # Sort all available seats by centrality
        sorted_all = sorted(zone_seats, key=lambda x: abs(x["col"] - 4.5))
        # Simple greedy pick for multi-row
        candidates.append(sorted_all[:quantity])

    # Score candidates
    for cand in candidates:
        score = 0
        
        # 1. Contiguity score
        row_counts = {}
        for s in cand:
            row_counts[s["row"]] = row_counts.get(s["row"], 0) + 1
        
        # Penalty for splitting across rows
        score -= (len(row_counts) - 1) * 1000
        
        # Bonus for contiguous seats
        cols = sorted([s["col"] for s in cand])
        gaps = 0
        for i in range(1, len(cols)):
            gap = cols[i] - cols[i-1] - 1
            if gap > 0:
                gaps += gap
        
        if gaps == 0:
            score += 500  # High bonus for being perfectly contiguous
        else:
            score -= gaps * 50 # Penalty for gaps
            
        # 2. Centrality score (closer to 4.5 is better)
        avg_col = sum(s["col"] for s in cand) / len(cand)
        centrality = abs(avg_col - 4.5)
        score -= centrality * 10 # small penalty for being far from center

        # 3. Isolated seat gap penalty
        # Check if booking this candidate leaves exactly 1 empty seat next to it
        # For each seat in candidate, check left and right
        isolated_penalty = 0
        for s in cand:
            # Check left
            left_col = s["col"] - 1
            if left_col >= 0:
                # Is left seat free but not in candidate?
                left_free = any(cs["row"] == s["row"] and cs["col"] == left_col and cs["is_free"] for cs in all_seats)
                left_in_cand = any(cs["col"] == left_col for cs in cand if cs["row"] == s["row"])
                if left_free and not left_in_cand:
                    # check seat further left
                    far_left_col = left_col - 1
                    if far_left_col < 0 or not any(cs["row"] == s["row"] and cs["col"] == far_left_col and cs["is_free"] for cs in all_seats):
                        isolated_penalty += 100 # Leaves a single isolated empty seat
            
            # Check right
            right_col = s["col"] + 1
            if right_col < 10:
                right_free = any(cs["row"] == s["row"] and cs["col"] == right_col and cs["is_free"] for cs in all_seats)
                right_in_cand = any(cs["col"] == right_col for cs in cand if cs["row"] == s["row"])
                if right_free and not right_in_cand:
                    far_right_col = right_col + 1
                    if far_right_col >= 10 or not any(cs["row"] == s["row"] and cs["col"] == far_right_col and cs["is_free"] for cs in all_seats):
                        isolated_penalty += 100

        score -= isolated_penalty

        if score > best_score:
            best_score = score
            best_combo = cand

    return [s["num"] for s in best_combo]
