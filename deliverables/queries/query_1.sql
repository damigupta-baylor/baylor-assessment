-- SQL query to retrieve HGNC IDs with connected diseases
select hg.hgnc_id, gd.disease
from hgnc_gene hg join gene_diseases gd ON hg.hgnc_id =gd.hgnc_id
order by hg.hgnc_id ;
