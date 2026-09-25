-- ZyroTrace AI backend — Phase 1 schema.
-- Run this once, in a NEW, separate Supabase project (not the old "anpr"
-- project the deployed Netlify dashboard uses). Keeping them separate means
-- nothing here can ever collide with, or get mistaken for, the old prototype's
-- tables.
--
-- reid_embeddings, evidence_assets, users, audit_logs are later phases
-- (4, 3, 7) and aren't created here.
--
-- Every table has RLS enabled with NO policies. Unlike the old prototype,
-- the browser never talks to this database directly — only the FastAPI
-- backend does, over a direct Postgres connection that bypasses RLS. So
-- "no policies" here is correct and intentional, not a gap to fill in later.

create table cameras (
    id                text primary key,
    name              text        not null,
    latitude          float8      not null,
    longitude         float8      not null,
    location_label    text,
    road_segment_id   text,
    is_active         boolean     not null default true,
    created_at        timestamptz not null default now()
);

create table processing_jobs (
    id                bigserial primary key,
    camera_id         text        not null references cameras(id),
    source_file_key   text        not null,
    status            text        not null default 'queued'
                                   check (status in ('queued', 'processing', 'completed', 'failed')),
    progress          real        not null default 0,
    started_at        timestamptz,
    completed_at      timestamptz,
    error_message     text,
    created_by        text,
    created_at        timestamptz not null default now()
);
create index on processing_jobs (camera_id);
create index on processing_jobs (status);

create table vehicle_tracks (
    id                bigserial primary key,
    job_id            bigint      not null references processing_jobs(id) on delete cascade,
    camera_id         text        not null references cameras(id),
    tracker_key       text        not null,
    first_seen_at     timestamptz,
    last_seen_at      timestamptz,
    vehicle_type      text,
    best_crop_key     text,
    created_at        timestamptz not null default now()
);
create index on vehicle_tracks (job_id);

create table vehicle_observations (
    id                bigserial primary key,
    track_id          bigint      not null references vehicle_tracks(id) on delete cascade,
    job_id            bigint      not null references processing_jobs(id) on delete cascade,
    camera_id         text        not null references cameras(id),
    observed_at       timestamptz not null,
    bbox              jsonb,
    vehicle_type      text,
    confidence        real,
    crop_key          text,
    created_at        timestamptz not null default now()
);
create index on vehicle_observations (track_id);
create index on vehicle_observations (camera_id, observed_at);

create table plate_observations (
    id                  bigserial primary key,
    observation_id      bigint      not null references vehicle_observations(id) on delete cascade,
    raw_text            text,
    normalized_text     text,
    ocr_confidence      real,
    detector_confidence real,
    plate_crop_key      text,
    created_at          timestamptz not null default now()
);
create index on plate_observations (normalized_text);

create table traffic_aggregates (
    id                bigserial primary key,
    camera_id         text        references cameras(id),
    segment_id        text,
    window_start      timestamptz not null,
    window_end        timestamptz not null,
    vehicle_count     integer,
    density_metric    real,
    average_speed     real,
    congestion_level  text,
    computed_at       timestamptz not null default now()
);
create index on traffic_aggregates (camera_id, window_start);

alter table cameras                enable row level security;
alter table processing_jobs        enable row level security;
alter table vehicle_tracks         enable row level security;
alter table vehicle_observations   enable row level security;
alter table plate_observations     enable row level security;
alter table traffic_aggregates     enable row level security;
