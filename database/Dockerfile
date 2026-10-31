# Use the official PostgreSQL image
FROM postgres:16

# Persistent database storage
VOLUME ["/var/lib/postgresql/data"]

# Copy SQL script to initialize the database
COPY create_table.sql /docker-entrypoint-initdb.d/01-create-tables.sql

# Expose PostgreSQL port
EXPOSE 5432