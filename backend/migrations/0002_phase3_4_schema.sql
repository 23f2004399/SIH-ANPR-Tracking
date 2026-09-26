-- Phase 3 and Phase 4 schema extensions

create extension if not exists vector;
create extension if not exists pg_trgm;

create table if not exists evidence_assets (
    id                bigserial primary key,
    track_id          bigint      not null references vehicle_tracks(id) on delete cascade,
    camera_id         text        not null references cameras(id),
    asset_type        text        not null check (asset_type in ('VEHICLE_BEST', 'PLATE_BEST', 'ROI_BEST', 'PLATE_CROP')),
    storage_key       text        not null,
    frame_number      integer,
    timestamp         timestamptz,
    quality_score     real,
    sharpness_score   real,
    created_at        timestamptz not null default now()
);
create index if not exists evidence_assets_track_id_idx on evidence_assets (track_id);

create table if not exists reid_embeddings (
    id                bigserial primary key,
    track_id          bigint      not null references vehicle_tracks(id) on delete cascade,
    asset_id          bigint      references evidence_assets(id) on delete set null,
    model_name        text,
    embedding         vector(512),
    quality_score     real,
    is_primary        boolean     default false,
    created_at        timestamptz not null default now()
);
create index if not exists reid_embeddings_track_id_idx on reid_embeddings (track_id);
