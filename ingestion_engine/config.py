from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings , SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    
    # __file__ = Path.cwd()
    # path =  __file__.parent
    # print(path)

    # model_config = SettingsConfigDict(env_file=('.env', '.env.prod'), extra='ignore')

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # always finds .env regardless of where you run python from
        extra="ignore",
    )

    postgres_url : PostgresDsn
    qdrant_host : str
    qdrant_port : int
    ollama_base_url : str  
    ollama_model : str 

    #windows only
    tesseract_cmd : Optional[Path] = None
    poppler_path : Optional[Path] = None

    embedding_model : str = 'BAAI/bge-small-en-v1.5'
    embedding_dim : int = 384
    collection_name : str = 'tenders'
    chunk_size : int = 400
    chunk_overlap : int = 50
    top_k : int = 8
    score_threshold : float = 0.4
    log_level : str = "INFO"



settings = Settings()
            