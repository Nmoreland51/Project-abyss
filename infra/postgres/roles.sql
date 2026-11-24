-- Cluster-wide roles. Run as a superuser with psql variables :migrator_pw and :runtime_pw.
-- app_migrator owns the schema and runs migrations; app_runtime (the API) has DML only.
SELECT format('CREATE ROLE app_migrator LOGIN PASSWORD %L', :'migrator_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_migrator') \gexec
SELECT format('CREATE ROLE app_runtime LOGIN PASSWORD %L', :'runtime_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime') \gexec
