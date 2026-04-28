import datetime
from src.models.showing import Showing

if __name__ == '__main__':
    try:
        rows = Showing.get_by_cinema_date(1, datetime.date.today().isoformat())
        print('OK showings:', len(rows))
    except Exception as e:
        print('ERROR', e)
        raise
