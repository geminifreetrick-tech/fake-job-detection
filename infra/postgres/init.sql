-- Bootstrap script run by the postgres container on first start.
-- We create logically separated schemas owned by the main app user.
CREATE SCHEMA IF NOT EXISTS auth AUTHORIZATION CURRENT_USER;
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION CURRENT_USER;
