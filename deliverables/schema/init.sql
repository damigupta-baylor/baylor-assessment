DROP TABLE IF EXISTS hgnc_gene;
DROP TABLE IF EXISTS gene_aliases;
DROP TABLE IF EXISTS gene_diseases;

CREATE TABLE hgnc_gene
(
    hgnc_id VARCHAR(255) PRIMARY KEY,
    hgnc_gene_name VARCHAR(255),
    hg38 VARCHAR(255),
    hg19 VARCHAR(255)
);
CREATE TABLE gene_aliases
(
    hgnc_id VARCHAR(255),
    alias VARCHAR(255),
    PRIMARY KEY(hgnc_id,alias),
    CONSTRAINT fk_gene_alias_hgnc_id FOREIGN KEY (hgnc_id)
    REFERENCES hgnc_gene(hgnc_id)

);
CREATE TABLE gene_diseases
(
    hgnc_id VARCHAR(255),
    disease VARCHAR(255),
    PRIMARY KEY(hgnc_id,disease),
    CONSTRAINT fk_gene_disease_hgnc_id FOREIGN KEY (hgnc_id)
    REFERENCES hgnc_gene(hgnc_id)
);

