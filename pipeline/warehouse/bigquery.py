"""BigQuery reads/writes. Tables are rebuilt from a full snapshot on every run."""

from google.cloud import bigquery

from config import ACTIVITIES_TABLE


def existing_laps(client: bigquery.Client) -> dict[str, list[dict]]:
    """Laps already stored, keyed by activity id, so they aren't re-fetched from Strava."""
    query = f"""
        SELECT activity_id, laps
        FROM `{ACTIVITIES_TABLE}`
        WHERE ARRAY_LENGTH(laps) > 0
    """
    return {
        row["activity_id"]: [dict(lap) for lap in row["laps"]]
        for row in client.query(query).result()
    }


def replace_table(client: bigquery.Client, table_id: str, rows: list[dict]) -> int:
    """Overwrite `table_id` with `rows` using a (free) load job, keeping the table's schema.

    A full snapshot instead of an incremental MERGE: the whole Strava history is three API
    pages, and rebuilding picks up edits (renamed activities, newly tagged races) and
    deletions that an incremental load would miss.
    """
    table = client.get_table(table_id)
    job_config = bigquery.LoadJobConfig(
        schema=table.schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    client.load_table_from_json(rows, table_id, job_config=job_config).result()
    return len(rows)
