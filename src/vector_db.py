# from datetime import datetime
import os
from typing import Any, Dict, List, Optional

import duckdb

# Create directories for database storage if they don't exist
if not os.path.exists(os.path.join("assets", "db")):
    os.makedirs(os.path.join("assets", "db"))
if not os.path.exists(os.path.join("assets", "db", "temp")):
    os.makedirs(os.path.join("assets", "db", "temp"))
if not os.path.exists(os.path.join("assets", "db", "snapshot")):
    os.makedirs(os.path.join("assets", "db", "snapshot"))


class VectorStore:
    def __init__(self) -> None:
        # Set the path for the persistent database
        self.persistant_path = os.path.join("assets", "db", "embeddings.db")

        # Initialize configuration settings from environment variables
        self.config = {
            "memory_limit": os.getenv("memory_limit"),
            "threads": int(os.getenv("threads")),
            "temp_directory": os.path.join("assets", "db", "temp"),
            "user": os.getenv("user"),
            "password": os.getenv("password"),
        }

        # Establish a connection to the database with the specified configuration
        self.conn = duckdb.connect(config=self.config)

        # Install and load the vector search extension
        self.conn.install_extension("vss")
        self.conn.load_extension("vss")

        # Set the embedding size from an environment variable
        self.embedding_size = int(os.getenv("embedding_size"))

        # Prepare the database by creating tables and indices
        self._prepare_database()

    def __del__(self) -> None:
        # Save the current state of the database to a CSV file before closing the connection
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
        # Create a table for embeddings with a primary key, text column, embedding column, metadata column, and creation timestamp
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
        # Insert a new embedding into the database with the provided text, embedding, metadata, and current timestamp
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
        # Convert the embedding list to a string format compatible with SQL
        embedding_str = ",".join(map(str, embedding))

        # Construct a query to search for the top-k nearest neighbors using cosine similarity
        query = f"""
        SELECT 
            text,
            array_distance(
                embedding, ARRAY[{embedding_str}]::FLOAT[{self.embedding_size}]
            ) AS distance_score
        FROM embeddings
        ORDER BY array_distance(
            embedding, ARRAY[{embedding_str}]::FLOAT[{self.embedding_size}]
        )
        LIMIT {top_k}; 
        """

        # Execute the query and return the search results as a DataFrame
        search_results = self.conn.execute(query).fetch_df()
        return search_results

    def refresh(self) -> None:
        # Save the current state of the database to a CSV file
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

        # Delete all embeddings from the database
        self.conn.execute(
            """
            DELETE FROM embeddings;
        """
        )
        self.conn.commit()
