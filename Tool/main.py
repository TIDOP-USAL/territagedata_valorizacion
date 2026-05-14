import time
import json
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import os
from config import API_KEY, UPDATE_NEW_REVIEWS
from GooglePlace import GooglePlace
from GoogleReview import GoogleReview
from MediaIncremental import MediaIncremental


def review_mapper(json_review):
    return GoogleReview(
        id=json_review['review_id'],
        text=json_review['snippet'] if 'snippet' in json_review else "",
        date=datetime.strptime(json_review['iso_date_of_last_edit'], "%Y-%m-%dT%H:%M:%SZ"),
        rating=json_review['rating']
    )
def calculate(self):

    place_id = self.ui.SelectPlace.currentData()

    final_score = run_full_analysis(
        place_id,
        API_KEY,
        UPDATE_NEW_REVIEWS
    )

    # Actualizar label
    self.ui.FinalScore.setText(f"Final score: {round(final_score,2)}")

def create_reviews_file_if_not_exists(file_name):
    try:
        with open(file_name, "x") as archivo:
            data = {}
            json.dump(data, archivo)
    except FileExistsError:
        print("El archivo ya existe.")


def remote_reviews_mock():
    data = None
    with open('piedra-caracol.json', 'r', encoding='utf-8') as archivo:
        data = json.load(archivo)

    return data


def http_request(url):
    response = requests.get(url)
    data = {}

    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Error en la petición: {response.status_code}")

    return data


# Retorna toda la información de la primera consulta
def get_last_remote_reviews(place_id, api_key):
    url = (f"https://serpapi.com/search?engine=google_maps_reviews"
           f"&place_id={place_id}"
           f"&sort_by=newestFirst"
           f"&api_key={api_key}")

    return http_request(url=url)


# Retorna la información con todas las reviews
def get_all_remote_reviews(place_id, api_key):
    data = get_last_remote_reviews(place_id=place_id, api_key=api_key)
    all_reviews = data['reviews']

    has_more_pages = 'serpapi_pagination' in data
    print(data)
    while has_more_pages:
        next_url = data['serpapi_pagination']['next'] + f'&api_key={api_key}'
        data = http_request(url=next_url)
        all_reviews += data['reviews']
        has_more_pages = 'serpapi_pagination' in data
        time.sleep(2) 
        print(next_url)
        print(f"Más páginas: {has_more_pages}")

    print("Todas las reseñas recopiladas")

    data['reviews'] = all_reviews

    return data


def get_unseen_remote_reviews(place_id, api_key, saved_reviews):
    new_or_updated_reviews = []
    data = get_last_remote_reviews(place_id, api_key) # Traemos la primera página
    
    last_review_reached = False
    
    while not last_review_reached:
        if "reviews" in data:
            found_something_in_this_page = False
            
            for review in data['reviews']:
                rid = review['review_id']
                remote_edit_date = review.get('iso_date_of_last_edit')
                
                # CASO A: La reseña no existe en nuestro JSON
                if rid not in saved_reviews:
                    new_or_updated_reviews.append(review)
                    found_something_in_this_page = True
                
                # CASO B: La reseña EXISTE pero la FECHA DE EDICIÓN es distinta
                elif remote_edit_date != saved_reviews[rid].get('iso_date_of_last_edit'):
                    print(f"Detectada edición en reseña de: {review['user']['name']}")
                    new_or_updated_reviews.append(review)
                    found_something_in_this_page = True
            
            # Si en toda esta página no hemos encontrado ni una sola reseña nueva 
            # ni una editada, asumimos que ya llegamos al "bloque" de datos antiguos.
            if not found_something_in_this_page:
                print("Llegamos a reseñas ya conocidas y sin cambios. Deteniendo búsqueda.")
                last_review_reached = True
                break
        
        # Paginación: si hay más páginas y no hemos decidido parar, seguimos
        if 'serpapi_pagination' in data and not last_review_reached:
            next_url = data['serpapi_pagination']['next'] + f'&api_key={api_key}'
            data = http_request(url=next_url)
            time.sleep(1) # Un pequeño respiro para la API
        else:
            last_review_reached = True

    print(f'Total procesadas: {len(new_or_updated_reviews)} (nuevas o editadas)')
    return new_or_updated_reviews

def generate_graph(x_data, y_data, type="plot", title="", label_x="Eje x", label_y="Eje y"):

    if type == "plot":
        plt.plot(x_data, y_data)
    elif type == "bar":
        plt.bar(x_data, y_data)
    elif type == "scatter":
        plt.scatter(x_data, y_data)

    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.title(title)
    
    plt.show()


def twin_graph():
    # Datos de ejemplo
    x = [1, 2, 3, 4, 5]
    y1 = [2, 3, 5, 7, 11]  # Primera serie
    y2 = [100, 200, 300, 400, 500]  # Segunda serie con un rango diferente

    # Creamos la figura y el eje principal
    fig, ax1 = plt.subplots()

    # Graficamos la primera serie (en el eje Y principal)
    ax1.plot(x, y1, 'b-', label='Serie 1')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Serie 1', color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    # Creamos un segundo eje Y que comparte el eje X
    ax2 = ax1.twinx()

    # Graficamos la segunda serie (en el eje Y secundario)
    ax2.plot(x, y2, 'r-', label='Serie 2')
    ax2.set_ylabel('Serie 2', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # Mostramos el gráfico
    plt.title('Gráfico con ejes Y separados')
    plt.show()


def generate_dual_graph(
        x_data,
        y_rating,
        y_votes,
        title="Rating evolution",
        label_x="Date",
        label_y_rating="Average rating",
        label_y_votes="Votes",
        output_path = None
):
    # Datos de ejemplo
    x = x_data
    y1 = y_rating
    y2 = y_votes

    # Creamos la figura y el eje principal
    fig, ax1 = plt.subplots()

    # Graficamos la primera serie (en el eje Y principal)
    ax1.plot(x, y1, 'b-', label=label_y_rating)
    ax1.set_xlabel(label_x)
    ax1.set_ylabel(label_y_rating, color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    plt.ylim(0,5)
    # Creamos un segundo eje Y que comparte el eje X
    ax2 = ax1.twinx()

    # Graficamos la segunda serie (en el eje Y secundario)
    ax2.plot(x, y2, 'r-', label=label_y_votes)
    ax2.set_ylabel(label_y_votes, color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # Mostramos el gráfico
    plt.title(title)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    plt.show()





########################################################################################################################
## START (VERSIÓN ADAPTADA PARA GUI)

CASTRO_DE_ULACA_ID = "ChIJcS-5dAGIQA0RPgY7UG5Eipk"
IGLESIA_DE_LA_INVENCION_DE_LA_SANTA_CRUZ_CARDENHOSA_ID = "ChIJxUqT_3mTQA0RyOKWq2ovvow"
IGLESIA_DE_LA_TRANSFIGURACION_DEL_SENHOR_VADILLO_ID = "ChIJP84HwB58Pw0ReoAlOp3JCWE"
IGLESIA_DE_LA_NATIVIDAD_DE_NUESTRA_SENHORA_CAMPILLO_ID = "ChIJp3RRnAx5Pw0RleErOMp92dQ"
VERRACO_CAMPILLO_ID = "ChIJKRMT7yB5Pw0RqBrcI3kHqZw"
ERMITA_SAN_MIGUEL_LA_HIJA_DE_DIOS_ID = "ChIJf7I-7FOHQA0RST0KQ_8Im-4"
IGLESIA_DE_SAN_PEDRO_APOSTOL_BERNUY_ID = "ChIJV0IySFbwQA0RyijSXAmyWSg"
IGLESIA_DE_NUESTRA_SRA_DEL_ROSARIO_VIZOLOZANO_ID = "ChIJVzAsFpPxQA0R4eMfyZUX9U8"
LOS_HENRENES_CILLAN_ID = "ChIJc7DzjsCcQA0R6QH0LJw2sac"
CASTILLO_DE_VILLAVICIOSA_SOLOSANCHO_ID = "ChIJZTCZYOGHQA0RNIncwFV8iT4"
NECROPOLIS_DE_OCO_ID = "ChIJO5G_YQ6EQA0RP7EuQ_1G7Jc"
LAS_TRES_CRUCES_CARDENHOSA_ID = "ChIJU2zOfdeSQA0RLRbse-zZeSk"
ERMITA_DE_SAN_SEGUNDO_AVILA_ID = "ChIJAQAAAKzzQA0RPq8mNYIhaXc"
CASTILLO_DE_MANQUEOSPESE_ID = "ChIJm0DkcwCJQA0RhRu8c4SVPzU"
ARCO_DE_CONEJEROS_ID = "ChIJUQrD1iftQA0RRZlic4DnSd4"
NECROPOLIS_DE_LA_COBA_ID = "ChIJQ2-2hHGCQA0RM7DZ_hPXu7w"
DOLMEN_DEL_PRADO_DE_LAS_CRUCES_ID = "ChIJVZ3X2FLwQA0RC1wVMQ97Y28"
ERMITA_NUESTRA_SENHORA_DE_LAS_FUENTES_ID = "ChIJZ_yGhxSCQA0RFS1OEb__Svk"
MONASTERIO_DE_NUESTRA_SENHORA_DEL_RISCO_ID = "ChIJ5ZUiBmV-Pw0RQYEJgUOAkZw"
LAS_PIEDRAS_DE_GAROZA_ID = "ChIJqW5MpAaGQA0RBSwSPT89XNs"
CASTRO_DE_LA_MESA_DE_MIRANDA_ID = "ChIJH5gWDRCbQA0RZKrNZ4iJXxY"
CASTRO_DE_LAS_COGOTAS_ID = "ChIJI5_BSBHtQA0REe8o41jZ4vk"
PARQUE_DE_EL_SOTO_AVILA_ID = "ChIJHTGfgRXzQA0RqcfyLknTZfc"
SANTUARIO_DE_NUESTRA_SENHORA_DE_SONSOLES_ID = "ChIJPZP6lRnzQA0RmVBjkfPr2Yo"


place_names = {
    CASTRO_DE_ULACA_ID : "CASTRO-ULACA",
    IGLESIA_DE_LA_INVENCION_DE_LA_SANTA_CRUZ_CARDENHOSA_ID : "IGLESIA_DE_LA_INVENCION_DE_LA_SANTA_CRUZ_CARDENHOSA",
    IGLESIA_DE_LA_TRANSFIGURACION_DEL_SENHOR_VADILLO_ID : "IGLESIA_DE_LA_TRANSFIGURACION_DEL_SENHOR_VADILLO",
    IGLESIA_DE_LA_NATIVIDAD_DE_NUESTRA_SENHORA_CAMPILLO_ID : "IGLESIA_DE_LA_NATIVIDAD_DE_NUESTRA_SENHORA_CAMPILLO",
    VERRACO_CAMPILLO_ID : "VERRACO_CAMPILLO",
    ERMITA_SAN_MIGUEL_LA_HIJA_DE_DIOS_ID : "ERMITA_SAN_MIGUEL_LA_HIJA_DE_DIOS",
    IGLESIA_DE_SAN_PEDRO_APOSTOL_BERNUY_ID : "IGLESIA_DE_SAN_PEDRO_APOSTOL_BERNUY",
    LOS_HENRENES_CILLAN_ID : "LOS_HENRENES_CILLAN",
    IGLESIA_DE_NUESTRA_SRA_DEL_ROSARIO_VIZOLOZANO_ID : "IGLESIA_DE_NUESTRA_SRA_DEL_ROSARIO_VIZOLOZANO",
    CASTILLO_DE_VILLAVICIOSA_SOLOSANCHO_ID : "CASTILLO_DE_VILLAVICIOSA_SOLOSANCHO",
    NECROPOLIS_DE_OCO_ID : "NECROPOLIS_DE_OCO",
    LAS_TRES_CRUCES_CARDENHOSA_ID : "LAS_TRES_CRUCES_CARDENHOSA",
    ERMITA_DE_SAN_SEGUNDO_AVILA_ID : "ERMITA_DE_SAN_SEGUNDO_AVILA",
    CASTILLO_DE_MANQUEOSPESE_ID : "CASTILLO_DE_MANQUEOSPESE",
    ARCO_DE_CONEJEROS_ID : "ARCO_DE_CONEJEROS",
    NECROPOLIS_DE_LA_COBA_ID : "NECROPOLIS_DE_LA_COBA",
    DOLMEN_DEL_PRADO_DE_LAS_CRUCES_ID : "DOLMEN_DEL_PRADO_DE_LAS_CRUCES",
    ERMITA_NUESTRA_SENHORA_DE_LAS_FUENTES_ID : "ERMITA_NUESTRA_SENHORA_DE_LAS_FUENTES",
    MONASTERIO_DE_NUESTRA_SENHORA_DEL_RISCO_ID : "MONASTERIO_DE_NUESTRA_SENHORA_DEL_RISCO",
    LAS_PIEDRAS_DE_GAROZA_ID : "LAS_PIEDRAS_DE_GAROZA",
    CASTRO_DE_LA_MESA_DE_MIRANDA_ID : "CASTRO_DE_LA_MESA_DE_MIRANDA",
    CASTRO_DE_LAS_COGOTAS_ID : "CASTRO_DE_LAS_COGOTAS",
    PARQUE_DE_EL_SOTO_AVILA_ID : "PARQUE_DE_EL_SOTO_AVILA",
    SANTUARIO_DE_NUESTRA_SENHORA_DE_SONSOLES_ID : "SANTUARIO_DE_NUESTRA_SENHORA_DE_SONSOLES"
}
def run_full_analysis(
    place_id,
    api_key,
    update_new_reviews=True,
    progress_callback=None,
    output_path=""
):
    if not output_path:
        output_path = os.getcwd()    
    
    if not os.path.exists('files'):
        os.makedirs('files')

    reviews_file_name = f'files/reviews-{place_names[place_id]}.json'
    place = GooglePlace()
    local_reviews = {}

    create_reviews_file_if_not_exists(reviews_file_name)

    # 1. Cargar datos locales (tu JSON actual)
    with open(reviews_file_name, 'r', encoding='utf-8') as archivo:
        local_reviews = json.load(archivo)

    print(f"Verificando {place_names[place_id]}...")
    
    # 2. Sincronización inteligente de reseñas (Nuevas y Editadas)
    if update_new_reviews:
        print(f"Buscando actualizaciones (nuevas o editadas) para {place_names[place_id]}...")
        
        # Llamamos a la función que compara fechas e IDs página por página
        nuevas_o_editadas = get_unseen_remote_reviews(
            place_id=place_id, 
            api_key=api_key, 
            saved_reviews=local_reviews
        )
        
        if nuevas_o_editadas:
            for item in nuevas_o_editadas:
                # Al usar el ID como llave, si ya existe (editada), se SOBRESESCRIBE.
                # Si no existe (nueva), se AGREGA.
                local_reviews[item['review_id']] = item
            
            # Guardamos los cambios en el JSON
            with open(reviews_file_name, 'w', encoding='utf-8') as archivo_escritura:
                json.dump(local_reviews, archivo_escritura, ensure_ascii=False, indent=4)
            print(f"JSON actualizado con {len(nuevas_o_editadas)} cambios.")
        else:
            print("Todo está al día. No se detectaron cambios recientes.")

    # 3. Cargar TODO (viejas + nuevas/editadas) en el objeto place
    for review_key in local_reviews:
        review_item = local_reviews[review_key]
        review = review_mapper(review_item)
        place.reviews.append(review)

    # 4. Cálculos para las gráficas
    ordered_reviews = place.get_ordered_reviews_by_date()
    
    media_incremental = MediaIncremental()
    x_data, mean_y_data, num_votes_array = [], [], []
    num_votes = 0
    total_to_process = len(ordered_reviews)

    for i, review in enumerate(ordered_reviews):
        num_votes += 1
        num_votes_array.append(num_votes)
        media = media_incremental.agregar(review.rating)
        x_data.append(review.date)
        mean_y_data.append(media)

        if progress_callback:
            percent = int((i + 1) / total_to_process * 100)
            progress_callback(percent)

    final_score = mean_y_data[-1] if mean_y_data else 0
    
    return {
        "final_score": final_score,
        "x_data": x_data,
        "y_rating": mean_y_data,
        "y_votes": num_votes_array,
        "total_reviews": len(place.reviews)
    }