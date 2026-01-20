from ingestion_engine.storage.postgres import get_session
from ingestion_engine.storage.services.tenderservice import TenderService
import json
from pathlib import Path
from .utils.file_manager_dir import tender_get_storage_dir
from .storage.services import document_service
import os
folder = Path("meta_data")
json_files = list(folder.glob("*.json"))

# with open("meta_data\Tender_data_2026-01-19_16-45-06.json") as f:
#     data = json.load(f)


records = None

# session = get_session()

if json_files:
    for json_file in json_files:
        if "Tender_data" in json_file.name:
            # print(json_file.name)
            with open(json_file,"rb") as f:
                records = json.load(f)
        if "Tenders_filepath" in json_file.name:
            # print(json_file.name)
            with open(json_file ,"rb") as f1:
                filerecords = json.load(f1)
tender_id_map = {}

with get_session() as session:
    if records:
        for record in records:
            # print(record)
            tender = TenderService.create_from_json(session, record)
            tender_id_map[tender.tender_uid] = tender.id
        

    if filerecords:
        # print(tender_id_map)
        for filerecord in filerecords:
            for title, path in filerecord.items():
                    
                    # if not path.is_file():
                    #     continue

                    # Skip Windows temp/lock files
                    # if path.name.startswith("~$"):
                    #     continue
                    print(f"path {path}")

                    document_service.DocumentService.register_document(
                        session=session,
                        tender_id= int(tender_id_map[title]),
                        file_path=(path)
                    )
                # if title and path:
                #     convertedfile =  Path(path)
                #     # print(f"convertedfile {convertedfile}")
                #     # if convertedfile.is_file():
                #     # file_path = convertedfile.parent()
                #     absolute_directory = convertedfile.parent.resolve()
                #     # print(f'file_path {file_path} path {path}')
                #     actualpath = os.path.dirname(path)
                    
                #     print(f'path {path} {actualpath}')
                #     document_service.DocumentService.register_document(session=session, tender_id=title, file_path=path)
                    

       