-- 0) На всякий случай: где мы и что видим
SELECT current_database() AS db, current_user AS usr;
SHOW search_path;

-- 1) Схемы и расширения
\dn+
\dx

-- 2) Что за объекты есть
-- Таблицы:
\dt *.*
-- Представления (VIEW):
\dv *.*
-- Материализованные представления (матвьюхи = потенциальные кубы):
\dm *.*

-- 3) Краткие размеры и примерные строки по пользовательским таблицам
SELECT
  schemaname,
  relname                           AS table_name,
  pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
  n_live_tup                        AS est_rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 4) Список колонок (по всем схемам кроме системных)
SELECT
  c.table_schema,
  c.table_name,
  c.ordinal_position,
  c.column_name,
  c.data_type,
  c.is_nullable,
  c.character_maximum_length,
  c.numeric_precision,
  c.numeric_scale
FROM information_schema.columns c
WHERE c.table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY c.table_schema, c.table_name, c.ordinal_position;

-- 5) Первичные ключи (PK)
SELECT
  tc.table_schema,
  tc.table_name,
  kc.column_name,
  tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kc
  ON  kc.table_schema  = tc.table_schema
  AND kc.table_name    = tc.table_name
  AND kc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_schema, tc.table_name, kc.ordinal_position;

-- 6) Внешние ключи (FK) — связи таблиц (очень важно для звезды)
SELECT
  tc.table_schema    AS src_schema,
  tc.table_name      AS src_table,
  kcu.column_name    AS src_column,
  ccu.table_schema   AS ref_schema,
  ccu.table_name     AS ref_table,
  ccu.column_name    AS ref_column,
  tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY src_schema, src_table;

-- 7) Индексы (полезно понять, что уже оптимизировано)
SELECT
  n.nspname      AS schema_name,
  c.relname      AS table_name,
  i.relname      AS index_name,
  pg_size_pretty(pg_relation_size(i.oid)) AS index_size,
  pg_get_indexdef(i.oid) AS index_def
FROM pg_index x
JOIN pg_class i ON i.oid = x.indexrelid
JOIN pg_class c ON c.oid = x.indrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname NOT IN ('pg_catalog','information_schema')
ORDER BY pg_relation_size(i.oid) DESC;

-- 8) Кандидаты в факт-таблицы (много FK в одну таблицу) и измерения
-- 8a) Сколько у таблицы внешних ключей (source side)
WITH fk_counts AS (
  SELECT tc.table_schema, tc.table_name, COUNT(*) AS fk_cnt
  FROM information_schema.table_constraints tc
  WHERE tc.constraint_type='FOREIGN KEY'
  GROUP BY tc.table_schema, tc.table_name
)
SELECT * FROM fk_counts ORDER BY fk_cnt DESC NULLS LAST;

-- 8b) Сколько раз на таблицу ссылаются другими (dimension candidates)
WITH ref_counts AS (
  SELECT ccu.table_schema AS table_schema, ccu.table_name AS table_name, COUNT(*) AS referenced_by_cnt
  FROM information_schema.table_constraints tc
  JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type='FOREIGN KEY'
  GROUP BY ccu.table_schema, ccu.table_name
)
SELECT * FROM ref_counts ORDER BY referenced_by_cnt DESC NULLS LAST;

-- 9) По конкретной таблице (когда определимся): описание структуры
-- Заменишь schema.table на нужную
-- \d+ schema.table

-- 10) Несколько примеров строк из крупных таблиц (подставь реальные имена)
-- SELECT * FROM schema.table LIMIT 5;
