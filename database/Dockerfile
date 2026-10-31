# Use the official PostgreSQL image from Docker Hub
FROM postgres:16

# Define a mount point for persistent data
VOLUME ["/var/lib/postgresql/data"]

# Expose PostgreSQL port
EXPOSE 5432


COPY create_table.sql /docker-entrypoint-initdb.d/01-create-tables.sql





