import os
import time
import logging
import psycopg2
from psycopg2 import OperationalError
from gene_metadata import parse_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def wait_for_db(host, port, database, user, password, max_attempts=30, delay=2):
    """Wait for the database to be ready."""
    for attempt in range(max_attempts):
        try:
            conn = psycopg2.connect(
                database=database, user=user, password=password, host=host, port=port
            )
            conn.close()
            logger.info("Database is ready.")
            return True
        except OperationalError as e:
            logger.warning(f"Database not ready, attempt {attempt + 1}/{max_attempts}: {e}")
            time.sleep(delay)
    logger.error("Failed to connect to database after %d attempts.", max_attempts)
    return False


def populate_db():
    """Populate the database with data from CSV files."""
    # Get database credentials from environment variables
    db_config = {
        'database': os.getenv('DB_NAME', 'MYDB'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'mydb'),
        'port': os.getenv('DB_PORT', '5432')
    }

    # Define CSV file paths relative to /app/output
    output_dir = os.path.join('/app', 'output')
    csv_files = [
        os.path.join(output_dir, 'hgnc_gene.csv'),
        os.path.join(output_dir, 'gene_diseases.csv'),
        os.path.join(output_dir, 'gene_aliases.csv')
    ]

    # Check if output directory and CSV files exist
    if not os.path.exists(output_dir):
        logger.error("Output directory %s does not exist.", output_dir)
        raise FileNotFoundError(f"Output directory {output_dir} does not exist")
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            logger.error("CSV file %s does not exist.", csv_file)
            raise FileNotFoundError(f"CSV file {csv_file} does not exist")

    # Connect to database
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        # Populate hgnc_gene table
        with open(csv_files[0], 'r') as f:
            next(f)
            cursor.copy_expert(
                "COPY hgnc_gene (hgnc_id, hgnc_gene_name, hg38, hg19) FROM STDIN WITH (FORMAT CSV, DELIMITER ',', QUOTE '\"', ESCAPE '\"')",
                f
            )
    except psycopg2.Error as e:
        logger.warning(
            f"Failed to populate hgnc_gene table due to duplicate keys or other error: {e}")
    try:
        # Populate gene_diseases table
        with open(csv_files[1], 'r') as f:
            next(f)
            cursor.copy_expert(
                "COPY gene_diseases (hgnc_id, disease) FROM STDIN WITH (FORMAT CSV, DELIMITER ',', QUOTE '\"', ESCAPE '\"')",
                f
            )
    except psycopg2.Error as e:
        logger.warning(
            f"Failed to populate gene_diseases table due to duplicate keys or other error: {e}")

    try:
        # Populate gene_aliases table
        with open(csv_files[2], 'r') as f:
            next(f)
            cursor.copy_expert(
                "COPY gene_aliases (hgnc_id, alias) FROM STDIN WITH (FORMAT CSV, DELIMITER ',', QUOTE '\"', ESCAPE '\"')",
                f
            )
    except psycopg2.Error as e:
        logger.warning(
            f"Failed to populate gene_aliases table due to duplicate keys or other error: {e}")

    logger.info("Successfully populated database.")


def main():
    """Main application entry point."""
    logger.info("Starting application...")

    # Wait for database to be ready
    db_config = {
        'host': os.getenv('DB_HOST', 'mydb'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'MYDB'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }
    if not wait_for_db(**db_config):
        logger.error("Application exiting due to database unavailability.")
        return

    try:
        # Parse PDF to generate CSV files
        parse_pdf()
        # Populate database with CSV data
        populate_db()
        logger.info("Application completed successfully.")
    except Exception as e:
        logger.error("Application failed: %s", e)
        raise


if __name__ == "__main__":
    main()
