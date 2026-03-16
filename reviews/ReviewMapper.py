from datetime import datetime
from GoogleReview import GoogleReview

class ReviewMapper:
    def __init__(self):
        pass
        
    def to_google_review(self, json_review):
        return GoogleReview(
        id=json_review['review_id'],
        text=json_review['snippet'] if 'snippet' in json_review else "",
        date=datetime.strptime(json_review['iso_date'], "%Y-%m-%dT%H:%M:%SZ"),
        rating=json_review['rating']
    )