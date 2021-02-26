from app.helpers import pretty_date
from datetime import datetime, timedelta

def test_now():
    assert pretty_date(datetime.utcnow()) == "just now"
def test_a_minute():
    assert (pretty_date(datetime.utcnow() - timedelta(seconds=100))) == "a minute ago"
def test_minutes():
    assert (pretty_date(datetime.utcnow() - timedelta(seconds=1820))) == "30 minutes ago"
def test_an_hour():
    assert (pretty_date(datetime.utcnow() - timedelta(seconds=4000))) == "an hour ago"
def test_three_hours():
    assert (pretty_date(datetime.utcnow() - timedelta(seconds=10800))) == "3 hours ago"
def test_six_hours():
    assert (pretty_date(datetime.utcnow() - timedelta(seconds=21600))) == "6 hours ago"
def test_yesterday():
    assert (pretty_date(datetime.utcnow() - timedelta(days=1))) == "Yesterday"
def test_days():
    assert (pretty_date(datetime.utcnow() - timedelta(days=2))) == "2 days ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=3))) == "3 days ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=4))) == "4 days ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=5))) == "5 days ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=6))) == "6 days ago"
def test_weeks():
    assert (pretty_date(datetime.utcnow() - timedelta(days=7))) == "1 week ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=14))) == "2 weeks ago"
    assert (pretty_date(datetime.utcnow() - timedelta(days=21))) == "3 weeks ago"
def test_months():
    assert (pretty_date(datetime.utcnow() - timedelta(days=32))) == "1 month ago" 
    assert (pretty_date(datetime.utcnow() - timedelta(days=364))) == "12 months ago" 
def test_years():
    assert (pretty_date(datetime.utcnow() - timedelta(days=365))) == "1 years ago"