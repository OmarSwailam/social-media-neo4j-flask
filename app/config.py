from neomodel import config as neomodelConfig
from datetime import timedelta

class Config:
    """
    General Configuration for the application.
    """

    #### General Configuration
    ENABLE_CORS = True
    SWAGGER_UI_DOC_EXPANSION = "list"
    SECRET_KEY = "d!-*k_6)0_xwm1x=j2r+^8f0rae8x8w-)k&=_+&_=*9hvzlcib"

    #### Neo4j Configuration
    NEO4J_URI = "neo4j://neo4j-db:7687"
    NEO4J_USERNAME="username"
    NEO4J_PASSWORD="password"

    #### Neomodel
    neomodelConfig.DATABASE_URL = "bolt://neo4j:password@neo4j-db:7687"
    neomodelConfig.AUTO_INSTALL_LABELS = True

    #### JWT Configuration
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(60))
