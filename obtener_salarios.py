# -------------------------------------------------------------------------------------------------
# Librerías
# -------------------------------------------------------------------------------------------------
# Biblioteca estándar:
import datetime
import json
import logging
from pathlib import Path
import time
import traceback
from types import NoneType              # Si se usa Spacy con Python >=3.10
import sys

# De terceros:
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter as mdc
import regex as re                      # regex permite realizar multiples lookbehinds.
import requests
import spacy
import en_core_web_sm

# -------------------------------------------------------------------------------------------------
# Constantes
# -------------------------------------------------------------------------------------------------
FOLDER_PATH = "data"
JSON_RESULTS_FILE = Path(f"{FOLDER_PATH}/resultados.json")
JSON_DB_FILE = Path(f"{FOLDER_PATH}/db.json")
LOG_FILE = Path(f"{FOLDER_PATH}/last_activity.log")

# Recordar que debe finalizar seguido del n° de página (Ej: ...cuanto-ganas-cobras/page10)
URL = "https://foros.3dgames.com.ar/threads/1059022-2022-cuanto-ganas-cobras/page"
TIMEOUT = 5

# Nombre de clases a buscar dentro de cada página html retornada desde la url de 3DG:
POST_CLASS = "post_"                # El nombre de class de cada <li> que contienen posts.
BLOCKQUOTE_CLASS = "postcontent"    # El nombre de class de cada <blockquote> que contienen texto.
USERNAME_CLASS = "username"         # El nombre de class de cada <a> que contienen usernames.
NUMBER_POST_CLASS = "postcounter"   # El nombre de class de cada <a> que contienen contador de post.
DATE_POST_CLASS = "date"            # El nombre de class de cada <span> que contiene la fecha del post.
# TIME_POST_CLASS = "time"          # El nombre de class de cada <span> que contiene la hora del post.
QUOTE_CLASS = "bbcode_container"    # El nombre de class de cada <div> que contiene quotes.

# Caracteres especiales:
ORIGINAL_NEWLINE_CHAR = "\n"        # El caracter de salto de linea dentro de posts.
NEW_ENDLINE_CHAR = "|"              # El nuevo caracter de reemplazo (para evitar problemas).

# REGEX:
REGEX_SALARY_PATTERN_1 = "(?<=salario mensual) (?:bruto|neto)?\s?:?\s?[^|]*"
# REGEX_SALARY_PATTERN_2 = "^[|]?[^|]*[|]" # Para probar en posts n° 4 11 108 111 112 138.
REGEX_PROBLEMATIC_CHARS_PATTERN = r"\t|\r|\*"
REGEX_REPLACE_INVALID_PATTERN = "[^\w.,]+"
REGEX_CONVERT_AMOUNT_PATTERNS = [("(?<=\d)[.|,](?=\d{3})", ""),
                                 ("(?<=\d)[.|,](?=\d{1,2})", "."),
                                 ("(MILLONES|MILLÓN|MILLON)", "1000000"),
                                 ("(MILES|MIL|K)", "1000"),
                                 ("(?<=\d)?\s?[a-zA-Z]+", "")]

# NLP (spaCy):
TOKENS_LIMIT = 6                    # Un límite de tokens a analizar por NLP (spaCy).
NUM =  "NUM"
PROPN = "PROPN"
NOUN = "NOUN"
PRON = "PRON"
ADJ = "ADJ"
SYM = "SYM"
PUNCT = "PUNCT"
DET = "DET"
ADP = "ADP"
ADV = "ADV"
AUX = "AUX"
CCONJ = "CCONJ"
NETO = "NETO"
BRUTO = "BRUTO"
MANO = "MANO"
ARS = "ARS"
USD = "USD"
EUR = "EUR"
VALID_CURRENCY_TYPES = [BRUTO, NETO, MANO]
VALID_NET_TYPES = [NETO, MANO]
DISCARDED_TAGS = [PUNCT, DET, ADP, AUX, CCONJ] # Tipos de tokens a saltear en análisis.
VALID_TYPE_CURRENCIES_TAGS = [PROPN, NOUN]
VALID_CURRENCIES_SYMBOLS_TAGS = [SYM]
VALID_AMOUNTS_TAGS = [NUM, PROPN] #, NOUN]
VALID_SUFFIX_SYMBOLS_TAGS = [NOUN, PROPN]
VALID_CURRENCIES_CODES = [ARS, USD, EUR]
VALID_PESOS_CODES = ["AR", "$", "PESO", "PESOS"]
VALID_DOLAR_CODES = ["U$D", "US$", "DOLAR", "DOLARES"]
VALID_EUROS_CODES = ["€", "EU", "EURO", "EUROS"]


# -------------------------------------------------------------------------------------------------
# Variables
# -------------------------------------------------------------------------------------------------
# Método alternativo para cargar pipiline. Pero se necesita descargar 1° el mismo desde:
# https://github.com/explosion/spacy-models/releases?q=+es_core_news_lg&expanded=true
nlp = en_core_web_sm.load()
# nlp = spacy.load("es_core_news_sm")
nlp.enable_pipe("senter")


# Variables globales:
main_counter = 1        # Un simple contador de actividades que se muestran por terminal.
results = []            # Array donde se guardan temp. todos los posts.
number_pages = None     # Contador de total de páginas.

# -------------------------------------------------------------------------------------------------
# Funciones
# -------------------------------------------------------------------------------------------------
def log_and_print(text, **kwargs):
    '''Función que logea y muestra por consola todo texto recibido por argumento.'''
    new_text = text.replace("\n", "").replace("   ", "")
    logging.info(new_text)
    print(text, **kwargs)


def get_html_from_page(page_number):
    '''Función que realiza un request de una url para obtener todo el html de una página del thread de 3DG.'''
    return requests.get(URL + str(page_number), timeout=TIMEOUT).content


def get_page_and_parse_to_bs4(page_number):
    '''Función para realizar request en la URL de 3DG, obtener html y parsear con BS4.'''
    html_page = get_html_from_page(page_number)
    soup = BeautifulSoup(html_page, "html.parser", from_encoding="ISO-8859-1")

    # Obtener todos los <li> donde normalmente está el contenido de cada post.
    # Se obtiene un array de 15 posts por página:
    all_posts = soup.findAll("li", {"id": re.compile(POST_CLASS + ".*")})

    return all_posts


def check_in_3DG_thread_the_last_pages():
    '''Función que chequea json con dato de últimas páginas y también si existen más páginas en 3DG. Guarda dicha cantidad en un archivo json y retorna el valor de la cantidad de páginas encontradas.'''
    # Un diccionario con el formato de datos esperado, pero con valores en cero:
    empty_db_data = {
        "total_pages": 1,
        "total_posts": 0,
        "salaries_posts": 0,
        "last_timestamp": None
    }

    data = read_from_json_file(JSON_DB_FILE, empty_db_data)
    number_pages = get_and_update_last_page(data)

    return number_pages


def get_and_update_last_page(data):
    '''Función que chequea el último número de páginas del thread de 3DG y actualiza este n° realizando requests por si existen nuevas páginas.'''
    global number_pages, main_counter

    # Mostrando mensaje:
    log_and_print(f"\n   {main_counter}) Chequeando la última cantidad de páginas en thread de 3DG... 🔎")
    main_counter += 1

    # Obteniendo el último número de páginas:
    last_number_pages = data["total_pages"]
    if data["last_timestamp"]:
        last_time = time.ctime(data["last_timestamp"])
    else:
        last_time = "---"

    # Obtener todos los posts de la última página:
    log_and_print(f"   - Ultima página: {last_number_pages}")
    log_and_print(f"   - Ultima fecha: {last_time}\n")

    log_and_print(f"   {main_counter}) Chequeando nuevas páginas de 3DG... 🔎")
    main_counter += 1
    last_posts = str(get_page_and_parse_to_bs4(last_number_pages))

    # Se fija contador y flag de control:
    pages_counter = last_number_pages + 1
    not_same_content = True

    # Se realiza ciclo de comprobación de nuevas páginas, si existen:
    while not_same_content:
        next_posts = str(get_page_and_parse_to_bs4(pages_counter))
        if next_posts != last_posts:
            log_and_print(f"   - Página {pages_counter}: ✅")
            last_number_pages = pages_counter
            last_posts = next_posts
            pages_counter += 1
        else:
            log_and_print(f"   - Página {pages_counter}: ❌")
            log_and_print("   - No hay más páginas.")
            break

    return last_number_pages


def parse_bs4_to_markdown(bs4_object):
    '''Función que convierte un texto con contenido html a formato markdown.'''
    return mdc(strip=['<!--']).convert_soup(bs4_object)


def get_specific_user_info(post):
    '''Función que obtiene info específica del user del post: nombre, fecha, nro. post y texto.'''
    username = post.find("a", class_= USERNAME_CLASS)
    number_post = post.find("a", class_= NUMBER_POST_CLASS)
    date_post = post.find("span", class_= DATE_POST_CLASS)
    # time_post = post.find("span", class_= TIME_POST_CLASS)
    post_text = post.find("blockquote", class_= BLOCKQUOTE_CLASS)

    return [username, number_post, date_post, post_text]


def remove_quote(post):
    '''Función para remover quotes dentro de un post de un usuario (si existen).'''
    # Buscar cualquier quote dentro del post y borrarlos (p/evitar info duplicada):
    quote = post.find("div", class_= QUOTE_CLASS) 
    if type(quote) is not NoneType:
        quote.extract()

    return post


def remove_problematic_chars(text):
    '''Función para remover caracteres problemáticos para parsear dentro de un texto.'''
    text = re.sub(REGEX_PROBLEMATIC_CHARS_PATTERN, '', text, flags=re.IGNORECASE)
    text = re.sub(ORIGINAL_NEWLINE_CHAR, NEW_ENDLINE_CHAR, text, flags=re.IGNORECASE)

    return text.strip()


def parse_date_string_to_timestamp(date_string):
    '''Función para parsear un string a timestamp (como entero).'''
    dt = datetime.datetime.strptime(date_string,"%d-%m-%y, %H:%M %p") # Ejemplo date: "10-02-22,03:30 PM"
    ts = int(dt.timestamp())

    return ts


def get_posts_from(page_number):
    '''Funcion que obtiene todos los posts del una página del thread de 3DG y los guarda en un array.'''
    all_posts = get_page_and_parse_to_bs4(page_number)
    page_results = []

    for post in all_posts:
        # Obtener todos los datos:
        username, post_number, date_post, text_post = get_specific_user_info(post)

        # Parsear los datos recibidos a un formato más adecuado:
        username = username.string
        post_number = int(post_number.string[1:])
        ts_post = parse_date_string_to_timestamp(date_post.get_text())

        # Quitar quotes, convertir a markdown y eliminar caracteres innecesarios del post:
        text_post = remove_quote(text_post)
        text_post = parse_bs4_to_markdown(text_post)
        text_post = remove_problematic_chars(text_post)

        # Crear diccionario con todos los datos obtenidos para guardarlos en array:
        page_results.append({"post_number": post_number, 
                             "username":  username.string,
                             "timestamp": ts_post,
                             "post": text_post})

    return page_results


def get_all_post_from(results, number_pages):
    '''Función que llama un n° de veces (recibido por arg.) a otra función para generar arrays de posts de varias páginas. Se devuelve modificado el array recibido por argumento con nuevos posts.'''
    global main_counter

    log_and_print(f"\n   {main_counter}) Descargando las {number_pages} páginas del thread. Esto puede llevar varios segundos... ⏳")
    main_counter += 1

    for page in range(1, number_pages + 1):
        results += get_posts_from(page)
        log_and_print(f"   - Página {page}: ✅")

    return results


def read_from_json_file(file, empty_results=None):
    '''Función que abre un archivo json y retorna su contenido.'''
    global main_counter
    log_and_print(f"\n   {main_counter}) Leyendo datos del archivo '{file}'... 💾")
    main_counter += 1

    results = empty_results
    try:
        with open(file, "r") as open_file:
            results = json.load(open_file)
    except Exception as error:
        error_message(error)
        log_and_print(f"\n   - No importa, solo para ahorrar búsquedas nomás, no pasa nada. 😉")
    finally:
        return results


def save_to_json_file(file, data):
    '''Función que abre un archivo json y guarda un contenido recibido por argumento.'''
    global main_counter
    log_and_print(f"\n   {main_counter}) Guardando datos en archivo '{file}'... 💾")
    main_counter += 1

    try:
        with open(file, "w", encoding="utf8") as file_to_save:
            json.dump(data, file_to_save, indent=4, ensure_ascii=False)
    except Exception as error:
        error_message(error)


def get_value_from_string(post_text):
    '''Función que recibe un string y devuelve un substring que coincida con un patrón buscado.'''
    # Aplicando 1° regex de búsqueda:
    value = re.findall(REGEX_SALARY_PATTERN_1, post_text, re.IGNORECASE)
    '''
    if value and not value[0]:
        value = re.findall(REGEX_SALARY_PATTERN_2, post_text, re.IGNORECASE)
    '''

    if value:
        return value[0].strip().upper()     # Devolver el único valor del array.
    else:
        return ""                           # Devolver string vacio.


def analize_and_get_data_from(full_text):
    '''Función que recibe un string de parámetro y parsea este para devolver 3 valores determinados.'''
    # log_and_print(f"\"{full_text}\"")
    nlp_obj = nlp(full_text)         # Pasando texto objeto NLP (spaCy).

    # Variables que guardarán los datos a obtener:
    type_slry = None
    currency_slry= None
    amount_slry = None
    counter = 1                 # Contador p/delimitar el análisis de palabras.
    # Analizando cada token en el texto (con un contador empezando en 1):
    for token in nlp_obj:
        text = token.text.upper()
        text_tag = token.pos_
        # Saltear etiquetas no útiles para el análisis:
        if text_tag not in DISCARDED_TAGS:
            # log_and_print(f"- {text}   {text_tag} ({counter})")

            if counter == 1:
                # La 1° palabra tiene siempre el tipo de salario (bruto o neto):
                if text in VALID_CURRENCY_TYPES:
                    type_slry = parse_currency_type(text)

                # En algunos pocos casos es el tipo de moneda:
                elif text_tag in VALID_TYPE_CURRENCIES_TAGS and not currency_slry:
                    currency_slry = check_if_currency_class_is_valid(text)

            elif counter == 2:
                if text in VALID_CURRENCY_TYPES and not type_slry:
                    type_slry = parse_currency_type(text)

                # Generalmente la 2° palabra tiene el tipo de moneda:
                elif text_tag in VALID_TYPE_CURRENCIES_TAGS and not currency_slry:
                    currency_slry = check_if_currency_class_is_valid(text)

                # O también puede ser el signo '$':
                elif text_tag in VALID_CURRENCIES_SYMBOLS_TAGS and len(token.lemma_) == 1 and not currency_slry:
                    currency_slry = check_if_currency_class_is_valid(text)

                # En algunos casos contienen el monto en la 2° palabra:
                elif text_tag in VALID_AMOUNTS_TAGS and text[0].isdigit() and not amount_slry:
                    amount_slry = parse_string_to_integer(text)

            else:
                # Si es un 'num' en 3° o 4° palabra, es el monto del salario:
                if text_tag in VALID_AMOUNTS_TAGS and text[0].isdigit() and not amount_slry:
                    amount_slry = parse_string_to_integer(text)

                # A veces también es posible un sufijo si ya hubo un n° antes:
                elif text_tag in VALID_SUFFIX_SYMBOLS_TAGS and amount_slry:
                    suffix = parse_string_to_integer(text)
                    if suffix:
                        amount_slry = amount_slry * suffix

                # Si es un 'proper name", puede ser el tipo de moneda:
                if text_tag in VALID_TYPE_CURRENCIES_TAGS and not currency_slry:
                    currency_slry = check_if_currency_class_is_valid(text)

            # Avanzando contador:
            counter += 1

            # Se pone tope para evitar seguir analizando cuando no tiene sentido:
            if counter >= TOKENS_LIMIT or (type_slry and currency_slry and amount_slry):
                break
    # log_and_print()

    # Si no se detectó tipo de salario pero si los otros 2, asignar "BRUTOS":
    if amount_slry and currency_slry and not type_slry:
        type_slry = BRUTO

    # Si no se detectó tipo de moneda pero si los otros 2, asignar 'ARS':
    if type_slry and amount_slry and not currency_slry:
        currency_slry = ARS

    return type_slry, currency_slry, amount_slry


def parse_currency_type(string):
    '''Función que recibe un string y devuelve otro según condiciones.'''
    if BRUTO in string:
        return BRUTO
    elif string in VALID_NET_TYPES:
        return NETO
    else:
        return string


def check_if_currency_class_is_valid(text):
    '''Función que recibe un string y chequea este si es válido según condiciones. Se devuelve string según éstas.'''
    if text not in VALID_CURRENCIES_CODES:
        if text in VALID_PESOS_CODES:
            text = ARS
        elif text in VALID_DOLAR_CODES:
            text = USD
        elif text in VALID_EUROS_CODES:
            text = EUR
        else:
            text = None

    return text


def parse_string_to_integer(string_number):
    '''Función que parsea un string recibido por arg. a un número entero. Devuelve string o entero u otro según condiciones.'''
    number = None
    if string_number:
        # Si el string no contiene solamente dígitos...
        if not string_number.isdigit():
            # Borrar cualquier caracter que no sea números, puntos. comas o palabras clave:
            string_number = re.sub(REGEX_REPLACE_INVALID_PATTERN, '', string_number, flags=re.IGNORECASE)

            # Reemplazar sufijos o palabras clave (ej: 'miles') con el patrón que corresponda:
            for pattern in REGEX_CONVERT_AMOUNT_PATTERNS:
                string_number = re.sub(pattern[0], pattern[1], string_number, flags=re.IGNORECASE)

        # Parsear string a número entero:
        try:
            if string_number:
                number = float(string_number)
        except ValueError as error:
            log_and_print(f"# Error al convertir el string '{string_number}' a número.")
        finally:
            return number


def get_all_salaries_data_from(results):
    '''Función que recibe un array de dicc. y guarda nuevos valores dentro de cada dicc. Retorna este array modificado, además de un número contador.''' 
    global main_counter
    salaries_posts_counter = 0
    value = None

    log_and_print(f"\n   {main_counter}) Analizando los {len(results)} posts encontrados. Esto también va a tardar unos segundos... ⏳")
    main_counter += 1

    # Recorriendo cada post en array results:
    for position, post in enumerate(results):
        # Obtener array de valores encontrados dentro del string posts['text']:
        selected_text = get_value_from_string(post["post"])

        if selected_text:
            type_slry, currency_slry, amount_slry = analize_and_get_data_from(selected_text)
            salaries_posts_counter += 1

        else:
            # Si no hubo ningún texto seleccionado, poner todo a 'None' y evitar así
            # repetir por accidente datos previos en siguientes posiciones.
            #  Más tarde estos resultados pasarán a 'null' al guardarse en archivo json:
            selected_text = None
            type_slry = None
            currency_slry = None
            amount_slry = None

        # Porcentaje de posts con contenido detectado de salarios:
        percent_posts_salaries = round((salaries_posts_counter * 100) / len(results), 1)

        # Agregar finalmente a cada diccionario dentro del array results:
        results[position]["selected_text"] = selected_text
        results[position]["type"] = type_slry
        results[position]["currency"] = currency_slry
        results[position]["amount"] = amount_slry

    log_and_print(f"   - Se detectaron {salaries_posts_counter} posts con salarios ({percent_posts_salaries}% del total). ")

    return results, salaries_posts_counter


def save_to_db(salaries_counter, file=JSON_DB_FILE):
    '''Función para crear dicc. con datos importantes del script, para guardar en archivo json.'''
    new_data = {
        "total_pages": number_pages,
        "total_posts": len(results),
        "salaries_posts": salaries_counter,
        "last_timestamp": int(get_time())
    }

    save_to_json_file(file, new_data)


def get_time():
    '''Sencilla función que retorna un float con tiempo actual.'''
    return time.time()


def get_elapsed_time_from(initial_time, final_time):
    '''Sencilla función que recibe un tiempo inicial y final como argumentos y devuelve un float con la diferencia de tiempo en segundos.'''
    return round(final_time - initial_time, 2)


def init_message():
    '''Sencilla función que muestra un mensaje de inicio de script.'''
    log_and_print("\n # Iniciando script:")


def end_message():
    '''Sencilla función que muestra un mensaje de fin de script.'''
    log_and_print("\n# Fin del script.\n") 


def success_message(elapsed_time):
    '''Función que muestra mensaje al usuario sobre finalización del script.'''
    log_and_print(f"\n   {main_counter}) Listo el pollo: todos los posts fueron analizados con éxito. 🐔✨")
    log_and_print(f"   - Recordar que los datos recolectados fueron guardados en el archivo '{JSON_RESULTS_FILE}'.")
    log_and_print(f"   - Tardé {elapsed_time} seg. en realizar todas las tareas. ⏳")


def error_message(error):
    '''Función que muestra mensaje de error al surgir alguna excepción durante la ejecución del script.'''
    log_and_print("\n   * Sorry, hubo un error inesperado durante la ejecución del script. 🤬")
    log_and_print(f"   * Ver log para más detalles: {LOG_FILE}.")
    logging.error("", exc_info=True)


def main():
    global results
    global number_pages

    try:
        # Iniciando:
        initial_time = get_time()
        logging.basicConfig(filename=LOG_FILE,
                            filemode="w",
                            format="[%(levelname)s] %(message)s",
                            level=logging.INFO)
        logging.info(f"[{time.ctime(initial_time)}]")
        init_message()

        # Realizando las tareas necesarias:
        number_pages = check_in_3DG_thread_the_last_pages()
        results = get_all_post_from(results, number_pages)
        results, salaries_counter = get_all_salaries_data_from(results)
        save_to_db(salaries_counter)
        save_to_json_file(JSON_RESULTS_FILE, results)

        # Finalizando, con mensaje de éxito:
        final_time = get_time()
        elapsed_time = get_elapsed_time_from(initial_time, final_time)
        success_message(elapsed_time)
        # assert False, "AssertionError creado al final del script a modo de prueba."

    except Exception as error:
        error_message(error)

    finally:
        end_message()

# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
