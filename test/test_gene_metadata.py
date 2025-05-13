import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
from gene_metadata import read_pdf_file, extract_hgnc_gene_ids, add_metadata_to_gene, parse_pdf, GeneDisease

class TestGeneMetadata(unittest.TestCase):
    def setUp(self):
        # setup data for testing
        self.sample_text = """
        This is a test document containing HGNC:618 and HGNC:2204.
        Diseases mentioned include Alport syndrome and nephrotic syndrome.
        """
        self.sample_hgnc_ids = {"HGNC:618", "HGNC:2204"}
        self.output_dir = "output"
        self.genes_csv = os.path.join(self.output_dir, "hgnc_gene.csv")
        self.aliases_csv = os.path.join(self.output_dir, "gene_aliases.csv")
        self.diseases_csv = os.path.join(self.output_dir, "gene_diseases.csv")

    @patch("gene_metadata.os.path.exists")
    @patch("gene_metadata.PyPDF2.PdfReader")
    def test_read_pdf_file(self, mock_pdf_reader, mock_exists):
        '''
        test pdf read
        '''

        mock_exists.return_value = True
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text with HGNC:618"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        mock_open_file = mock_open()

        # invoke method for testing
        with patch("builtins.open", mock_open_file):
            result = read_pdf_file("test.pdf")

        # assert contents
        self.assertEqual(result, "Sample text with HGNC:618")
        mock_pdf_reader.assert_called_once_with(mock_open_file().__enter__())
        mock_page.extract_text.assert_called_once()


    def test_extract_hgnc_gene_ids(self):
        ''' test extracting hgnc_ids from text '''

        result = extract_hgnc_gene_ids(self.sample_text)

        self.assertEqual(result, self.sample_hgnc_ids)

    @patch("gene_metadata.mygene.MyGeneInfo")
    @patch("gene_metadata.get_diseases")
    def test_add_metadata_to_gene(self, mock_get_diseases, mock_mygene):
        ''' test gene metadata '''

        mock_mygene_instance = MagicMock()
        mock_mygene.return_value = mock_mygene_instance
        mock_mygene_instance.query.return_value = {
            "hits": [{
                "symbol": "APOL1",
                "alias": ["APOL2", "APOL3"],
                "genomic_pos": {"chr": "22", "start": 36661906, "end": 36676353},
                "genomic_pos_hg19": {"chr": "22", "start": 36649329, "end": 36663776}
            }]
        }
        mock_get_diseases.return_value = {"Alport syndrome", "Nephrotic syndrome"}
        hgnc_id = "HGNC:618"
        text = "Alport syndrome is mentioned here."

        # invoke method for testing
        result = add_metadata_to_gene(hgnc_id, text)

        # run assertions
        self.assertIsInstance(result, GeneDisease)
        self.assertEqual(result.symbol, "APOL1")
        self.assertEqual(result.hgnc_id, hgnc_id)
        self.assertEqual(result.aliases, ["APOL2", "APOL3"])
        self.assertEqual(result.hg38, "chr22:36661906-36676353")
        self.assertEqual(result.hg19, "chr22:36649329-36663776")
        self.assertEqual(result.flt_diseases, ["Alport syndrome"])


    @patch("gene_metadata.read_pdf_file")
    @patch("gene_metadata.extract_hgnc_gene_ids")
    @patch("gene_metadata.add_metadata_to_gene")
    @patch("gene_metadata.os.path.exists")
    @patch("gene_metadata.os.makedirs")
    @patch("gene_metadata.del_file")
    def test_parse_pdf(self, mock_del_file, mock_makedirs, mock_exists, mock_add_metadata, mock_extract_ids, mock_read_pdf):
        ''' test parse pdf'''

        mock_exists.side_effect = [True, False]  # PDF exists, output dir does not
        mock_read_pdf.return_value = self.sample_text
        mock_extract_ids.return_value = self.sample_hgnc_ids
        mock_add_metadata.return_value = GeneDisease(
            symbol="APOL1",
            hgnc_id="HGNC:618",
            aliases=["APOL2", "APOL3"],
            hg38="chr22:36661906-36676353",
            hg19="chr22:36649329-36663776",
            flt_diseases=["Alport syndrome"]
        )
        mock_open_files = mock_open()

        with patch("builtins.open", mock_open_files), patch("gene_metadata.csv.writer") as mock_csv_writer:
            mock_writer_instance = MagicMock()
            mock_csv_writer.return_value = mock_writer_instance

            # invoke method for testing
            parse_pdf("test.pdf")

            # Assert
            mock_read_pdf.assert_called_once_with("test.pdf")
            mock_extract_ids.assert_called_once_with(self.sample_text)
            mock_makedirs.assert_called_once_with(self.output_dir)
            self.assertEqual(mock_del_file.call_count, 3)  # Called for each CSV
            mock_writer_instance.writerow.assert_any_call(['hgnc_id', 'hgnc_gene_name', 'hg38', 'hg19'])
            mock_writer_instance.writerow.assert_any_call(['hgnc_id', 'alias'])
            mock_writer_instance.writerow.assert_any_call(['hgnc_id', 'disease'])
            mock_writer_instance.writerow.assert_any_call(['HGNC:618', 'APOL1', 'chr22:36661906-36676353', 'chr22:36649329-36663776'])
            mock_writer_instance.writerow.assert_any_call(['HGNC:618', 'APOL2'])
            mock_writer_instance.writerow.assert_any_call(['HGNC:618', 'APOL3'])
            mock_writer_instance.writerow.assert_any_call(['HGNC:618', 'Alport syndrome'])

    # TODO test when pdf file is missing

if __name__ == '__main__':
    unittest.main()