import asyncpg


async def search_plates(conn: asyncpg.Connection, query: str, exact: bool = False, limit: int = 20) -> list[dict]:
    if exact:
        rows = await conn.fetch(
            """
            select * from vehicle_tracks vt
            where exists (
                select 1 from plate_observations po
                where po.observation_id in (select id from vehicle_observations where track_id = vt.id)
                and po.normalized_text = $1
            )
            order by first_seen_at desc
            limit $2
            """,
            query, limit
        )
    else:
        rows = await conn.fetch(
            """
            select * from vehicle_tracks vt
            where exists (
                select 1 from plate_observations po
                where po.observation_id in (select id from vehicle_observations where track_id = vt.id)
                and po.normalized_text ilike '%' || $1 || '%'
            )
            order by first_seen_at desc
            limit $2
            """,
            query, limit
        )
    return [dict(r) for r in rows]


async def get_vehicle_history(conn: asyncpg.Connection, track_id: int) -> list[dict]:
    rows = await conn.fetch(
        """
        select po.*, vo.observed_at, vo.camera_id 
        from plate_observations po
        join vehicle_observations vo on vo.id = po.observation_id
        where vo.track_id = $1
        order by vo.observed_at asc
        """,
        track_id
    )
    return [dict(r) for r in rows]


async def get_vehicle_assets(conn: asyncpg.Connection, track_id: int) -> list[dict]:
    rows = await conn.fetch(
        "select * from evidence_assets where track_id = $1 order by timestamp asc",
        track_id
    )
    return [dict(r) for r in rows]


async def save_embedding(
    conn: asyncpg.Connection,
    track_id: int,
    asset_id: int,
    model_name: str,
    embedding: list[float],
    quality_score: float,
    is_primary: bool
) -> dict:
    embedding_str = str(embedding)
    row = await conn.fetchrow(
        """
        insert into reid_embeddings (track_id, asset_id, model_name, embedding, quality_score, is_primary)
        values ($1, $2, $3, $4::vector, $5, $6)
        returning id, created_at
        """,
        track_id, asset_id, model_name, embedding_str, quality_score, is_primary
    )
    return dict(row)

async def get_primary_embedding(conn: asyncpg.Connection, track_id: int) -> list[float]:
    row = await conn.fetchrow(
        """
        select embedding 
        from reid_embeddings 
        where track_id = $1 
        order by quality_score desc 
        limit 1
        """,
        track_id
    )
    if not row:
        return None
    # pgvector returns a string in asyncpg unless a codec is registered, parse it
    emb_str = row['embedding']
    if isinstance(emb_str, str):
        # Format is usually '[0.1,0.2,...]'
        clean_str = emb_str.strip('[]')
        return [float(x) for x in clean_str.split(',')]
    return list(emb_str)


async def search_similar_vehicles(conn: asyncpg.Connection, query_embedding: list[float], limit: int = 10) -> list[dict]:
    embedding_str = str(query_embedding)
    rows = await conn.fetch(
        """
        select 
            track_id, 
            min(embedding <=> $1::vector) as distance
        from reid_embeddings
        group by track_id
        order by distance asc
        limit $2
        """,
        embedding_str, limit
    )
    return [dict(r) for r in rows]
