import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd

from .tcga_requests import PYTCGA_BASE_DIRECTORY

TCGA_CLINICAL_URL = "https://tcga-data.nci.nih.gov/tcgafiles/ftp_auth/distro_ftpusers/anonymous/tumor/{}/bcr/biotab/clin/"

PATIENT_DATA_FILE_CODE = 'clinical_patient'
def request_clinical_data(disease_code,
                  cache=True,
                  block_size=1024):
    """Downloads TCGA public clinical data from the TCGA FTP site
    
    Parameters
    ----------
    disease_code : str
        TCGA disease type, i.e. 'LUAD', 'BLCA', 'BRCA' etc.
    cache : bool, optional
        Whether to cache the results of the request
    block_size : int, optional
        Block size for file downloads
    
    Returns
    -------
    patient_data_path : str
        Path to TCGA patient data file after downloading
    """
    # Create directory to save clinical data
    disease_code_dir = os.path.join(PYTCGA_BASE_DIRECTORY, disease_code)

    if cache and os.path.exists(disease_code_dir):
        patient_data_file = [f for f in os.listdir(disease_code_dir) if PATIENT_DATA_FILE_CODE in f]

        if len(patient_data_file) == 1:
            return os.path.join(disease_code_dir, patient_data_file[0])

    if not os.path.exists(disease_code_dir):
        os.mkdir(disease_code_dir)

    clinical_data_directory = TCGA_CLINICAL_URL.format(disease_code)
    r = requests.get(clinical_data_directory)
    soup = BeautifulSoup(r.content)

    # Retrieve list of files and filter to txt files
    file_links = [link.get('href') 
                    for link in soup.find_all('a')]
    clinical_files = [link for link in file_links if link.endswith('.txt')]

    # Download all clinical data files
    patient_data_path = None
    for clinical_file in clinical_files:
        output_file = os.path.join(disease_code_dir, clinical_file)
        logging.debug('Saving {} clinical data request to {}'.format(clinical_file, output_file))

        if PATIENT_DATA_FILE_CODE in output_file:
            patient_data_path = output_file

        with open(output_file, 'wb') as archive:
            archive_response = requests.get(clinical_data_directory + '/' + clinical_file, stream=True)

            for block in archive_response.iter_content(block_size):
                archive.write(block)

    return patient_data_path


def load_clinical_data(disease_code):
    """Downloads and loads the TCGA clinical data into a Pandas dataframe

    Parameters
    ----------
    disease_code : str
        TCGA disease type, i.e. 'LUAD', 'BLCA', 'BRCA' etc.

    Returns
    -------
    patient_data_df : Dataframe
        Returns a Pandas dataframe with the patient data
    """
    patient_data_path = request_clinical_data(disease_code, cache=True)

    patient_data_df = pd.read_csv(patient_data_path, sep='\t')

    return patient_data_df