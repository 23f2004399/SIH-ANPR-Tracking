#!/usr/bin/env python3
"""
City-Wide Multi-Camera ANPR Trajectory Tracking and Vehicle Analytics Pipeline
        # Check whether to save vehicle crop and embedding
        should_save_vehicle = (
            track_data.get("best_vehicle_crop") is not None and
            (is_confident or self.args.save_all_crops) and
            track_duration >= self.args.min_track_frames
        )

        emb_path_str = ""
        if should_save_vehicle:
            # 1. Save single best vehicle crop (chosen by ROI size, sharpness, and boundaries)
            v_crop = track_data["best_vehicle_crop"]
            v_crop_path = os.path.join(self.vehicle_crops_dir, f"{camera_id}_track_{track_id}.jpg")
            cv2.imwrite(v_crop_path, v_crop)

            # 2. Re-ID Embedding Generation (512-d normalized vector)
            embedding = self.reid_model.get_embedding(v_crop)
            emb_path = os.path.join(self.vehicle_crops_dir, f"{camera_id}_track_{track_id}_emb.npy")
            np.save(emb_path, np.array(embedding))
            emb_path_str = emb_path

            # 3. Auto-generate 6-7 sample crops for Re-ID accuracy testing
            if getattr(self.args, "save_samples", True):
                raw_samples = track_data.get("sample_crops", [])
                if raw_samples:
                    if len(raw_samples) > 7:
                        indices = np.linspace(0, len(raw_samples) - 1, num=7, dtype=int)
                        chosen_samples = [raw_samples[i] for i in indices]
                    else:
                        chosen_samples = raw_samples

                    track_sample_dir = os.path.join(self.sample_crops_dir, f"{camera_id}_track_{track_id}")
                    os.makedirs(track_sample_dir, exist_ok=True)
                    for s_idx, s_crop in enumerate(chosen_samples, start=1):
                        s_path = os.path.join(track_sample_dir, f"sample_{s_idx:02d}.jpg")
                        cv2.imwrite(s_path, s_crop)

        # Save single best plate crop if confident
        if is_confident and track_data.get("best_plate_crop") is not None:
            p_crop_path = os.path.join(self.plate_crops_dir, f"{camera_id}_track_{track_id}.jpg")
            cv2.imwrite(p_crop_path, track_data["best_plate_crop"])

        with open(self.csv_log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                camera_id,
                track_id,
                entry_ts,
                exit_ts,
                best_plate,
                f"{avg_conf:.2f}",
                f"{entry_sec:.2f}",
                f"{exit_sec:.2f}",
                emb_path_str
            ])

        if emb_path_str:
            logger.info(
                f"[{camera_id}] 🏁 Track #{track_id} EXITED | "
                f"Plate: '{best_plate}' (Avg Conf: {avg_conf:.1f}%) | "
                f"Time: {entry_dt:%H:%M:%S} -> {exit_dt:%H:%M:%S} | 💾 Saved Best Crop + Embedding"
            )
        else:
            logger.info(
                f"[{camera_id}] 🏁 Track #{track_id} EXITED | "
                f"Plate: '{best_plate}' (Avg Conf: {avg_conf:.1f}%) | "
                f"Time: {entry_dt:%H:%M:%S} -> {exit_dt:%H:%M:%S} | ⏭️ Skipped crop saving"
            )

        return True

    # --------------------------------------------------------------------------
    # Video Stream Processing Routine
    # --------------------------------------------------------------------------
    def process_video_stream(self, video_path: str, camera_id: str):
        """
        Process a video feed sequentially with full-frame tracking & detailed terminal telemetry.
        """
        if not os.path.exists(video_path):
            logger.error(f"[{camera_id}] Video file not found: {video_path}")
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"[{camera_id}] Failed to open video: {video_path}")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        input_filename = os.path.basename(video_path)
        input_stem = os.path.splitext(input_filename)[0]
        out_video_name = f"annotated_{input_stem}.mp4"
        out_video_path = os.path.join(self.args.output_dir, out_video_name)

        logger.info(f"\n" + "="*70)
        logger.info(f"▶ STARTING FEED: {camera_id} | Input: '{input_filename}'")
        logger.info(f"  Resolution: {frame_width}x{frame_height} @ {fps:.1f} FPS | Total Frames: {total_frames}")
        logger.info(f"  Target Output Video: '{out_video_path}'")
        logger.info("="*70)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = None
        if not self.args.no_video:
            video_writer = cv2.VideoWriter(out_video_path, fourcc, fps, (frame_width, frame_height))

        active_tracks: Dict[int, dict] = {}
        frame_idx = 0
        logged_count = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                if self.args.max_frames and frame_idx >= self.args.max_frames:
                    logger.info(f"[{camera_id}] Reached --max_frames={self.args.max_frames}, stopping early.")
                    break

                frame_idx += 1
                current_frame_plates = []

                # Step 1: Vehicle Detection & Tracking with ByteTrack (No deprecated 'half' argument)
                track_results = self.vehicle_model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    classes=self.vehicle_classes,
                    conf=self.args.conf_thresh,
                    device=self.device,
                    verbose=False
                )

                if track_results and track_results[0].boxes and track_results[0].boxes.id is not None:
                    boxes = track_results[0].boxes.xyxy.cpu().numpy()
                    track_ids = track_results[0].boxes.id.int().cpu().numpy()
                    confs = track_results[0].boxes.conf.cpu().numpy()

                    for box, track_id, v_conf in zip(boxes, track_ids, confs):
                        track_id = int(track_id)

                        vx1, vy1, vx2, vy2 = map(int, box)
                        vx1, vy1 = max(0, vx1), max(0, vy1)
                        vx2, vy2 = min(frame_width, vx2), min(frame_height, vy2)

                        vehicle_crop = frame[vy1:vy2, vx1:vx2]

                        # Compute ROI quality (sharpness, size, boundary distance)
                        v_score, v_sharpness = compute_crop_quality(
                            crop=vehicle_crop,
                            bbox=(vx1, vy1, vx2, vy2),
                            frame_width=frame_width,
                            frame_height=frame_height,
                            conf=float(v_conf)
                        )

                        # New vehicle entry
                        if track_id not in active_tracks:
                            active_tracks[track_id] = {
                                "entry_frame": frame_idx,
                                "last_seen_frame": frame_idx,
                                "last_ocr_frame": -999,
                                "ocr_reads": [],
                                "plate_bbox_found": False,
                                "best_plate": "DETECTING...",
                                "best_conf": 0.0,
                                "bbox": (vx1, vy1, vx2, vy2),
                                "best_vehicle_crop": vehicle_crop.copy() if vehicle_crop.size > 0 else None,
                                "best_vehicle_score": v_score,
                                "best_vehicle_sharpness": v_sharpness,
                                "sample_crops": [vehicle_crop.copy()] if (vehicle_crop.size > 0 and v_score > 0) else [],
                                "last_sample_frame": frame_idx,
                                "best_plate_crop": None,
                                "best_plate_area": 0
                            }
                            logger.info(
                                f"[{camera_id} | Frame {frame_idx:04d}] 🚗 Track #{track_id} "
                                f"entered view (Conf: {v_conf*100:.1f}%) at [{vx1},{vy1},{vx2},{vy2}]"
                            )
                        else:
                            active_tracks[track_id]["last_seen_frame"] = frame_idx
                            active_tracks[track_id]["bbox"] = (vx1, vy1, vx2, vy2)
                            
                            # Keep highest quality vehicle crop (sharpness, ROI size, unclipped)
                            if v_score > active_tracks[track_id]["best_vehicle_score"]:
                                active_tracks[track_id]["best_vehicle_crop"] = vehicle_crop.copy()
                                active_tracks[track_id]["best_vehicle_score"] = v_score
                                active_tracks[track_id]["best_vehicle_sharpness"] = v_sharpness

                            # Collect candidate sample crops across the vehicle's tracklet
                            if (frame_idx - active_tracks[track_id]["last_sample_frame"] >= 3) and (vehicle_crop.size > 0):
                                if vehicle_crop.shape[0] >= 40 and vehicle_crop.shape[1] >= 40:
                                    active_tracks[track_id]["sample_crops"].append(vehicle_crop.copy())
                                    active_tracks[track_id]["last_sample_frame"] = frame_idx
                                    if len(active_tracks[track_id]["sample_crops"]) > 28:
                                        active_tracks[track_id]["sample_crops"] = active_tracks[track_id]["sample_crops"][::2]

                        # Step 2: License Plate Detection & OCR Recognition
                        frames_since_ocr = frame_idx - active_tracks[track_id]["last_ocr_frame"]
                        has_enough_samples = len(active_tracks[track_id]["ocr_reads"]) >= self.args.max_ocr_samples

                        if (not has_enough_samples) and (frames_since_ocr >= self.args.ocr_interval):
                            active_tracks[track_id]["last_ocr_frame"] = frame_idx

                            if vehicle_crop.size > 0 and vehicle_crop.shape[0] > 20 and vehicle_crop.shape[1] > 20:
                                
                                # Run Plate Detection (No deprecated 'half' argument)
                                plate_results = self.plate_model.predict(
                                    source=vehicle_crop,
                                    conf=self.args.plate_conf_thresh,
                                    device=self.device,
                                    verbose=False
                                )

                                if plate_results and plate_results[0].boxes and len(plate_results[0].boxes) > 0:
                                    p_boxes = plate_results[0].boxes.xyxy.cpu().numpy()
                                    p_confs = plate_results[0].boxes.conf.cpu().numpy()

                                    best_p_idx = np.argmax(p_confs)
                                    px1, py1, px2, py2 = map(int, p_boxes[best_p_idx])
                                    best_p_conf = float(p_confs[best_p_idx])

                                    # Global plate coordinates for frame annotation
                                    global_px1, global_py1 = vx1 + px1, vy1 + py1
                                    global_px2, global_py2 = vx1 + px2, vy1 + py2
                                    current_frame_plates.append((global_px1, global_py1, global_px2, global_py2))

                                    # Switch state to RECOGNIZING...
                                    active_tracks[track_id]["plate_bbox_found"] = True
                                    if active_tracks[track_id]["best_plate"] == "DETECTING...":
                                        active_tracks[track_id]["best_plate"] = "RECOGNIZING..."

                                    # Pad in FRAME coordinates, not vehicle-crop coordinates.
                                    pad_x = max(6, int((px2 - px1) * self.args.plate_pad))
                                    pad_y = max(4, int((py2 - py1) * self.args.plate_pad))
                                    c_px1 = max(0, global_px1 - pad_x)
                                    c_py1 = max(0, global_py1 - pad_y)
                                    c_px2 = min(frame_width,  global_px2 + pad_x)
                                    c_py2 = min(frame_height, global_py2 + pad_y)

                                    plate_crop = frame[c_py1:c_py2, c_px1:c_px2]

                                    # Only process plates that have minimum resolution to be legible (height >= 16px, width >= 40px)
                                    if plate_crop.size > 0 and plate_crop.shape[0] >= 16 and plate_crop.shape[1] >= 40:
                                        # Run Multi-Pass PaddleOCR
                                        ocr_lines = self._run_ocr_inference(plate_crop, track_id, camera_id, frame_idx)

                                        if ocr_lines:
                                            for raw_text, ocr_score in ocr_lines:
                                                cleaned = clean_plate_text(raw_text)
                                                # Discard vehicle manufacturer logos / commercial text
                                                if is_brand_or_noise(cleaned):
                                                    logger.info(
                                                        f"[{camera_id} | Frame {frame_idx:04d}] ⚠️ Track #{track_id}: "
                                                        f"Discarded manufacturer brand/logo OCR '{raw_text}'"
                                                    )
                                                    continue
                                                # Near-zero-confidence variants are noise; they
                                                # would still get a say in the length vote.
                                                if cleaned and len(cleaned) >= 4 and ocr_score >= 0.20:
                                                    active_tracks[track_id]["ocr_reads"].append((cleaned, ocr_score))
                                                    cur_best, cur_conf = resolve_best_plate(active_tracks[track_id]["ocr_reads"])
                                                    active_tracks[track_id]["best_plate"] = cur_best
                                                    active_tracks[track_id]["best_conf"] = cur_conf
                                                    
                                                    # Keep the LARGEST crop, not the one this
                                                    # OCR pass scored highest — scoring crops by
                                                    # the engine we're trying to evaluate is
                                                    # circular. More pixels on the plate is the
                                                    # signal that actually predicts legibility.
                                                    area = plate_crop.shape[0] * plate_crop.shape[1]
                                                    if area > active_tracks[track_id]["best_plate_area"]:
                                                        active_tracks[track_id]["best_plate_crop"] = plate_crop.copy()
                                                        active_tracks[track_id]["best_plate_area"] = area

                                                    logger.info(
                                                        f"[{camera_id} | Frame {frame_idx:04d}] ✅ Track #{track_id}: "
                                                        f"OCR Accepted -> '{cleaned}' (Score: {ocr_score*100:.1f}%) | "
                                                        f"Current Resolved: '{cur_best}' ({cur_conf:.1f}%)"
                                                    )
                                                else:
                                                    logger.info(
                                                        f"[{camera_id} | Frame {frame_idx:04d}] ⚠️ Track #{track_id}: "
                                                        f"Candidate '{raw_text}' discarded (length < 4 chars or noisy)"
                                                    )
                                        else:
                                            # If OCR failed, still maintain candidate plate crop if detection confidence was high
                                            area = plate_crop.shape[0] * plate_crop.shape[1]
                                            if best_p_conf > 0.40 and area > active_tracks[track_id]["best_plate_area"]:
                                                active_tracks[track_id]["best_plate_crop"] = plate_crop.copy()
                                                active_tracks[track_id]["best_plate_area"] = area

                # Step 3: Check for Dead Tracklets (Lost for max_lost_frames)
                dead_ids = [
                    t_id for t_id, t_data in active_tracks.items()
                    if frame_idx - t_data["last_seen_frame"] > self.args.max_lost_frames
                ]
                for t_id in dead_ids:
                    if self._log_track_to_csv(camera_id, t_id, active_tracks[t_id], fps):
                        logged_count += 1
                    del active_tracks[t_id]

                # Step 4: Video Annotation
                if video_writer is not None:
                    annotated_frame = self._render_frame(
                        frame=frame,
                        active_tracks=active_tracks,
                        current_frame_plates=current_frame_plates,
                        camera_id=camera_id,
                        frame_idx=frame_idx,
                        total_frames=total_frames,
                        logged_count=logged_count,
                        fps=fps
                    )
                    video_writer.write(annotated_frame)

                # Frame progress update every 100 frames
                if frame_idx % 100 == 0 or frame_idx == total_frames:
                    elapsed = time.time() - start_time
                    fps_val = frame_idx / max(elapsed, 0.001)
                    pct = (frame_idx / max(total_frames, 1)) * 100.0
                    logger.info(
                        f"[{camera_id}] Progress: {frame_idx}/{total_frames} ({pct:.1f}%) | "
                        f"Rate: {fps_val:.1f} FPS | Active Tracks: {len(active_tracks)}"
                    )

        except KeyboardInterrupt:
            logger.warning(f"[{camera_id}] Interrupted by user. Finalizing buffer...")
        finally:
            # Flush any remaining active tracks
            for t_id, t_data in list(active_tracks.items()):
                if self._log_track_to_csv(camera_id, t_id, t_data, fps):
                    logged_count += 1
                del active_tracks[t_id]

            cap.release()
            if video_writer is not None:
                video_writer.release()
                logger.info(f"[{camera_id}] ✅ Annotated video saved: '{out_video_path}'")

        if self.device == "cuda":
            torch.cuda.empty_cache()

        duration = time.time() - start_time
        logger.info(
            f"[{camera_id}] Finished in {duration:.2f}s | "
            f"Avg Speed: {frame_idx / max(duration, 0.001):.1f} FPS | "
            f"Total Vehicles Logged: {logged_count}\n"
        )

    # --------------------------------------------------------------------------
    # Frame Visualization with 3-Stage Dynamic Bounding Box Tags
    # --------------------------------------------------------------------------
    def _render_frame(
        self,
        frame: np.ndarray,
        active_tracks: Dict[int, dict],
        current_frame_plates: List[Tuple[int, int, int, int]],
        camera_id: str,
        frame_idx: int,
        total_frames: int,
        logged_count: int,
        fps: float
    ) -> np.ndarray:
        """
        Render dynamic 3-stage bounding box tags:
        1. DETECTING...  (Orange) - Vehicle detected, searching for plate
        2. RECOGNIZING... (Yellow) - Plate bbox detected, running OCR
        3. [PLATE NUMBER] (Green)  - Number plate confirmed with confidence
        """
        vis_frame = frame.copy()
        h, w = vis_frame.shape[:2]

        # Every size below was hand-tuned against 1080p. CAM2 is 4K, so fixed
        # pixel sizes render at half the apparent size there. Scale all overlay
        # geometry off the frame height so the HUD looks the same on any feed.
        s = h / 1080.0
        px = lambda v: max(1, int(round(v * s)))        # scale a pixel distance
        fs = lambda v: v * s                             # scale a font size

        for track_id, t_data in active_tracks.items():
            if t_data["last_seen_frame"] == frame_idx:
                vx1, vy1, vx2, vy2 = t_data["bbox"]
                plate_str = t_data["best_plate"]
                conf = t_data["best_conf"]

                if plate_str not in ["DETECTING...", "RECOGNIZING...", "UNKNOWN"]:
                    box_color = (0, 220, 0)
                    tag_text = f"ID:{track_id} | {plate_str} ({conf:.0f}%)"
                    text_color = (0, 0, 0)
                elif plate_str == "RECOGNIZING...":
                    box_color = (0, 215, 255)
                    tag_text = f"ID:{track_id} | RECOGNIZING..."
                    text_color = (0, 0, 0)
                else:
                    box_color = (255, 140, 0)
                    tag_text = f"ID:{track_id} | DETECTING..."
                    text_color = (255, 255, 255)

                cv2.rectangle(vis_frame, (vx1, vy1), (vx2, vy2), box_color, px(2))

                tag_scale, tag_thick = fs(0.52), px(2)
                (tw, th), baseline = cv2.getTextSize(
                    tag_text, cv2.FONT_HERSHEY_SIMPLEX, tag_scale, tag_thick)
                lbl_y1 = max(0, vy1 - th - px(8))
                lbl_y2 = vy1
                lbl_x2 = min(w, vx1 + tw + px(10))

                cv2.rectangle(vis_frame, (vx1, lbl_y1), (lbl_x2, lbl_y2), box_color, -1)
                cv2.putText(
                    vis_frame,
                    tag_text,
                    (vx1 + px(5), vy1 - px(5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    tag_scale,
                    text_color,
                    tag_thick,
                    cv2.LINE_AA
                )

        # Draw detected license plate bounding boxes in current frame (Cyan outline)
        for bx1, by1, bx2, by2 in current_frame_plates:
            cv2.rectangle(vis_frame, (bx1, by1), (bx2, by2), (0, 255, 255), px(2))

        # Modern Top-Left HUD
        hud_w, hud_h, margin = px(360), px(110), px(15)
        overlay = vis_frame.copy()
        cv2.rectangle(overlay, (margin, margin),
                      (margin + hud_w, margin + hud_h), (18, 22, 28), -1)
        cv2.addWeighted(overlay, 0.78, vis_frame, 0.22, 0, vis_frame)
        cv2.rectangle(vis_frame, (margin, margin),
                      (margin + hud_w, margin + hud_h), (50, 60, 75), px(1))

        pct = (frame_idx / max(total_frames, 1)) * 100.0
        hud_lines = [
            (f"NODE: {camera_id} | ZYRODEV ANPR", 38, 0.52, (0, 200, 255), 2),
            (f"FRAME: {frame_idx}/{total_frames} ({pct:.1f}%)", 62, 0.44, (220, 220, 220), 1),
            (f"ACTIVE VEHICLES: {len(active_tracks)}", 84, 0.44, (100, 255, 100), 1),
            (f"VEHICLES LOGGED: {logged_count}", 106, 0.44, (255, 180, 50), 1),
        ]
        for text, y, t_scale, color, t_thick in hud_lines:
            cv2.putText(vis_frame, text, (px(26), px(y)), cv2.FONT_HERSHEY_SIMPLEX,
                        fs(t_scale), color, px(t_thick), cv2.LINE_AA)

        # Burnt-in recording timestamp, top-right, the way a DVR/RTSP feed shows it.
        # This is the clock the CSV entry/exit times are anchored to.
        stamp = self._wallclock(frame_idx, fps).strftime(OVERLAY_TS_FMT)
        font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, fs(0.62), px(2)
        (tw, th), base = cv2.getTextSize(stamp, font, scale, thick)
        x2, y1 = w - px(20), px(18)
        x1, y2 = x2 - tw - px(20), y1 + th + base + px(12)

        shade = vis_frame.copy()
        cv2.rectangle(shade, (x1, y1), (x2, y2), (0, 0, 0), -1)
        cv2.addWeighted(shade, 0.45, vis_frame, 0.55, 0, vis_frame)
        # Dark outline first so the text stays readable over a bright sky.
        org = (x1 + px(10), y2 - base - px(5))
        cv2.putText(vis_frame, stamp, org, font, scale, (0, 0, 0), thick + px(2), cv2.LINE_AA)
        cv2.putText(vis_frame, stamp, org, font, scale, (255, 255, 255), thick, cv2.LINE_AA)

        return vis_frame

    # --------------------------------------------------------------------------
    # Multi-Camera Sequential Runner
    # --------------------------------------------------------------------------
    def run(self, video_paths: List[str]):
        """Run pipeline across all input video files sequentially."""
        total = len(video_paths)
        logger.info(f"Initializing ANPR Processing Pipeline for {total} video stream(s)...")

        start_num = getattr(self.args, "camera_start_idx", 4)
        custom_ids = getattr(self.args, "camera_ids", []) or []

        for idx, v_path in enumerate(video_paths):
            if idx < len(custom_ids):
                cam_id = custom_ids[idx]
            else:
                cam_id = f"Camera_{start_num + idx}"
            self.process_video_stream(v_path, cam_id)

        logger.info("\n" + "="*70)
        logger.info("🎉 ALL CAMERA FEEDS PROCESSED SUCCESSFULLY!")
        logger.info(f"📁 Consolidated CSV Log: {self.csv_log_path}")
        logger.info(f"📁 Verified Crops: {os.path.join(self.args.output_dir, 'crops')}")
        logger.info(f"📁 Output Video Directory: {self.args.output_dir}")
        logger.info("="*70)


# ==============================================================================
# CLI Entry Point
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="City-Wide Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics"
    )
    parser.add_argument(
        "positional_videos",
        nargs="*",
        default=[],
        help="Optional positional list of video files"
    )
    parser.add_argument(
        "--videos",
        nargs="+",
        default=[],
        help="List of video files to process sequentially (e.g. --videos cam1.mp4 cam2.mp4)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs",
        help="Directory to save output annotated videos, crops, and vehicle_logs.csv (default: ./outputs)"
    )
    parser.add_argument(
        "--camera_start_idx",
        type=int,
        default=4,
        help="Starting index for camera numbering (default: 4 -> Camera_4, Camera_5, Camera_6)"
    )
    parser.add_argument(
        "--camera_ids",
        nargs="+",
        default=[],
        help="Explicit camera IDs list (e.g. --camera_ids Camera_4 Camera_5 Camera_6)"
    )
    parser.add_argument(
        "--vehicle_model",
        type=str,
        default="yolo11n.pt",
        help="YOLO model for vehicle tracking: 'yolo11n.pt' or 'yolov8n.pt' (default: yolo11n.pt)"
    )
    parser.add_argument(
        "--plate_model",
        type=str,
        default="yolov8n_plate.pt",
        help="Trained plate detector model weights (default: yolov8n_plate.pt)"
    )
    parser.add_argument(
        "--conf_thresh",
        type=float,
        default=0.35,
        help="Confidence threshold for vehicle detection (default: 0.35)"
    )
    parser.add_argument(
        "--plate_conf_thresh",
        type=float,
        default=0.25,
        help="Confidence threshold for plate detection (default: 0.25)"
    )
    parser.add_argument(
        "--ocr_interval",
        type=int,
        default=1,
        help="Run OCR every N frames for active vehicles (default: 1). Raising this to "
             "2-3 is close to free: the per-character vote still gets plenty of samples."
    )
    parser.add_argument(
        "--max_ocr_samples",
        type=int,
        default=40,
        help="Max OCR reads per vehicle before locking candidate pool (default: 40). "
             "Each frame contributes up to 4 reads (one per preprocessing variant), so "
             "this is roughly 10 frames of evidence for the per-character vote."
    )
    parser.add_argument(
        "--min_save_conf",
        type=float,
        default=25.0,
        help="Minimum OCR confidence percentage required to save plate crops to disk (default: 25.0)"
    )
    parser.add_argument(
        "--save_all_crops",
        action="store_true",
        default=True,
        help="Save vehicle crop and Re-ID embedding for all tracked vehicles meeting quality threshold (default: True)"
    )
    parser.add_argument(
        "--reid_model",
        type=str,
        default="veri776",
        help="Vehicle Re-ID model architecture: 'veri776' (SOTA VeRi-776 Domain Model), 'dinov2', 'resnet50', 'resnet18' (default: veri776)"
    )
    parser.add_argument(
        "--hybrid_color",
        action="store_true",
        default=True,
        help="Enable color-aware hybrid feature fusion (deep structure + HSV color palette) (default: True)"
    )
    parser.add_argument(
        "--save_samples",
        action="store_true",
        default=True,
        help="Auto-generate and save 6-7 sample crops per vehicle for Re-ID accuracy testing (default: True)"
    )
    parser.add_argument(
        "--min_track_frames",
        type=int,
        default=5,
        help="Minimum frames a vehicle must be tracked before saving crops/embeddings (default: 5)"
    )
    parser.add_argument(
        "--max_lost_frames",
        type=int,
        default=30,
        help="Frames before finalizing an inactive tracklet (default: 30)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device ('cuda', 'cpu', or leave blank for auto)"
    )
    parser.add_argument(
        "--no_video",
        action="store_true",
        help="Disable writing annotated MP4 videos for high-speed batch processing"
    )
    parser.add_argument(
        "--recorded_at",
        type=parse_recorded_at,
        default="2026-08-31 15:58:00",
        help="Wall-clock time the source footage started recording, shared by every "
             "camera (default: 2026-08-31 15:58:00). Burnt into the output video and "
             "used for the entry/exit timestamps in vehicle_logs.csv."
    )
    parser.add_argument(
        "--max_frames",
        type=int,
        default=0,
        help="Stop each feed after N frames (0 = whole video). Useful for quick demo runs."
    )
    parser.add_argument(
        "--plate_pad",
        type=float,
        default=0.25,
        help="Fractional padding added around the plate box, in frame coords (default: 0.25)"
    )
    parser.add_argument(
        "--state_prior",
        type=str,
        default="",
        help="Comma-separated state codes these cameras actually see (e.g. TN,KL,KA). "
             "Breaks ties when repairing a garbled state field."
    )

    return parser.parse_args()


def main():
    global STATE_PRIOR
    args = parse_args()

    STATE_PRIOR = tuple(s.strip().upper() for s in args.state_prior.split(",") if s.strip())
    if unknown := [s for s in STATE_PRIOR if s not in STATE_CODES]:
        logger.warning(f"Unknown state code(s) in --state_prior: {', '.join(unknown)}")

    all_videos = args.videos if args.videos else args.positional_videos
    if not all_videos:
        print("\n[ERROR] No video files provided!")
        print("Usage: python main.py --videos ./input2/CAM1_comp.mp4 --output_dir ./outputs\n")
        sys.exit(1)

    pipeline = MultiCameraANPRPipeline(args)
    pipeline.run(all_videos)


if __name__ == "__main__":
    main()
