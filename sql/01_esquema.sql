-- =====================================================================
-- Sistema experto para la generación de rutinas de entrenamiento
-- Esquema de la base de datos (PostgreSQL)
--
-- Núcleo del sistema experto:
--   hecho  <--  hecho_hipotesis  -->  hipotesis      (muchos a muchos)
--                     |
--                     v
--              regla_inferencia   (agrupa los hechos de un mismo camino
--                                  del árbol: SI h1 Y h2 ... ENTONCES Hxx)
--
-- Modelo probabilístico (bayesiano):
--   hipotesis.probabilidad_previa   P(H)      probabilidad a priori
--   peso_hecho_hipotesis.peso       P(E | H)  peso de cada hecho para cada
--                                   hipótesis (verosimilitud)
--   pregunta.confiabilidad          qué tanto refleja cada respuesta el
--                                   camino real del árbol
--   P(H) y los pesos se derivan de las reglas con recalcular_probabilidades().
--
-- Cada consulta guarda su ranking (top 5) en ranking_consulta.
-- =====================================================================

SET client_encoding = 'UTF8';

DROP TABLE IF EXISTS ranking_consulta, respuesta_pregunta, consulta, usuario,
                     peso_hecho_hipotesis, probabilidad_condicional,
                     hecho_hipotesis, regla_inferencia, hipotesis,
                     hecho, pregunta CASCADE;
DROP FUNCTION IF EXISTS recalcular_probabilidades();

-- ---------------------------------------------------------------------
-- 1. BASE DE CONOCIMIENTO
-- ---------------------------------------------------------------------

-- Preguntas del cuestionario de diagnóstico (P1..P5).
CREATE TABLE pregunta (
    id_pregunta  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo       VARCHAR(5)   NOT NULL UNIQUE,
    texto        VARCHAR(300) NOT NULL,
    variable     VARCHAR(40)  NOT NULL UNIQUE,   -- nombre de la variable del sistema
    orden        INT          NOT NULL UNIQUE,
    -- Probabilidad de que la respuesta del usuario coincida con el camino
    -- del árbol de la rutina correcta. El resto (1 - confiabilidad) se
    -- reparte entre todas las opciones como margen de error.
    confiabilidad NUMERIC(4,3) NOT NULL DEFAULT 0.950
                  CHECK (confiabilidad > 0 AND confiabilidad <= 1)
);

-- Hechos: cada opción de respuesta de una pregunta (variable = valor).
CREATE TABLE hecho (
    id_hecho     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo       VARCHAR(5)   NOT NULL UNIQUE,   -- HE01..HE15
    id_pregunta  INT          NOT NULL,
    valor        VARCHAR(60)  NOT NULL,
    CONSTRAINT fk_hecho_pregunta FOREIGN KEY (id_pregunta)
        REFERENCES pregunta(id_pregunta) ON DELETE CASCADE,
    CONSTRAINT uq_hecho_valor UNIQUE (id_pregunta, valor),
    -- permite validar en respuesta_pregunta que el hecho sea de esa pregunta
    CONSTRAINT uq_hecho_pregunta UNIQUE (id_hecho, id_pregunta)
);

-- Hipótesis: las 26 rutinas que el sistema puede concluir (H01..H26).
CREATE TABLE hipotesis (
    id_hipotesis        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo              VARCHAR(5)   NOT NULL UNIQUE,
    nivel               VARCHAR(20)  NOT NULL
                        CHECK (nivel IN ('Principiante','Intermedio','Avanzado')),
    equipo              VARCHAR(30)  NOT NULL,
    objetivo            VARCHAR(30)  NULL,
    fase                VARCHAR(20)  NULL,
    descripcion_rutina  TEXT         NOT NULL,
    -- P(H): proporción de caminos del árbol (reglas) que llegan a la rutina
    probabilidad_previa NUMERIC(9,8) NOT NULL DEFAULT 0
                        CHECK (probabilidad_previa BETWEEN 0 AND 1)
);

-- Regla de inferencia: un camino del árbol de decisión que concluye en
-- una hipótesis. Sus hechos están en hecho_hipotesis y se unen con Y.
-- Una hipótesis puede tener varias reglas (H01 y H02 tienen tres cada una).
CREATE TABLE regla_inferencia (
    id_regla      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo        VARCHAR(5) NOT NULL UNIQUE,    -- R01..R30
    id_hipotesis  INT        NOT NULL,
    CONSTRAINT fk_regla_hipotesis FOREIGN KEY (id_hipotesis)
        REFERENCES hipotesis(id_hipotesis) ON DELETE CASCADE,
    CONSTRAINT uq_regla_hipotesis UNIQUE (id_regla, id_hipotesis)
);

-- Tabla que rompe el muchos a muchos entre hecho e hipótesis.
-- Cada fila dice: "este hecho sustenta esta hipótesis dentro de esta regla".
CREATE TABLE hecho_hipotesis (
    id_hecho_hipotesis  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_hecho            INT NOT NULL,
    id_hipotesis        INT NOT NULL,
    id_regla            INT NOT NULL,
    CONSTRAINT fk_hh_hecho FOREIGN KEY (id_hecho)
        REFERENCES hecho(id_hecho) ON DELETE CASCADE,
    CONSTRAINT fk_hh_hipotesis FOREIGN KEY (id_hipotesis)
        REFERENCES hipotesis(id_hipotesis) ON DELETE CASCADE,
    -- la regla debe pertenecer a la misma hipótesis de la fila
    CONSTRAINT fk_hh_regla FOREIGN KEY (id_regla, id_hipotesis)
        REFERENCES regla_inferencia(id_regla, id_hipotesis) ON DELETE CASCADE,
    CONSTRAINT uq_hh_regla_hecho UNIQUE (id_regla, id_hecho)
);

-- Pesos hecho–hipótesis: para cada par (hecho, hipótesis), el peso es la
-- verosimilitud P(hecho | hipótesis), es decir, la probabilidad de que un
-- usuario al que le corresponde la rutina H responda ese hecho. Para cada
-- hipótesis, los pesos de las opciones de una misma pregunta suman 1.
CREATE TABLE peso_hecho_hipotesis (
    id_peso       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_hecho      INT          NOT NULL,
    id_hipotesis  INT          NOT NULL,
    peso          NUMERIC(9,8) NOT NULL CHECK (peso BETWEEN 0 AND 1),
    CONSTRAINT fk_peso_hecho FOREIGN KEY (id_hecho)
        REFERENCES hecho(id_hecho) ON DELETE CASCADE,
    CONSTRAINT fk_peso_hipotesis FOREIGN KEY (id_hipotesis)
        REFERENCES hipotesis(id_hipotesis) ON DELETE CASCADE,
    CONSTRAINT uq_peso_hecho_hipotesis UNIQUE (id_hecho, id_hipotesis)
);

-- Deriva las probabilidades a partir de las reglas (caminos del árbol):
--   P(H)     = reglas de H / total de reglas
--   peso(E, H) = P(E | H) = c * (reglas de H que usan E / reglas de H que evalúan la pregunta)
--              + (1 - c) / opciones de la pregunta
--              donde c es la confiabilidad de la pregunta.
--   Si ninguna regla de H evalúa la pregunta, P(E | H) = 1 / opciones
--   (la pregunta no aporta información sobre H).
-- Se ejecuta al cargar el conocimiento y cada vez que cambia una regla o
-- una hipótesis, sin modificar el motor (RNF-04).
CREATE FUNCTION recalcular_probabilidades() RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    total_reglas INT;
BEGIN
    SELECT COUNT(*) INTO total_reglas FROM regla_inferencia;

    UPDATE hipotesis h
       SET probabilidad_previa = CASE WHEN total_reglas = 0 THEN 0 ELSE
           (SELECT COUNT(*) FROM regla_inferencia r
             WHERE r.id_hipotesis = h.id_hipotesis)::NUMERIC / total_reglas END;

    DELETE FROM peso_hecho_hipotesis;

    INSERT INTO peso_hecho_hipotesis (id_hipotesis, id_hecho, peso)
    WITH conteo AS (
        SELECT hi.id_hipotesis, he.id_hecho, he.id_pregunta,
               (SELECT COUNT(*) FROM hecho_hipotesis hh
                 WHERE hh.id_hipotesis = hi.id_hipotesis
                   AND hh.id_hecho = he.id_hecho) AS reglas_con_hecho
          FROM hipotesis hi CROSS JOIN hecho he
    ), totales AS (
        SELECT id_hipotesis, id_pregunta,
               SUM(reglas_con_hecho) AS reglas_con_pregunta,
               COUNT(*)              AS opciones
          FROM conteo GROUP BY id_hipotesis, id_pregunta
    )
    SELECT c.id_hipotesis, c.id_hecho,
           CASE WHEN t.reglas_con_pregunta = 0 THEN 1.0 / t.opciones
                ELSE p.confiabilidad * c.reglas_con_hecho / t.reglas_con_pregunta
                     + (1 - p.confiabilidad) / t.opciones
           END
      FROM conteo c
      JOIN totales t  ON t.id_hipotesis = c.id_hipotesis
                     AND t.id_pregunta = c.id_pregunta
      JOIN pregunta p ON p.id_pregunta = c.id_pregunta;
END;
$$;

-- ---------------------------------------------------------------------
-- 2. SISTEMA TRANSACCIONAL
-- ---------------------------------------------------------------------

CREATE TABLE usuario (
    id_usuario       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(120) NOT NULL,
    correo           VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash  VARCHAR(200) NOT NULL,
    rol              VARCHAR(30)  NOT NULL DEFAULT 'usuario'
                     CHECK (rol IN ('usuario','experto','ingeniero','administrador')),
    fecha_registro   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Consulta: cada vez que un usuario realiza el diagnóstico.
-- Guarda la hipótesis (rutina) más probable, su probabilidad a posteriori
-- y la regla (camino del árbol) que explica el resultado.
CREATE TABLE consulta (
    id_consulta   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario    INT       NOT NULL,
    id_regla      INT       NOT NULL,
    id_hipotesis  INT       NOT NULL,
    probabilidad  NUMERIC(6,5) NOT NULL CHECK (probabilidad BETWEEN 0 AND 1),
    fecha         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_consulta_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_consulta_regla FOREIGN KEY (id_regla, id_hipotesis)
        REFERENCES regla_inferencia(id_regla, id_hipotesis)
);

-- Respuesta del usuario a cada pregunta dentro de una consulta.
-- Es la base de hechos de esa consulta.
CREATE TABLE respuesta_pregunta (
    id_respuesta  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_consulta   INT NOT NULL,
    id_pregunta   INT NOT NULL,
    id_hecho      INT NOT NULL,
    CONSTRAINT fk_respuesta_consulta FOREIGN KEY (id_consulta)
        REFERENCES consulta(id_consulta) ON DELETE CASCADE,
    -- el hecho elegido debe ser una opción de esa misma pregunta
    CONSTRAINT fk_respuesta_hecho FOREIGN KEY (id_hecho, id_pregunta)
        REFERENCES hecho(id_hecho, id_pregunta),
    CONSTRAINT uq_respuesta_pregunta UNIQUE (id_consulta, id_pregunta)
);

-- Ranking de cada consulta: las 5 rutinas más probables con su probabilidad
-- a posteriori al momento del diagnóstico (posición 1 = la recomendada).
CREATE TABLE ranking_consulta (
    id_ranking    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_consulta   INT          NOT NULL,
    posicion      SMALLINT     NOT NULL CHECK (posicion >= 1),
    id_hipotesis  INT          NOT NULL,
    probabilidad  NUMERIC(6,5) NOT NULL CHECK (probabilidad BETWEEN 0 AND 1),
    CONSTRAINT fk_ranking_consulta FOREIGN KEY (id_consulta)
        REFERENCES consulta(id_consulta) ON DELETE CASCADE,
    -- si el ingeniero elimina una hipótesis, sale de los rankings guardados
    CONSTRAINT fk_ranking_hipotesis FOREIGN KEY (id_hipotesis)
        REFERENCES hipotesis(id_hipotesis) ON DELETE CASCADE,
    CONSTRAINT uq_ranking_posicion UNIQUE (id_consulta, posicion),
    CONSTRAINT uq_ranking_hipotesis UNIQUE (id_consulta, id_hipotesis)
);
