# Salarios 3DG (2022)

## Intro

Dos simples scripts para calcular y mostrar la media de salarios (en bruto) a partir de los datos vertidos por usuarios anónimos en un thread del foro de 3DGames:

[2022 - ¿Cuánto ganás/cobrás?](https://foros.3dgames.com.ar/threads/1059022-2022-cuanto-ganas-cobras/page1)

La idea nace de mera curiosidad de querer saber cuál era promedio de salarios, notando los elevados montos que los usuarios subían al thread. Estos salarios no parecían demasiado representativos en un principio, teniendo en mente los datos públicos que uno puede ver de encuestas como las de [SysArmy](https://sueldos.openqube.io/encuesta-sueldos-2022.01/), [Encuestas IT](https://www.encuestasit.com/sueldo-desarrollador-de-software-programador-argentina-1), [cuantoGano](https://www.cuantogano.com/sueldos/it-programacion.html) o incluso datos de [CESSI](https://www.cessi.org.ar/ver-noticias-cessi-la-evolucion-de-los-salarios-en-la-industria-it-2755).

## Descripción

El 1° script ([obtener_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/obtener_salarios.py)) se encarga de buscar todos los posts del mencionado thread. Después se filtra los mismos según determinados parámetros (empleado para esta tarea tanto regex como la librería [spaCy](https://spacy.io/)) y así obtener todos los salarios brutos que fueron recolectados de todos los posts (o más específicamente, de aquellos posts siguieron un formato de mensaje establecido en el 1° mensaje del thread):

![Imagen 1](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-1.png)

El 2° script ([plotear_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/plotear_salarios.py)) se encargar de mostrar en un gráfico los resultados obtenidos, empleado la librería [Seaborn](https://seaborn.pydata.org/). Pero antes de hacer esto se obtiene primero el valor del dolar blue del día desde la API de [CriptoYa.com](https://criptoya.com/ar) y del euro blue desde la web de [PrecioEuroBlue.com.ar](https://www.precioeuroblue.com.ar/).
Ya con estos valores a disposición se puede realizar la conversión a pesos y obtener los valores medios necesarios:

![Imagen 2](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-2.png)

Para así mostrar finalmente el plot con todos los salarios en bruto convertidos a pesos y una linea de salario medio:

![Imagen 3](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-3.png)

## Instalación y uso

1) Si se tiene ya instalado [Git](https://git-scm.com/downloads) en nuestro sistema operativo, basta nomás con clonar el presente repositorio:
```bash
git clone git@github.com:FedeHC/salarios3dg.git
```

<br>
Con el repo clonado y dentro de la carpeta de descarga del repositorio, procedemos con el resto:
<br>

2) a) OPCIONAL: Antes es recomendable usar un entorno virtual como por ej. [VirtualEnv](https://github.com/pypa/virtualenv):

```bash
virtualenv salarios3DG
```

2) b) Y recién luego instalar dentro de éste último todas las librerías usadas por ambos scripts:

```bash
pip install -r requirements.txt
```

2) c) OPCIONAL: Tener presente que la librería [spaCy](https://spacy.io/usage#quickstart) puede darnos algunos inconvenientes para instalarlo y usarlo. En ocasiones es necesario descargar un módulo (pipeline de entrenamiento) necesario para poder usar la librería:

```bash
python -m spacy download es_core_news_sm
```
Y dentro del script ([obtener_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/obtener_salarios.py#L96)) ir a la linea 96, comentarla (#) y descomentar la linea siguiente, tal como se muestra a continuación:

```python
# nlp = en_core_web_sm.load()
nlp = spacy.load("es_core_news_sm")
```
<br>

3) a) Una vez terminado, basta nomás con ejecutar ambos scripts en el sig. orden:

```bash
python obtener_salarios.py
```

3) b) Y luego:

```bash
python plotear_salarios.py
```
