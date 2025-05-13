-- SQL query to retrieve HGNC gene names with aliases
select hg.hgnc_gene_name, ga.alias from gene_aliases ga join hgnc_gene hg on hg.hgnc_id =ga.hgnc_id
order by ga.hgnc_id ;


