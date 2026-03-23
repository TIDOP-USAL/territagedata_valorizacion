import json
import os
import numpy as np
import matplotlib.pyplot as plt
from GooglePlace import GooglePlace
from GoogleReview import GoogleReview
from ReviewMapper import ReviewMapper
from pathlib import Path
from MediaIncremental import MediaIncremental
from scipy import stats
from enum import Enum
from io import BytesIO
from main import place_names



class PaletaColor(Enum):
    DATOS = "#4A90E2"
    TREND = "#A0A0A0"

def generate_rating_graph(x_data, y_data, intercept, slope):

    plt.figure(figsize=(10,6))
    plt.ylim(0,5)

    plt.plot(
        x_data,
        y_data,
        color=PaletaColor.DATOS.value,
        linewidth=2
    )

    trend_line = intercept + slope * x_data

    plt.plot(
        x_data,
        trend_line,
        color=PaletaColor.TREND.value,
        linewidth=2,
        linestyle="--"
    )

    img_stream = BytesIO()
    plt.savefig(img_stream, format="png", dpi=300, bbox_inches="tight")
    plt.close()

    img_stream.seek(0)

    return img_stream
def generate_rating_date_evolution_graph(x_data, y_data):

    plt.figure(figsize=(10,6))
    plt.ylim(0,5)

    plt.scatter(
        x_data,
        y_data,
        color=PaletaColor.DATOS.value,
        s=40
    )

    img_stream = BytesIO()
    plt.savefig(img_stream, format="png", dpi=300, bbox_inches="tight")
    plt.close()

    img_stream.seek(0)

    return img_stream
#######################################################################################################

reviews_folder = "./files"
graphs_folder = "./raw_trend_graphs"
means_graphs_folder = "./means_trend_graphs"
means_evolution_folder = "./means_evolution"
rating_date_evolution_folder = "./rating_date_evolution"
means_date_evolution_folder = "./means_date_evolution"
raw_graphs_folder = "./raw_trend_graphs"
results_path = "./results/trend_results.json"

def generate_trend_graphs(place_id, output_folder):

        place_name = place_names[place_id]
        json_file = f"./files/reviews-{place_name}.json"

        with open(json_file, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        media_incremental = MediaIncremental()
        place = GooglePlace()

        for review in datos.values():
            google_review = ReviewMapper().to_google_review(review)
            place.reviews.append(google_review)

        ratings = []
        dates = []
        means_list = []

        for review in place.get_ordered_reviews_by_date():
            mean = media_incremental.agregar(review.rating)
            means_list.append(mean)
            ratings.append(review.rating)
            dates.append(review.date)

        limits = [10, 20, 30, len(ratings)]

        raw_images = []
        mean_images = []
        date_images = []

        for limit in limits:

            real_limit = min(limit, len(ratings))

            x = np.arange(real_limit)
            y_raw = np.array(ratings[-real_limit:])
            y_means = np.array(means_list[-real_limit:])
            date_subset = dates[-real_limit:]

            res_raw = stats.linregress(x, y_raw)
            res_means = stats.linregress(x, y_means)

            raw_images.append(
                generate_rating_graph(x, y_raw, res_raw.intercept, res_raw.slope)
            )

            mean_images.append(
                generate_rating_graph(x, y_means, res_means.intercept, res_means.slope)
            )

            date_images.append(
                generate_rating_date_evolution_graph(date_subset, y_raw)
            )

        return raw_images, mean_images, date_images

