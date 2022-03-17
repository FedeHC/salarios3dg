# Salarios 3DG (2022)

## Intro

Dos simples scripts para calcular y mostrar la media de salarios (en bruto) a partir de los datos vertidos del siguiente thread de una sección del foro de 3DGames:

[2022 - ¿Cuánto ganás/cobrás?](https://foros.3dgames.com.ar/threads/1059022-2022-cuanto-ganas-cobras/page1)

La idea nace de mera curiosidad por saber nomás el promedio de salarios al notar los elevados montos que los usuarios venían subiendo, ya que no parecían demasiado representativos (o al menos no como parecía en un principio) si se tiene en mente datos de encuestas como las de [SysArmy](https://sueldos.openqube.io/encuesta-sueldos-2022.01/), [EncuestasIT.com](https://www.encuestasit.com/sueldo-desarrollador-de-software-programador-argentina-1) o [CESSI](https://www.cessi.org.ar/ver-noticias-cessi-la-evolucion-de-los-salarios-en-la-industria-it-2755).

## Detalles:

El 1° script ([obtener_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/obtener_salarios.py)) se encarga de buscar todos los posts de dicho thread. Y luego se filtra los mismos según determinados parámetros (empleado tanto Regex como la librería [spaCy](https://spacy.io/) para dicha tarea) y así obtener todos los salarios brutos vertidos en esos posts.

![Imagen 1](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-1.png)

El 2° script ([plotear_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/plotear_salarios.py)) se encargar de mostrar en un gráfico con los resultados obtenidos, empleado la librería [Seaborn](https://seaborn.pydata.org/). Básicamente se muestra un plot con linea de salario medio.


![Imagen 2](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-2.png)

![Imagen 3](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-3.png)

