-- ============================================================================
-- ANPR Prototype — Supabase schema
-- Run this in the Supabase dashboard: SQL Editor -> New query -> Run
-- ============================================================================

drop table if exists detections cascade;
drop table if exists cameras cascade;

-- ---------------------------------------------------------------- cameras
-- Three hardcoded nodes for the prototype. Coordinates drive the Leaflet
-- route; video_url points at the browser-playable H.264 re-encode.
create table cameras (
    id           text primary key,          -- 'Camera_1' — matches vehicle_logs.csv
    name         text        not null,
    city         text        not null default 'Chennai',
    latitude     float8      not null,
    longitude    float8      not null,
    video_url    text,                      -- public URL of cam1.mp4 etc.
    recorded_at  timestamptz not null,      -- wall-clock start of the footage
    created_at   timestamptz not null default now()
);

-- ---------------------------------------------------------------- detections
-- One row per tracklet, mirroring outputs/vehicle_logs.csv exactly.
--
-- entry/exit come in two forms on purpose:
--   *_timestamp  — real wall-clock, for cross-camera trajectory ordering
--   *_offset_sec — seconds into the video file, for video.currentTime seeking
-- The offsets are what let the player jump straight to the moment a vehicle
-- enters frame; a single timestamp column cannot express that.
create table detections (
    id                bigserial primary key,
    camera_id         text        not null references cameras(id) on delete cascade,
    track_id          integer     not null,
    plate_number      text        not null,   -- 'UNKNOWN' rows are kept: they
    confidence        real        not null,   -- are the vehicle-count analytics
    entry_timestamp   timestamptz not null,
    exit_timestamp    timestamptz not null,
    entry_offset_sec  real        not null,
    exit_offset_sec   real        not null,
    created_at        timestamptz not null default now()
);

-- Search by plate is the hot path; the camera+time index serves analytics.
create index detections_plate_idx      on detections (plate_number);
create index detections_camera_time_idx on detections (camera_id, entry_timestamp);
-- Partial index: every plate query filters out the unreadable rows first.
create index detections_named_idx on detections (plate_number)
    where plate_number <> 'UNKNOWN';

-- ---------------------------------------------------------------- security
-- The frontend ships the *publishable* key, which is safe to expose ONLY
-- because RLS is on and the policies below grant read and nothing else.
-- Writes go through the Python uploader using the secret key, server-side.
alter table cameras    enable row level security;
alter table detections enable row level security;

create policy "public read cameras"
    on cameras for select using (true);

create policy "public read detections"
    on detections for select using (true);

-- ---------------------------------------------------------------- analytics
-- Per-camera rollup for the "Urban Traffic Analytics" panel. A view keeps the
-- counting rules in one place instead of duplicating them in JS.
-- security_invoker: run the view with the *querying* user's permissions, not the
-- creator's. Without it the view silently bypasses RLS, which Supabase's linter
-- flags as CRITICAL — harmless while both tables are public-read, but wrong the
-- moment any policy tightens.
create or replace view camera_stats
with (security_invoker = true) as
select
    c.id                                                          as camera_id,
    c.name,
    c.city,
    count(d.id)                                                   as total_vehicles,
    count(d.id) filter (where d.plate_number <> 'UNKNOWN')        as plates_read,
    count(distinct d.plate_number)
        filter (where d.plate_number <> 'UNKNOWN')                as unique_plates,
    round(avg(d.confidence) filter (where d.confidence > 0)::numeric, 1)
                                                                  as avg_confidence,
    min(d.entry_timestamp)                                        as first_seen,
    max(d.exit_timestamp)                                         as last_seen,
    -- Footage duration in seconds, from the video offsets.
    round(max(d.exit_offset_sec)::numeric, 1)                     as duration_sec
from cameras c
left join detections d on d.camera_id = c.id
group by c.id, c.name, c.city;
