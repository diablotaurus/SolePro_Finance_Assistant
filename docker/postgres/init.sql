-- Initial database setup for SolePro Finance Assistant

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schema for better organization (optional)
-- CREATE SCHEMA IF NOT EXISTS solepro;

-- Set search path
-- SET search_path TO solepro, public;

-- Note: Tables will be created by SQLAlchemy/Alembic
-- This file is for any custom SQL that needs to run on initialization