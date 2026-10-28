# Sistema experto de rutinas de entrenamiento

Aplicación en Python (consola y web), con arquitectura POO a tres capas, motor de inferencia bayesiano y base de conocimiento en PostgreSQL.

## Requisitos

- Python 3.10 o superior
- PostgreSQL 16 o superior

## Instalación

```bash
pip install -r requirements.txt
```

Cree en la raíz del proyecto un archivo `config_local.py` con sus datos de conexión:

```python
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "sistema_experto_rutina"
DB_USER = "postgres"
DB_PASSWORD = "SU_CONTRASEÑA"
```

`config_local.py` está en `.gitignore`, así la contraseña no se sube al repositorio. También puede usar las variables de entorno `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`.

## Puesta en marcha

```bash
python inicializar_bd.py   # crea la base, carga el conocimiento y los usuarios de prueba
python main.py             # inicia el sistema (consola)
python servidor_web.py     # o la versión web: http://127.0.0.1:5000
```

`inicializar_bd.py` borra y vuelve a crear las tablas cada vez que se ejecuta.

Si se prefiere pgAdmin, se pueden ejecutar `sql/01_esquema.sql` y `sql/02_carga_conocimiento.sql` en ese orden. En ese caso los usuarios se crean desde la opción **Registrarme**, y los roles se asignan como administrador o con un `UPDATE` a la tabla `usuario`.

En Windows se recomienda usar Windows Terminal o la terminal de VS Code para ver los colores y las tildes correctamente.

## Cuentas de prueba

La contraseña de todas es `demo123`.

| Rol | Correo |
|---|---|
| Administrador | admin@rutinas.com |
| Experto humano | experto@rutinas.com |
| Ingeniero del conocimiento | ingeniero@rutinas.com |
| Usuario final | laura.gomez@example.com (y los demás usuarios de la Tabla 19) |

## Arquitectura

```
presentacion/   Capa de presentación: menús de consola por rol (rich)
negocio/        Capa de lógica de negocio
  entidades.py              Hecho, Pregunta, Hipotesis, ReglaInferencia, BaseHechos...
  motor_inferencia.py       Inferencia bayesiana y selección de preguntas
  servicio_*.py             Casos de uso (diagnóstico, base de conocimiento, usuarios)
  repositorios.py           Interfaces que debe cumplir la capa de datos
datos/          Capa de datos: repositorios sobre PostgreSQL (psycopg)
sql/            Esquema y carga del conocimiento del experto
main.py         Crea los objetos de cada capa y los conecta
```

Cada capa solo conoce a la de abajo. La capa de negocio depende de las interfaces de `repositorios.py` y no de PostgreSQL, así que se puede cambiar la base de conocimiento sin modificar el motor (RNF-04).

## Modelo de la base de conocimiento

```
pregunta 1──N hecho N──M hipotesis
                   \         /
                 hecho_hipotesis ──N:1── regla_inferencia
```

- **hecho**: cada opción de respuesta, del tipo variable = valor. Son 15.
- **hipotesis**: las 26 rutinas posibles.
- **hecho_hipotesis**: rompe el muchos a muchos. Cada fila indica que un hecho sustenta una hipótesis dentro de una regla. Tiene 118 filas.
- **regla_inferencia**: agrupa los hechos de un mismo camino del árbol (R01 a R30). Sus hechos se unen con Y. Una hipótesis puede tener varias reglas; H01 y H02 tienen tres cada una.
- **peso_hecho_hipotesis**: el peso de cada hecho para cada hipótesis, que es la verosimilitud P(hecho | hipótesis); 26 × 15 = 390 filas. Junto con `hipotesis.probabilidad_previa` forma el modelo bayesiano.
- **ranking_consulta**: las 5 rutinas más probables de cada consulta, con su posición y probabilidad.
- **consulta** y **respuesta_pregunta**: guardan cada diagnóstico (rutina, probabilidad a posteriori y camino del árbol) y las respuestas del usuario, que forman su base de hechos.

El motor también decide qué preguntar. Solo muestra una pregunta si alguna regla que todavía es posible necesita un hecho de esa pregunta. Por eso el cuestionario es adaptativo sin reglas de navegación aparte.

## Motor de inferencia bayesiano

El sistema razona con probabilidades. Cada rutina H tiene:

- **P(H)**, probabilidad a priori: reglas de H / total de reglas. H01 y H02 tienen 3/30 (tres caminos del árbol llegan a ellas) y las demás 1/30.
- **P(E | H)**, peso hecho–hipótesis (verosimilitud) de cada respuesta E, guardado en `peso_hecho_hipotesis`. Se deriva de las reglas con la confiabilidad `c` de cada pregunta (0,95 por defecto):
  - si las reglas de H evalúan la pregunta: `P(E|H) = c · (reglas de H con E / reglas de H con la pregunta) + (1 − c) / opciones`
  - si no la evalúan: `P(E|H) = 1 / opciones` (la respuesta no informa sobre H).

Con cada respuesta se aplica el teorema de Bayes a las 26 rutinas:

```
P(H | E1..En) = P(H) · Π P(Ei | H)  /  Σk P(Hk) · Π P(Ei | Hk)
```

El resultado es la rutina con mayor probabilidad a posteriori, las 4 siguientes como alternativas (top 5) y la evolución de la probabilidad respuesta por respuesta. La regla (camino del árbol) que coincide con las respuestas se muestra como explicación.

Las probabilidades se calculan en PostgreSQL con la función `recalcular_probabilidades()`. Se ejecuta al cargar el conocimiento y cada vez que el ingeniero crea o elimina una hipótesis o una regla, así el motor no se modifica (RNF-04). Para cambiar la confianza en una pregunta:

```sql
UPDATE pregunta SET confiabilidad = 0.90 WHERE codigo = 'P1';
SELECT recalcular_probabilidades();
```

## Ejecutar desde VS Code

Renombre la carpeta `config_vscode` a `.vscode` y abra la carpeta del proyecto en VS Code. En "Ejecutar y depurar" aparecen las configuraciones *Inicializar base de datos*, *Ejecutar sistema experto* (consola) y *Ejecutar interfaz web*. Elija como intérprete el Python donde instaló `requirements.txt`.

## Interfaz web

Además de la consola, el sistema tiene una interfaz web (Flask) que usa exactamente los mismos servicios y el mismo motor bayesiano.

```bash
python servidor_web.py      # luego abrir http://127.0.0.1:5000
```

Secciones:

- **Inicio**: acceso rápido al diagnóstico, resumen y última rutina.
- **Diagnóstico**: el cuestionario con apariencia de chat; muestra la rutina, su probabilidad, cómo cambió con cada respuesta y las alternativas. Se guarda en el historial.
- **Mis rutinas**: historial de diagnósticos con su detalle.
- **Catálogo**: las 26 rutinas, filtrables por nivel y equipo.
- **Cómo funciona**: niveles, preguntas y significado del porcentaje.
- **Gestión** (experto, ingeniero y administrador): base de conocimiento, diagnósticos de todos los usuarios y, para el administrador, usuarios y roles. La edición de reglas sigue en la consola.

Archivos: `servidor_web.py` (arranque), `web/app.py` (rutas), `web/templates/` (HTML) y `web/static/estilos.css` (CSS).
