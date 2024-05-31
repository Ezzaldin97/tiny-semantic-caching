# from datetime import datetime
import os
from typing import Any, Dict, List, Optional

import duckdb

if not os.path.exists(os.path.join("assets", "db")):
    os.makedirs(os.path.join("assets", "db"))
if not os.path.exists(os.path.join("assets", "db", "temp")):
    os.makedirs(os.path.join("assets", "db", "temp"))
if not os.path.exists(os.path.join("assets", "db", "snapshot")):
    os.makedirs(os.path.join("assets", "db", "snapshot"))


class VectorStore:
    def __init__(self) -> None:
        self.persistant_path = os.path.join("assets", "db", "embeddings.db")
        self.config = {
            "memory_limit": os.getenv("memory_limit"),
            "threads": int(os.getenv("threads")),
            "temp_directory": os.path.join("assets", "db", "temp"),
            "user": os.getenv("user"),
            "password": os.getenv("password"),
        }
        self.conn = duckdb.connect(config=self.config)
        ### install vector search extensions
        self.conn.install_extension("vss")
        self.conn.load_extension("vss")
        self.embedding_size = int(os.getenv("embedding_size"))
        self._prepare_database()

    def __del__(self) -> None:
        self.conn.from_query(
            query="""
            SELECT * FROM embeddings;
        """
        ).to_csv(
            file_name=os.path.join(
                "assets",
                "db",
                "snapshot",
                "current.csv",
                # f"{datetime.strftime(datetime.now(),format='%Y%m%d-%H%M%S')}.csv"
            )
        )
        self.conn.close()

    def _prepare_database(self) -> None:
        self.conn.sql(
            f"""
            CREATE TABLE IF NOT EXISTS embeddings(
                embedding_id UUID PRIMARY KEY,
                text VARCHAR NOT NULL,
                embedding FLOAT[{self.embedding_size}] NOT NULL,
                metadata STRUCT(file VARCHAR, chunk INTEGER),
                creation_timestamp TIMESTAMP NOT NULL,
            );
            CREATE INDEX embedding_index 
            ON embeddings 
            USING HNSW (embedding)
            WITH (
                metric = 'cosine'
            );
        """
        )

    def insert(
        self,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO embeddings
            VALUES(
                uuid(),
                $text,
                $embedding,
                $metadata,
                CURRENT_TIMESTAMP
            )
        """,
            {
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
            },
        )
        self.conn.commit()

    def search(self, embedding: List[float], top_k: int = 3):
        # Convert the embedding list to a format compatible with SQL (string of numbers)
        ### use cosine similarity
        embedding_str = ",".join(map(str, embedding))
        query = f"""
        SELECT 
            text,
            array_cosine_similarity(
                embedding, ARRAY[{embedding_str}]::FLOAT[{self.embedding_size}]
            ) AS distance_score
        FROM embeddings
        ORDER BY array_cosine_similarity(
            embedding, ARRAY[{embedding_str}]::FLOAT[{self.embedding_size}]
        )
        LIMIT {top_k}; 
        """
        search_results = self.conn.execute(query).fetch_df()
        return search_results

    def refresh(self) -> None:
        self.conn.from_query(
            query="""
            SELECT * FROM embeddings;
        """
        ).to_csv(
            file_name=os.path.join(
                "assets",
                "db",
                "snapshot",
                "current.csv",
                # f"{datetime.strftime(datetime.now(),format='%Y%m%d-%H%M%S')}.csv"
            )
        )
        self.conn.execute(
            """
            DELETE FROM embeddings;
        """
        )
        self.conn.commit()
