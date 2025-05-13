import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
from main import wait_for_db, populate_db, main
from psycopg2 import OperationalError

class TestMain(unittest.TestCase):
    def setUp(self):
        # Sample database configuration
        self.db_config = {
            'host': 'mydb',
            'port': '5432',
            'database': 'MYDB',
            'user': 'postgres',
            'password': 'postgres'
        }
        # Sample CSV file paths
        self.output_dir = "/app/output"
        self.csv_files = [
            os.path.join(self.output_dir, 'hgnc_gene.csv'),
            os.path.join(self.output_dir, 'gene_diseases.csv'),
            os.path.join(self.output_dir, 'gene_aliases.csv')
        ]
        # Sample CSV content
        self.sample_csv_content = [
            "hgnc_id,hgnc_gene_name,hg38,hg19\nHGNC:618,APOL1,chr22:36661906-36676353,chr22:36649329-36663776\n",
            "hgnc_id,disease\nHGNC:618,Alport syndrome\n",
            "hgnc_id,alias\nHGNC:618,APOL2\nHGNC:618,APOL3\n"
        ]

    @patch("main.psycopg2.connect")
    @patch("main.time.sleep")
    def test_wait_for_db_success(self, mock_sleep, mock_connect):
        # mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # invoke method for testing
        result = wait_for_db(**self.db_config, max_attempts=3, delay=1)

        # assertions
        self.assertTrue(result)
        mock_connect.assert_called_once_with(**self.db_config)
        mock_conn.close.assert_called_once()


    @patch("main.wait_for_db")
    @patch("main.parse_pdf")
    @patch("main.populate_db")
    @patch("main.os.getenv")
    def test_main(self, mock_getenv, mock_populate_db, mock_parse_pdf, mock_wait_for_db):

        mock_getenv.side_effect = lambda key, default: self.db_config.get(key.lower(), default)
        mock_wait_for_db.return_value = True

        # invoke method for testing
        main()

        # assertions
        mock_wait_for_db.assert_called_once_with(**self.db_config)
        mock_parse_pdf.assert_called_once()
        mock_populate_db.assert_called_once()


if __name__ == '__main__':
    unittest.main()