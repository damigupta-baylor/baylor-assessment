import csv
import os
import re
import logging
from typing import Optional, List
from dataclasses import dataclass, field
import PyPDF2
import requests
import mygene
from xml.etree import ElementTree as ET
from fuzzywuzzy import fuzz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class GeneDisease:
    symbol: str
    flt_diseases: List[str] = field(default_factory=list)
    hgnc_id: Optional[str] = None
    aliases: Optional[List[str]] = None
    hg38: Optional[str] = None
    hg19: Optional[str] = None
    diseases: Optional[List] = None


def read_pdf_file(filename: str) -> str:
    """Reads a PDF file into text."""
    logger.info(f"Starting PDF file reading for {filename}")
    if not os.path.exists(filename):
        logger.error(f"PDF file {filename} not found.")
        raise FileNotFoundError(f"PDF file {filename} not found")

    try:
        with open(filename, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    text += page_text
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num} in {filename}: {e}")
            logger.info(f"Completed PDF file reading for {filename}, extracted {len(text)} characters")
            return text
    except Exception as e:
        logger.error(f"Error reading PDF file {filename}: {e}")
        raise


def get_diseases(gene_symbol: str) -> set:
    """Get diseases associated with this gene using Entrez and ClinVar."""
    logger.info(f"Fetching diseases for gene symbol {gene_symbol}")
    try:
        # Get ClinVar IDs for the gene
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "schema": "clinvar",
            "term": f"{gene_symbol}[gene]",
            "retmax": 100,
            "retmode": "json"
        }
        response = requests.get(esearch_url, params=params, timeout=10)
        response.raise_for_status()
        esearch_data = response.json()
        id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            logger.info(f"No ClinVar IDs found for gene {gene_symbol}.")
            return set()

        # Get diseases for these variants from ClinVar
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {
            "schema": "clinvar",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        response = requests.get(esummary_url, params=params, timeout=10)
        response.raise_for_status()
        diseases = []
        root = ET.fromstring(response.content)
        for doc in root.findall(".//DocumentSummary"):
            trait_set = doc.find(".//trait_set")
            if trait_set is not None:
                for trait in trait_set.findall(".//trait"):
                    trait_name = trait.find(".//trait_name")
                    if trait_name is not None and trait_name.text:
                        if trait_name.text not in ['not specified', 'not provided']:
                            diseases.append(trait_name.text)
        logger.info(f"Retrieved {len(diseases)} diseases for gene {gene_symbol}")
        return set(diseases)
    except requests.RequestException as e:
        logger.error(f"Network error while fetching diseases for {gene_symbol}: {e}")
        return set()
    except Exception as e:
        logger.error(f"Unexpected error while fetching diseases for {gene_symbol}: {e}")
        return set()


def filter_diseases(gd: GeneDisease, text: str):
    """Filter disease associations by presence in text."""
    logger.info(f"Filtering diseases for gene {gd.symbol}")
    if not gd.diseases:
        logger.info(f"No diseases to filter for gene {gd.symbol}.")
        return

    for d in gd.diseases:
        for line in text.splitlines():
            similarity = fuzz.ratio(line.lower(), d.lower())
            if similarity > 60:
                if d not in gd.flt_diseases:
                    gd.flt_diseases.append(d)
    logger.info(f"Filtered {len(gd.flt_diseases)} diseases for gene {gd.symbol}")


def add_metadata_to_gene(hgnc_id: str, text: str) -> Optional[GeneDisease]:
    """Get metadata for this HGNC gene and create GeneDisease object."""
    logger.info(f"Retrieving metadata for HGNC ID {hgnc_id}")
    try:
        mg = mygene.MyGeneInfo()
        gene_info = mg.query(hgnc_id, species='human', fields='symbol,alias,genomic_pos_hg19,genomic_pos')
        if not gene_info.get('hits'):
            logger.warning(f"No gene info found for HGNC ID {hgnc_id}.")
            return None
        gene_data = gene_info['hits'][0]
        gene_symbol = gene_data.get('symbol')
        if not gene_symbol:
            logger.error(f"Unable to get symbol for gene {hgnc_id}.")
            return None

        aliases = gene_data.get('alias', [])
        if isinstance(aliases, str):
            aliases = [aliases]
        elif not aliases:
            aliases = []

        hg38_coords = gene_data.get('genomic_pos', {})
        hg19_coords = gene_data.get('genomic_pos_hg19', {})
        if isinstance(hg38_coords, list):
            hg38_coords = hg38_coords[0] if hg38_coords else {}
        if isinstance(hg19_coords, list):
            hg19_coords = hg19_coords[0] if hg19_coords else {}
        hg38_str = (f"chr{hg38_coords.get('chr', 'N/A')}:{hg38_coords.get('start', 'N/A')}-"
                    f"{hg38_coords.get('end', 'N/A')}" if hg38_coords else 'N/A')
        hg19_str = (f"chr{hg19_coords.get('chr', 'N/A')}:{hg19_coords.get('start', 'N/A')}-"
                    f"{hg19_coords.get('end', 'N/A')}" if hg19_coords else 'N/A')

        diseases = get_diseases(gene_symbol)
        gene_disease = GeneDisease(
            symbol=gene_symbol,
            hgnc_id=hgnc_id,
            aliases=aliases,
            hg19=hg19_str,
            hg38=hg38_str,
            diseases=list(diseases)
        )
        filter_diseases(gene_disease, text)
        logger.info(
            f"Created GeneDisease object for {gene_symbol} with {len(gene_disease.flt_diseases)} filtered diseases")
        return gene_disease
    except Exception as e:
        logger.error(f"Error retrieving metadata for {hgnc_id}: {e}")
        return None


def extract_hgnc_gene_ids(text: str) -> set:
    """Extract HGNC gene IDs from text."""
    logger.info(f"Extracting HGNC gene IDs from text")
    gene_pattern = re.compile(r"(HGNC:\d+)")
    hgnc_gene_ids = gene_pattern.findall(text)
    logger.info(f"Extracted {len(hgnc_gene_ids)} HGNC gene IDs")
    return set(hgnc_gene_ids)


def del_file(fname: str):
    """Delete a file if it exists."""
    logger.info(f"Attempting to delete file {fname}")
    try:
        if os.path.exists(fname):
            os.remove(fname)
            logger.info(f"Deleted file {fname}.")
    except OSError as e:
        logger.error(f"Error deleting file {fname}: {e}")


def parse_pdf(fname: str = "pub.pdf"):
    """Parse PDF file for HGNC gene names, fetch metadata, and write to CSV files."""
    logger.info(f"Starting PDF parsing for {fname}")
    if not os.path.exists(fname):
        logger.error(f"PDF file {fname} does not exist.")
        raise FileNotFoundError(f"PDF file {fname} does not exist")

    output_dir = "output"
    if not os.path.exists(output_dir):
        logger.info(f"Creating output directory {output_dir}.")
        os.makedirs(output_dir)

    genes_csv = os.path.join(output_dir, "hgnc_gene.csv")
    aliases_csv = os.path.join(output_dir, "gene_aliases.csv")
    diseases_csv = os.path.join(output_dir, "gene_diseases.csv")

    del_file(genes_csv)
    del_file(aliases_csv)
    del_file(diseases_csv)

    text = read_pdf_file(fname)
    hgnc_gene_ids = extract_hgnc_gene_ids(text)

    try:
        with open(genes_csv, 'a', encoding='utf-8', newline='') as genes_file:
            with open(aliases_csv, 'a', encoding='utf-8', newline='') as aliases_file:
                with open(diseases_csv, 'a', encoding='utf-8', newline='') as diseases_file:
                    logger.info(f"Writing CSV files: {genes_csv}, {aliases_csv}, {diseases_csv}")

                    genes_writer = csv.writer(genes_file, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    aliases_writer = csv.writer(aliases_file, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    diseases_writer = csv.writer(diseases_file, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

                    # Write headers to CSV files
                    genes_writer.writerow(['hgnc_id', 'hgnc_gene_name', 'hg38', 'hg19'])
                    aliases_writer.writerow(['hgnc_id', 'alias'])
                    diseases_writer.writerow(['hgnc_id', 'disease'])

                    for hgnc_id in hgnc_gene_ids:
                        gene_disease = add_metadata_to_gene(hgnc_id, text)
                        if gene_disease:
                            # Write to hgnc_gene.csv
                            genes_writer.writerow([
                                gene_disease.hgnc_id,
                                gene_disease.symbol,
                                gene_disease.hg38,
                                gene_disease.hg19
                            ])
                            # Write to gene_aliases.csv
                            for alias in gene_disease.aliases or []:
                                aliases_writer.writerow([gene_disease.hgnc_id, alias])
                            # Write to gene_diseases.csv
                            for disease in gene_disease.flt_diseases:
                                diseases_writer.writerow([gene_disease.hgnc_id, disease])
                            logger.info(
                                f"Generated CSV entries for {hgnc_id} with {len(gene_disease.aliases or [])} aliases and {len(gene_disease.flt_diseases)} diseases")
        logger.info(f"Completed parsing PDF {fname} and writing CSVs")
    except Exception as e:
        logger.error(f"Error writing CSV files: {e}")
        raise
