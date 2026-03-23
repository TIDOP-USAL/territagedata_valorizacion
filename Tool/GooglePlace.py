from datetime import datetime
from GoogleReview import GoogleReview

class GooglePlace:
    def __init__(self, title = "", rating = 0, reviews=None):
        self.title = title
        self.rating = rating
        if reviews is None:
            self.reviews = []

    def add_review(self, review : GoogleReview):
        self.reviews.append(review)

    def get_ordered_reviews_by_date(self) -> list[GoogleReview]:
        #return sorted(self.reviews, key=lambda review: datetime.strptime(review.date, "%Y-%m-%dT%H:%M:%SZ"))
        return sorted(self.reviews, key=lambda review: review.date)
