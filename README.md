# Gene Metadata Extraction and Database Population

This is the solution to the technical assessment. It is implemented in Docker, python, and Postgres.
There are many ways to solve this problem, many libraries that can be used. I did not have time to determine which
would be best, so this is just one approach. 

## Project Overview

The application performs the following tasks at startup:
1. **PDF Parsing**: Reads a PDF file (`pub.pdf`) to extract HGNC gene IDs.
2. **Metadata Extraction**: Queries external APIs (e.g., MyGene.info, NCBI ClinVar) for these hgnc gene ids
   - Fetches gene metadata i.e. aliases, genomic coordinates (hg19, hg38)
   - Fetches all associated diseases from ClinVar. Filters the diseases - a fuzzy match is run on disease name 
   against the pdf text, retain Clinvar diseases which meet a similarity threshold.
3. **CSV Generation**: Writes extracted data to three 
CSV files (`hgnc_gene.csv`, `gene_aliases.csv`, `gene_diseases.csv`) in the `/app/output` directory.
4. **Database Population**: Loads the CSV data into a PostgreSQL database with predefined tables 
(`hgnc_gene`, `gene_aliases`, `gene_diseases`).

This aims to find the 'best match' of Clinvar diseases with diseases mentioned in the text. Reasonable gene disease 
matches are found for 4 of the genes. For the gene RRAGD, a good match is not found.  

## Prerequisites

- **Docker**: Ensure Docker and Docker Compose are installed.

## Setup and Usage
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Build and Start the Services:
   - Run the following command to build and start the PostgreSQL database:
     ```bash
     docker-compose build && docker-compose up mydb -d
     ```
   - Wait for the database to be fully initialized (this may take a few seconds).

3. Run the Application:
   - Start the Python application to parse the PDF, generate CSVs, and populate the database:
     ```bash
     docker-compose up myapp
     ```

4. Verify the Output:
   - Check the `/app/output` directory (mounted to `./output` on your machine) for the generated CSV files:
     - `hgnc_gene.csv`: Contains HGNC ID, gene name, and genomic coordinates (hg38, hg19).
     - `gene_aliases.csv`: Contains HGNC ID and gene aliases.
     - `gene_diseases.csv`: Contains HGNC ID and associated diseases filtered by text similarity.
   - Connect to the PostgreSQL database to verify the populated tables:
     - Use a tool like `psql` or dBeaver.
     - Connection details: Host=`localhost`, Port=`5433`, Database=`MYDB`, User=`postgres`, Password=`postgres`.

5. Running Unit Tests:
   - Some unit tests are provided - `test_gene_metadata.py` and `test_main.py`. Note they are not complete.
   - To run the tests, ensure you are in the project directory and have the required dependencies installed:
     ```bash
     pip install -r requirements.txt
     ```
   - Execute the tests using:
     ```bash
     python -m unittest discover -v
     ```


## Database Schema
The database contains three tables:
- `hgnc_gene`
- `gene_aliases`
- `gene_diseases`

See `init.sql` for the complete schema definition.


## Future Improvements

- Set up a directory structure with dirs for `src`, `data` etc.
- Improve error handling.
- Implement features for scalability.
- Expand unit test coverage to include more edge cases and database interactions.
- Improve the mechanism for fuzzy matching on disease names.

## Deliverables
See the `deliverables` directory.
