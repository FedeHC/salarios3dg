# Salarios 3DG (2022)

## Intro

Dos simples scripts para calcular y mostrar la media de salarios (en bruto) a partir de los datos vertidos por usuarios anónimos en un thread del foro de 3DGames:

[2022 - ¿Cuánto ganás/cobrás?](https://foros.3dgames.com.ar/threads/1059022-2022-cuanto-ganas-cobras/page1)

La idea nace de mera curiosidad por querer saber cuál era promedio de salarios, notando los elevados montos que los usuarios subían al thread. Estos salarios no parecían demasiado representativos en un principio, teniendo en mente los datos públicos que uno puede ver de encuestas como las de [SysArmy](https://sueldos.openqube.io/encuesta-sueldos-2022.01/), [Encuestas IT](https://www.encuestasit.com/sueldo-desarrollador-de-software-programador-argentina-1), [cuantoGano](https://www.cuantogano.com/sueldos/it-programacion.html) o incluso datos de [CESSI](https://www.cessi.org.ar/ver-noticias-cessi-la-evolucion-de-los-salarios-en-la-industria-it-2755).

## Descripción

El 1° script ([obtener_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/obtener_salarios.py)) se encarga de buscar todos los posts de dicho thread. Y luego se filtra los mismos según determinados parámetros (empleado tanto Regex como la librería [spaCy](https://spacy.io/) para dicha tarea) y así obtener todos los salarios brutos vertidos en esos posts.

![Imagen 1](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-1.png)

El 2° script ([plotear_salarios.py](https://github.com/FedeHC/salarios3dg/blob/main/plotear_salarios.py)) se encargar de mostrar en un gráfico con los resultados obtenidos, empleado la librería [Seaborn](https://seaborn.pydata.org/). Básicamente se muestra un plot con linea de salario medio.


![Imagen 2](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-2.png)

![Imagen 3](https://raw.githubusercontent.com/FedeHC/salarios3dg/main/images/captura-3.png)

## Instalación y uso

1) Si se tiene ya instalado git en nuestro sistema operativo, basta nomás con clonar el presente repositorio:
```bash
git clone git@github.com:FedeHC/salarios3dg.git
```

2) a) Es recomendable usar un entorno virtual como por ej. [VirtualEnv](https://github.com/pypa/virtualenv):

```bash
virtualenv salarios3DG
```

2) b) E instalar dentro de éste todas las librerías usadas por ambos scripts:

```bash
pip install -r requirements.txt
```

3) a) Una vez terminado, basta nomás con ejecutar ambos scripts en el sig. orden:

```bash
python obtener_salarios.py
```

3) b) Y luego:

```bash
python plotear_salarios.py
```
