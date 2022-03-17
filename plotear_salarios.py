# -------------------------------------------------------------------------------------------------
# Librerías
# -------------------------------------------------------------------------------------------------
# Biblioteca estándar
from pathlib import Path
import requests
import time
import tkinter

# De terceros:
import matplotlib
matplotlib.use("tkagg")         # Para evitar mensaje de error (por no estar 'tkinter').
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import regex as re

# -------------------------------------------------------------------------------------------------
# Constantes
# -------------------------------------------------------------------------------------------------
FOLDER_PATH = "data"
JSON_RESULTS_FILE = Path(f"{FOLDER_PATH}/resultados.json")

CRYPTO_YA_URL = "https://criptoya.com/api/dolar"
TIMEOUT = 0.5
PRECIOEUROBLUE_URL = "https://www.precioeuroblue.com.ar/"
EURO_REGEX_PATTERN = "(?<=<span class=\"label reference\">)\d+.\d+"
TYPE = "type"
GROSS = "BRUTO"
NET = "NETO"
CHOOSED_SALARIES_TYPE = GROSS
TITLE = "[3DG] 2022 - ¿Cuánto ganás/cobrás?"

# -------------------------------------------------------------------------------------------------
# Funciones
# -------------------------------------------------------------------------------------------------
def get_time():
    '''Sencilla función que retorna un float con tiempo actual.'''
    return time.time()


def get_elapsed_time_from(initial_time, final_time):
    '''Sencilla función que recibe un tiempo inicial y final como argumentos y devuelve un float con la diferencia de tiempo en segundos.'''
    return round(final_time - initial_time, 2)


def request_dolar_blue(url):
    '''Función que obtiene valor de venta del dolar blue desde api de CriptoYa.com'''
    dolar_blue = None
    # Obtener dolar blue usando API de CryptoYa.com:
    response_dolar = requests.get(url, timeout=TIMEOUT).json()
    if response_dolar:
        dolar_blue = float(response_dolar["blue"])
        print(f"\n- Dolar blue: {dolar_blue}")

    return dolar_blue


def request_euro_blue(url, regex_pattern):
    '''Función que obtiene valor de venta del euro blue desde html de precioeuroblue.com.ar'''
    euro_blue = None
    # Obtener euro blue bajando html de www.precioeuroblue.com.ar:
    response_euro = requests.get(url, timeout=TIMEOUT).text
    if response_euro:
        # Usar regex para obtener valor del html descargado:
        euro_values = re.findall(regex_pattern, response_euro)
        if euro_values: # 2 valores: el 1°es euro blue de compra, el 2° valor el de venta.
            euro_blue = float(euro_values[1])       # Obtenemos el 2° valor, el de venta.
            print(f"- Euro blue: {euro_blue}\n")

    return euro_blue


def make_and_return_dataframe(file):
    '''Función que crea y retorna un objeto dataframe (pandas)'''
    # Leer Json y convertir a Panda Dataframe:
    df = pd.read_json(file)

    return df


def change_to_pesos(df, amount_counter, dolar_blue, euro_blue):
    '''Función que recorre un objeto dataframe y reemplaza ciertos valores de monedas extrajeras por moneda local. Devuelve el dataframe modificado y un contador de campos con valores de montos.'''
    # Convirtiendo dolares y euros a pesos:
    for x in range(len(df)) :
        if df.iloc[x, 7] > 0:
            amount_counter += 1
        if df.iloc[x, 6] == "USD":
            df.iloc[x, 7] *= dolar_blue
        elif df.iloc[x, 6] == "EUR":
            df.iloc[x, 7] *= euro_blue

    return df, amount_counter


def filter_salaries(df):
    '''Función que retoma un nuevo dataframe a partir del filtro sobre el dataframe recibido por argumento.'''
    return df[df[TYPE] == CHOOSED_SALARIES_TYPE]


def get_mean_from_dataframe(df, dolar_blue):
    '''Función que obtiene valor medio de cierto campo de un dataframe. Devuelve un valor medio en pesos y un valor medio en dolares'''
    # Obtener medias de salarios, en pesos y dólares:
    mean_pesos = int(np.mean(df.amount))
    mean_dolares = int(mean_pesos / dolar_blue)

    return mean_pesos, mean_dolares


def show_scatterplot(df, total_posts, amount_counter, mean_pesos):
    '''Función que plotea un gráfico con libería seaborn a partir de dataframe y demás datos pasados por argumento.'''
    # Plotear con Seaborn:
    sns.set_theme(style="darkgrid", palette="rocket")
    g = sns.scatterplot(data=df,
                        x="post_number",
                        y="amount",
                        hue="type",
                        s=100,
                        palette="deep",
                        marker="o")

    # Título y labels:
    g.set_title(TITLE)
    g.set_xlabel(f"Users ({total_posts} salarios detectados en {CHOOSED_SALARIES_TYPE.lower()})")
    g.set_ylabel("Sueldos en pesos ($)")

    # Linea de salario medio (matplotlib):
    plt.axhline(y=mean_pesos,
                color='red',
                linestyle='dashed',
                label="media", )

    # Leyenda :
    plt.text(172.0,
             mean_pesos,
             f"Media (${int(mean_pesos)})",
             horizontalalignment='left',
             size='small',
             color='red') #, weight='semibold')

    # El argumento style='plain' evita que se convierta los salarios a notación científica:
    plt.ticklabel_format(style='plain', axis='y')


    # plt.figure(num=TITLE) # Intentando poner título en ventana de matplotlib/seaborn.
    plt.show()


def main():

    # Variables:
    print("\n# Iniciando script.")
    amount_counter = 0
    total_posts = 0

    # Tareas:
    dolar_blue = request_dolar_blue(CRYPTO_YA_URL)
    euro_blue = request_euro_blue(PRECIOEUROBLUE_URL, EURO_REGEX_PATTERN)
    df = make_and_return_dataframe(JSON_RESULTS_FILE)
    total_posts = len(df)
    df, amount_counter = change_to_pesos(df, amount_counter, dolar_blue, euro_blue)
    df = filter_salaries(df)
    mean_pesos, mean_dolares = get_mean_from_dataframe(df, dolar_blue)

    '''
    time_list = [time_0, time_1, time_2, time_3, time_4, time_5, time_6]
    for pos, t in enumerate(time_list, 1):
        if pos < len(time_list)-1:
            print(f"- Tiempo {pos}: {get_elapsed_time_from(t, time_list[pos+1])} seg.")
    '''

    # Mostrar datos por terminal antes de mostrar gráfico:
    print(f"- Total de posts en thread: {total_posts}")
    print(f"- Posts con salarios detectados: {amount_counter}")
    print(f"- Valor medio de salarios (en pesos): ${mean_pesos}")
    print(f"- Valor medio de salarios (en dolares blue:) u$s{mean_dolares}\n")

    # Mostrar gráfico:
    show_scatterplot(df, len(df), amount_counter, mean_pesos)


    print("# Fin del script.\n")

# -------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
