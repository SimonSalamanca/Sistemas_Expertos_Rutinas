-- =====================================================================
-- Carga del conocimiento del experto humano
-- 5 preguntas, 15 hechos, 26 hipótesis, 30 reglas de inferencia y
-- 118 filas en hecho_hipotesis. Al final se derivan las probabilidades
-- (26 previas y 390 filas en probabilidad_condicional).
-- Ejecutar después de 01_esquema.sql
-- =====================================================================

SET client_encoding = 'UTF8';
BEGIN;

-- 1. Preguntas del cuestionario
INSERT INTO pregunta (codigo, texto, variable, orden) VALUES
 ('P1', '¿Sabrías explicar cómo se hace correctamente un ejercicio básico, como una sentadilla, un empuje o una tracción?', 'tecnica_dominada', 1),
 ('P2', '¿Hace cuánto tiempo entrenas de forma constante?', 'tiempo_entrenando', 2),
 ('P3', '¿Con qué equipo cuentas para entrenar?', 'equipo_disponible', 3),
 ('P4', '¿Cuál es tu objetivo principal al entrenar?', 'objetivo_principal', 4),
 ('P5', '¿Prefieres priorizar volumen de entrenamiento o intensidad de carga en esta etapa?', 'fase_priorizada', 5);

-- 2. Hechos: opciones de respuesta de cada pregunta
INSERT INTO hecho (codigo, id_pregunta, valor)
SELECT v.codigo, p.id_pregunta, v.valor
FROM (VALUES
 ('HE01', 'P1', 'Sí'),
 ('HE02', 'P1', 'No'),
 ('HE03', 'P1', 'No estoy seguro'),
 ('HE04', 'P2', 'Menos de 6 meses'),
 ('HE05', 'P2', '6 meses a 2 años'),
 ('HE06', 'P2', 'Más de 2 años'),
 ('HE07', 'P3', 'Básico o en casa'),
 ('HE08', 'P3', 'Gimnasio completo'),
 ('HE09', 'P4', 'Fuerza'),
 ('HE10', 'P4', 'Hipertrofia'),
 ('HE11', 'P4', 'Resistencia'),
 ('HE12', 'P4', 'Pérdida de grasa'),
 ('HE13', 'P4', 'Rendimiento deportivo'),
 ('HE14', 'P5', 'Volumen'),
 ('HE15', 'P5', 'Intensidad')
) AS v(codigo, pregunta, valor)
JOIN pregunta p ON p.codigo = v.pregunta
ORDER BY v.codigo;

-- 3. Hipótesis (nodos terminales del árbol de decisión)
INSERT INTO hipotesis (codigo, nivel, equipo, objetivo, fase, descripcion_rutina) VALUES
 ('H01', 'Principiante', 'Básico o en casa', NULL, NULL,
  '3 días/semana. Circuito de cuerpo completo con peso corporal, bandas y mancuernas livianas: sentadilla, flexión de brazos, remo con banda, puente de glúteo y plancha abdominal. 3x10-15, carga mínima, énfasis total en la técnica antes de progresar.'),
 ('H02', 'Principiante', 'Gimnasio completo', NULL, NULL,
  '3 días/semana. Circuito de cuerpo completo con máquinas guiadas y barra con carga ligera: sentadilla en máquina o prensa, press de pecho en máquina, jalón al pecho, puente de glúteo y plancha abdominal. 3x10-15, carga ligera, énfasis total en la técnica.'),
 ('H03', 'Intermedio', 'Básico o en casa', 'Fuerza', NULL,
  '4 días/semana. Sentadilla búlgara con mancuernas, press militar con mancuernas, remo con mancuerna a una mano y peso muerto rumano con mancuernas. 4x8-10, aumento progresivo de carga.'),
 ('H04', 'Intermedio', 'Básico o en casa', 'Hipertrofia', NULL,
  '4 días/semana. Zancadas con mancuernas, press inclinado con mancuernas, remo renegado y press de hombro con mancuernas, distribuidos por grupo muscular. 4x10-12, descanso 45-60 s.'),
 ('H05', 'Intermedio', 'Básico o en casa', 'Resistencia', NULL,
  '5 días/semana. Circuitos de sentadilla con salto, burpees, remo con banda y escaladores, en rondas largas con descansos breves.'),
 ('H06', 'Intermedio', 'Básico o en casa', 'Pérdida de grasa', NULL,
  '5 días/semana. Circuitos de alta intensidad (HIIT): sentadilla con salto, mountain climbers, remo con banda y plancha dinámica, descansos cortos.'),
 ('H07', 'Intermedio', 'Básico o en casa', 'Rendimiento deportivo', NULL,
  '4 días/semana. Trabajo de potencia: sentadilla con salto, zancadas con salto, push press con mancuernas y desplazamientos laterales de agilidad con peso corporal, orientado al deporte.'),
 ('H08', 'Intermedio', 'Gimnasio completo', 'Fuerza', NULL,
  '4 días/semana. Sentadilla con barra, press banca con barra, remo con barra y peso muerto rumano con barra. Rutina dividida empuje/tracción/pierna, 4x6-8, cargas progresivas.'),
 ('H09', 'Intermedio', 'Gimnasio completo', 'Hipertrofia', NULL,
  '4-5 días/semana. Rutina por grupo muscular: press banca, jalón al pecho, extensión de cuádriceps y curl femoral en máquina. 4x10-12.'),
 ('H10', 'Intermedio', 'Gimnasio completo', 'Resistencia', NULL,
  '5 días/semana. Circuitos en máquinas (prensa, remo, elíptica) combinados con pesas de carga moderada, series largas.'),
 ('H11', 'Intermedio', 'Gimnasio completo', 'Pérdida de grasa', NULL,
  '5 días/semana. Circuitos de máquinas (prensa, remo, press) combinados con cardio en cinta o elíptica, descansos cortos.'),
 ('H12', 'Intermedio', 'Gimnasio completo', 'Rendimiento deportivo', NULL,
  '4 días/semana. Sentadilla con barra a velocidad controlada, arrancada con mancuernas y ejercicios pliométricos, orientado al deporte.'),
 ('H13', 'Avanzado', 'Básico o en casa', 'Fuerza', 'Volumen',
  '5 días/semana. Sentadilla búlgara pesada, press militar con mancuernas, remo a una mano y peso muerto rumano con mancuernas pesadas. Fase de acumulación: 4-5x8-10, descansos de 90 s.'),
 ('H14', 'Avanzado', 'Básico o en casa', 'Fuerza', 'Intensidad',
  '5 días/semana. Sentadilla a una pierna con mancuernas pesadas, press militar pesado y peso muerto rumano a carga máxima tolerable. Fase de intensificación: 5x3-5, descansos de 2-3 min.'),
 ('H15', 'Avanzado', 'Básico o en casa', 'Hipertrofia', 'Volumen',
  '5-6 días/semana. Zancadas búlgaras, press inclinado con mancuernas, remo renegado y elevaciones laterales, distribuidos por grupo muscular. 4-5x10-15, descansos cortos.'),
 ('H16', 'Avanzado', 'Básico o en casa', 'Hipertrofia', 'Intensidad',
  '5-6 días/semana. Técnicas de intensificación con mancuernas (series descendentes, repeticiones forzadas) en sentadilla búlgara, press y remo. Cargas más altas, menor volumen por sesión.'),
 ('H17', 'Avanzado', 'Básico o en casa', 'Resistencia', NULL,
  '6 días/semana. Circuitos de alta exigencia alternando bloques de alto volumen y bloques de alta intensidad: sentadilla con salto, burpees, mountain climbers y remo con banda, con planificación por semanas.'),
 ('H18', 'Avanzado', 'Básico o en casa', 'Pérdida de grasa', NULL,
  '6 días/semana. HIIT avanzado con mancuernas y bandas, alternando semanas de mayor volumen de trabajo metabólico y semanas de mayor intensidad, descansos mínimos.'),
 ('H19', 'Avanzado', 'Básico o en casa', 'Rendimiento deportivo', NULL,
  '5-6 días/semana. Trabajo de potencia, pliometría y velocidad con peso corporal y bandas, alternando bloques de acumulación de volumen y bloques de máxima intensidad según la fase de la temporada deportiva.'),
 ('H20', 'Avanzado', 'Gimnasio completo', 'Fuerza', 'Volumen',
  '5 días/semana. Sentadilla frontal, press banca con pausa, peso muerto rumano y remo con barra. Fase de acumulación: 4-5x8-10, descansos de 90 s.'),
 ('H21', 'Avanzado', 'Gimnasio completo', 'Fuerza', 'Intensidad',
  '5 días/semana. Sentadilla trasera, press banca y peso muerto convencional con barra olímpica. Fase de intensificación: 5x3-5, descansos de 2-3 min, progresión estricta hacia cargas máximas.'),
 ('H22', 'Avanzado', 'Gimnasio completo', 'Hipertrofia', 'Volumen',
  '5-6 días/semana. Rutina por grupo muscular: press banca, jalón al pecho, extensión de cuádriceps y curl femoral. 4-5x10-15, descansos cortos.'),
 ('H23', 'Avanzado', 'Gimnasio completo', 'Hipertrofia', 'Intensidad',
  '5-6 días/semana. Técnicas de intensificación (series descendentes, superseries, repeticiones forzadas) en press banca, sentadilla y jalón al pecho. Cargas más altas, menor volumen por sesión.'),
 ('H24', 'Avanzado', 'Gimnasio completo', 'Resistencia', NULL,
  '6 días/semana. Circuitos en máquinas y pesas alternando bloques de alto volumen y bloques de alta intensidad, con planificación por semanas.'),
 ('H25', 'Avanzado', 'Gimnasio completo', 'Pérdida de grasa', NULL,
  '6 días/semana. HIIT avanzado con máquinas y barra, alternando semanas de mayor volumen metabólico y semanas de mayor intensidad, descansos mínimos.'),
 ('H26', 'Avanzado', 'Gimnasio completo', 'Rendimiento deportivo', NULL,
  '5-6 días/semana. Trabajo de potencia con barra (arrancada, sentadilla explosiva) y pliometría, alternando bloques de volumen y bloques de máxima intensidad según la fase de la temporada deportiva.');

-- 4. Reglas de inferencia: una por camino del árbol
INSERT INTO regla_inferencia (codigo, id_hipotesis)
SELECT v.codigo, h.id_hipotesis
FROM (VALUES
 ('R01', 'H01'),
 ('R02', 'H02'),
 ('R03', 'H01'),
 ('R04', 'H02'),
 ('R05', 'H01'),
 ('R06', 'H02'),
 ('R07', 'H03'),
 ('R08', 'H04'),
 ('R09', 'H05'),
 ('R10', 'H06'),
 ('R11', 'H07'),
 ('R12', 'H08'),
 ('R13', 'H09'),
 ('R14', 'H10'),
 ('R15', 'H11'),
 ('R16', 'H12'),
 ('R17', 'H13'),
 ('R18', 'H14'),
 ('R19', 'H15'),
 ('R20', 'H16'),
 ('R21', 'H17'),
 ('R22', 'H18'),
 ('R23', 'H19'),
 ('R24', 'H20'),
 ('R25', 'H21'),
 ('R26', 'H22'),
 ('R27', 'H23'),
 ('R28', 'H24'),
 ('R29', 'H25'),
 ('R30', 'H26')
) AS v(codigo, hipotesis)
JOIN hipotesis h ON h.codigo = v.hipotesis
ORDER BY v.codigo;

-- 5. hecho_hipotesis: hechos que sustentan cada hipótesis, por regla.
--    Los hechos de una misma regla se unen con Y.
INSERT INTO hecho_hipotesis (id_hecho, id_hipotesis, id_regla)
SELECT he.id_hecho, r.id_hipotesis, r.id_regla
FROM (VALUES
 -- R01: SI tecnica_dominada = No Y equipo_disponible = Básico o en casa ENTONCES H01
 ('R01', 'HE02'),
 ('R01', 'HE07'),
 -- R02: SI tecnica_dominada = No Y equipo_disponible = Gimnasio completo ENTONCES H02
 ('R02', 'HE02'),
 ('R02', 'HE08'),
 -- R03: SI tecnica_dominada = No estoy seguro Y equipo_disponible = Básico o en casa ENTONCES H01
 ('R03', 'HE03'),
 ('R03', 'HE07'),
 -- R04: SI tecnica_dominada = No estoy seguro Y equipo_disponible = Gimnasio completo ENTONCES H02
 ('R04', 'HE03'),
 ('R04', 'HE08'),
 -- R05: SI tecnica_dominada = Sí Y tiempo_entrenando = Menos de 6 meses Y equipo_disponible = Básico o en casa ENTONCES H01
 ('R05', 'HE01'),
 ('R05', 'HE04'),
 ('R05', 'HE07'),
 -- R06: SI tecnica_dominada = Sí Y tiempo_entrenando = Menos de 6 meses Y equipo_disponible = Gimnasio completo ENTONCES H02
 ('R06', 'HE01'),
 ('R06', 'HE04'),
 ('R06', 'HE08'),
 -- R07: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Fuerza ENTONCES H03
 ('R07', 'HE01'),
 ('R07', 'HE05'),
 ('R07', 'HE07'),
 ('R07', 'HE09'),
 -- R08: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Hipertrofia ENTONCES H04
 ('R08', 'HE01'),
 ('R08', 'HE05'),
 ('R08', 'HE07'),
 ('R08', 'HE10'),
 -- R09: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Resistencia ENTONCES H05
 ('R09', 'HE01'),
 ('R09', 'HE05'),
 ('R09', 'HE07'),
 ('R09', 'HE11'),
 -- R10: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Pérdida de grasa ENTONCES H06
 ('R10', 'HE01'),
 ('R10', 'HE05'),
 ('R10', 'HE07'),
 ('R10', 'HE12'),
 -- R11: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Rendimiento deportivo ENTONCES H07
 ('R11', 'HE01'),
 ('R11', 'HE05'),
 ('R11', 'HE07'),
 ('R11', 'HE13'),
 -- R12: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Fuerza ENTONCES H08
 ('R12', 'HE01'),
 ('R12', 'HE05'),
 ('R12', 'HE08'),
 ('R12', 'HE09'),
 -- R13: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Hipertrofia ENTONCES H09
 ('R13', 'HE01'),
 ('R13', 'HE05'),
 ('R13', 'HE08'),
 ('R13', 'HE10'),
 -- R14: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Resistencia ENTONCES H10
 ('R14', 'HE01'),
 ('R14', 'HE05'),
 ('R14', 'HE08'),
 ('R14', 'HE11'),
 -- R15: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Pérdida de grasa ENTONCES H11
 ('R15', 'HE01'),
 ('R15', 'HE05'),
 ('R15', 'HE08'),
 ('R15', 'HE12'),
 -- R16: SI tecnica_dominada = Sí Y tiempo_entrenando = 6 meses a 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Rendimiento deportivo ENTONCES H12
 ('R16', 'HE01'),
 ('R16', 'HE05'),
 ('R16', 'HE08'),
 ('R16', 'HE13'),
 -- R17: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Fuerza Y fase_priorizada = Volumen ENTONCES H13
 ('R17', 'HE01'),
 ('R17', 'HE06'),
 ('R17', 'HE07'),
 ('R17', 'HE09'),
 ('R17', 'HE14'),
 -- R18: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Fuerza Y fase_priorizada = Intensidad ENTONCES H14
 ('R18', 'HE01'),
 ('R18', 'HE06'),
 ('R18', 'HE07'),
 ('R18', 'HE09'),
 ('R18', 'HE15'),
 -- R19: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Hipertrofia Y fase_priorizada = Volumen ENTONCES H15
 ('R19', 'HE01'),
 ('R19', 'HE06'),
 ('R19', 'HE07'),
 ('R19', 'HE10'),
 ('R19', 'HE14'),
 -- R20: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Hipertrofia Y fase_priorizada = Intensidad ENTONCES H16
 ('R20', 'HE01'),
 ('R20', 'HE06'),
 ('R20', 'HE07'),
 ('R20', 'HE10'),
 ('R20', 'HE15'),
 -- R21: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Resistencia ENTONCES H17
 ('R21', 'HE01'),
 ('R21', 'HE06'),
 ('R21', 'HE07'),
 ('R21', 'HE11'),
 -- R22: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Pérdida de grasa ENTONCES H18
 ('R22', 'HE01'),
 ('R22', 'HE06'),
 ('R22', 'HE07'),
 ('R22', 'HE12'),
 -- R23: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Básico o en casa Y objetivo_principal = Rendimiento deportivo ENTONCES H19
 ('R23', 'HE01'),
 ('R23', 'HE06'),
 ('R23', 'HE07'),
 ('R23', 'HE13'),
 -- R24: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Fuerza Y fase_priorizada = Volumen ENTONCES H20
 ('R24', 'HE01'),
 ('R24', 'HE06'),
 ('R24', 'HE08'),
 ('R24', 'HE09'),
 ('R24', 'HE14'),
 -- R25: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Fuerza Y fase_priorizada = Intensidad ENTONCES H21
 ('R25', 'HE01'),
 ('R25', 'HE06'),
 ('R25', 'HE08'),
 ('R25', 'HE09'),
 ('R25', 'HE15'),
 -- R26: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Hipertrofia Y fase_priorizada = Volumen ENTONCES H22
 ('R26', 'HE01'),
 ('R26', 'HE06'),
 ('R26', 'HE08'),
 ('R26', 'HE10'),
 ('R26', 'HE14'),
 -- R27: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Hipertrofia Y fase_priorizada = Intensidad ENTONCES H23
 ('R27', 'HE01'),
 ('R27', 'HE06'),
 ('R27', 'HE08'),
 ('R27', 'HE10'),
 ('R27', 'HE15'),
 -- R28: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Resistencia ENTONCES H24
 ('R28', 'HE01'),
 ('R28', 'HE06'),
 ('R28', 'HE08'),
 ('R28', 'HE11'),
 -- R29: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Pérdida de grasa ENTONCES H25
 ('R29', 'HE01'),
 ('R29', 'HE06'),
 ('R29', 'HE08'),
 ('R29', 'HE12'),
 -- R30: SI tecnica_dominada = Sí Y tiempo_entrenando = Más de 2 años Y equipo_disponible = Gimnasio completo Y objetivo_principal = Rendimiento deportivo ENTONCES H26
 ('R30', 'HE01'),
 ('R30', 'HE06'),
 ('R30', 'HE08'),
 ('R30', 'HE13')
) AS v(regla, hecho)
JOIN regla_inferencia r ON r.codigo = v.regla
JOIN hecho he ON he.codigo = v.hecho
ORDER BY v.regla, v.hecho;

-- 6. Probabilidades del modelo bayesiano, derivadas de las reglas
SELECT recalcular_probabilidades();

COMMIT;

-- Verificación: 5 / 15 / 26 / 30 / 118 / 390
SELECT 'pregunta' AS tabla, COUNT(*) AS registros FROM pregunta
UNION ALL SELECT 'hecho', COUNT(*) FROM hecho
UNION ALL SELECT 'hipotesis', COUNT(*) FROM hipotesis
UNION ALL SELECT 'regla_inferencia', COUNT(*) FROM regla_inferencia
UNION ALL SELECT 'hecho_hipotesis', COUNT(*) FROM hecho_hipotesis
UNION ALL SELECT 'probabilidad_condicional', COUNT(*) FROM probabilidad_condicional;
