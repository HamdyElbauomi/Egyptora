-- Runs once when the Docker database is first created.
-- Separate database for pytest, so tests never touch your dev data.
CREATE DATABASE egyptora_test OWNER egyptora;
