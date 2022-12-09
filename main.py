from fileinput import filename
import sys
import json
import os
from pathlib import Path
import pytesseract
from dotenv import dotenv_values

from S3Bucket import S3Bucket
from ManageCMDInputs import CMDInput
from ImageGenerator import Pdf2Image
from MlPipeline import MlPipeline
from ConvertToPDF import Convert2PDF


# Load Environment Variables from .env file
DocumentparserDirLoc = Path(os.getcwd())
FrontendDirLoc = DocumentparserDirLoc.parent
environmentVarFileLoc = FrontendDirLoc.joinpath('.env')
ENVVAR = dotenv_values(environmentVarFileLoc)

pytesseract.pytesseract.tesseract_cmd = ENVVAR['TESSERACT_CMD']

# empty PDF Folder
pdfDirLoc = DocumentparserDirLoc.joinpath('TemporaryFiles').joinpath('PDF')
for file in os.listdir(pdfDirLoc):
    os.remove(pdfDirLoc.joinpath(file))

# Logging Function
def log(message):
    print(f'\n>>> {message} \n')


# Read PDF file name from Command Line
# log("Reading CMD Input")
cmdManage = CMDInput(sys.argv)
S3PdfFile = cmdManage.S3PdfFile
if(not S3PdfFile):
    raise Exception("SOLVE CMD ERROR")

# connect S3 Bucket
# log("Connecting to S3 bucket...")
S3BucketObj = S3Bucket(ENVVAR)

# downloading Pdf file from S3 Bucket
# log("Downloading PDF file...")
S3BucketObj.downloadPdfFile(S3PdfFile)
downloadedPdfLoc = S3BucketObj.downloadedPdfLoc

# converting file to proper PDF format
convertToPDFPbj = Convert2PDF(downloadedPdfLoc)

# Converting and saving the image
# log("Converting and saving the image")
pdf2Image = Pdf2Image(downloadedPdfLoc, ENVVAR)
convertedImageLoc = pdf2Image.convertedImageLoc

# upload to S3 Bucket
# log("Uploading the image to S3 Bucket...")
S3BucketObj.uploadImageFile(convertedImageLoc)

# ML Pipeline
# log("Running ML Models...")
mlPipeline = MlPipeline(convertedImageLoc)
jsonValue = mlPipeline.autoRun()
# jsonValue='{"Trade date": "05-Aug-2022", "Effective date": "05-Aug-2022", "Maturity date": "06-Jul-2032", "Payment date": "05-Aug-2022", "Net payment": "USD 1,350.01", "Reset date": "07-Nov-2022", "Start date": "05-Sep-2022", "End date": "07-Nov-2022", "Day count": "30", "Notional": "2,370,913.94", "Rate": "0.000000", "Spread": "0.000000", "All in rate": "0.000000", "Amount": "%|8,265.18", "Index": "TELE"}'
jsonValue = json.dumps(jsonValue)
jsonValue = jsonValue.replace("'", '"')

print(jsonValue, end='')

# saving JSON to local folder
# log("Saving JSON to local folder")
def extractFileName(S3PdfFile) -> str:
    fileName = S3PdfFile.split(".")[0]
    return fileName
createdJsonLoc = f'../Document_Parser/TemporaryFiles/JSON/{extractFileName(S3PdfFile)}.json'
with open(createdJsonLoc, "w") as file:
    json.dump(jsonValue, file)

# Uploading JSON file to S3 Bucket
# log("Uploading JSON to S3 Bucket...")
S3BucketObj.uploadJsonFile(createdJsonLoc)

os.remove(downloadedPdfLoc)
