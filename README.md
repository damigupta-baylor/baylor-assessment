# Gene Metadata Extraction and Database Population

This is the solution to the technical assessment. It is implemented in Docker, python, and Postgres.
There are many ways to solve this problem, many libraries that can be used. I did not have time to determine which
would be best, so this is just one approach. 

## Project Overview

The application performs the following tasks at startup:
1. **PDF Parsing**: Reads a PDF file (`pub.pdf`) to extract HGNC gene IDs.
2. **Metadata Extraction**: Queries external APIs (e.g., MyGene.info, NCBI ClinVar) for these hgnc gene ids
   - Fetches gene metadata i.e. aliases, genomic coordinates (hg19, hg38)
   - Fetches associated diseases. Identifies matches to these diseases in the publication text, and filters the rest out.
3. **CSV Generation**: Writes extracted data to three 
CSV files (`hgnc_gene.csv`, `gene_aliases.csv`, `gene_diseases.csv`) in the `/app/output` directory.
4. **Database Population**: Loads the CSV data into a PostgreSQL database with predefined tables 
(`hgnc_gene`, `gene_aliases`, `gene_diseases`).

**Disease Matching**  
The simplest way to do this would be to just use the MIM ids in the publication. But that would not cover all the diseases referenced in the 
publication, so I opted for another route - fetch disease names from an external source, and match against the presence of these disease names in the publication.
The steps are:
- For each gene, find corresponding variants in ClinVar. Across the variants, fetch associated disease names. Of course there are various databases from which disease information could be fetched, it would
have been good to also use MIM, MONDO, Orphanet etc. Also it would have been useful to also fetch disease aliases and the disease hierarchy. 
- For each such disease, do a fuzzy match against the publication text to identify 'similar' diseases e.g. the publication mentions `NPHS2 (HGNC:13394)`. In ClinVar, this is linked to `NEPHROTIC SYNDROME, TYPE 2`. The publication text has a phrase `nephrotic syndrome`, which is deemed a match. But clearly this mechanism is not perfect.
The mechanism works out for genes APOL1, COL4A3, NPHS2, HNF1A. But the mechanism fails to find a suitable match for RRAGD. In fact there are 2 incorrect associations with `Inborn genetic diseases`. So this mechanism needs to be improved.

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
