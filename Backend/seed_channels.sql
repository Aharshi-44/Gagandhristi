-- ============================================================
-- GAGANDRISTHI V2: SEED & CLEAN ALERT CHANNEL CATALOGUE
-- Retains ONLY the 3 Satellite Analytical Models
-- Removes all old communication channels (Email, Slack, SMS, etc.)
-- ============================================================

-- 1. Insert or update the 3 core analytical models
INSERT INTO public.alert_channel_catalogue (
    script_id,
    script_name,
    channel_name,
    category,
    args,
    auxdata
) VALUES 
(
    'siamese_unet_levir_cd',
    'Structural Changes (DL)',
    'Structural Infrastructure',
    'INFRASTRUCTURE',
    '{"model": "Siamese U-Net", "threshold": 0.25, "pretraining": "LEVIR-CD", "channel_key": "structural"}'::jsonb,
    '{"description": "Detects newly erected or demolished man-made structures, buildings, walls, and fortifications while ignoring seasonal ground changes."}'::jsonb
),
(
    'ndvi_vari_vegetation',
    'Vegetation Clearance (NDVI/VARI)',
    'Vegetation & Forest Clearance',
    'ENVIRONMENTAL',
    '{"model": "Vegetation Multi-Temporal Index", "indices": ["NDVI", "VARI"], "threshold": 0.12, "channel_key": "vegetation"}'::jsonb,
    '{"description": "Detects multi-temporal vegetative biomass shifts, logging, jungle clearing, defense perimeter clearance, and distinguishes from seasonal regrowth."}'::jsonb
),
(
    'pixel_diff_cva',
    'Tactical Surface Anomaly (Pixel Diff)',
    'Tactical Surface Disturbance',
    'TACTICAL_ANOMALY',
    '{"model": "Radiometric Change Vector Analysis", "threshold": 0.18, "channel_key": "pixel_diff"}'::jsonb,
    '{"description": "Detects surface anomalies, temporary vehicle convoys on open terrain, earth displacement, fresh unpaved roads, and tent pitching."}'::jsonb
)
ON CONFLICT (script_id) DO UPDATE SET
    script_name = EXCLUDED.script_name,
    channel_name = EXCLUDED.channel_name,
    category = EXCLUDED.category,
    args = EXCLUDED.args,
    auxdata = EXCLUDED.auxdata;

-- 2. Safely remap any existing subscriptions referencing old channels to the Structural model
UPDATE public.subscription 
SET channel_id = (SELECT id FROM public.alert_channel_catalogue WHERE script_id = 'siamese_unet_levir_cd' LIMIT 1)
WHERE channel_id NOT IN (
    SELECT id FROM public.alert_channel_catalogue 
    WHERE script_id IN ('siamese_unet_levir_cd', 'ndvi_vari_vegetation', 'pixel_diff_cva')
);

-- 3. Delete all other non-model channels (Email, Slack, SMS, WhatsApp, Webhooks)
DELETE FROM public.alert_channel_catalogue 
WHERE script_id NOT IN (
    'siamese_unet_levir_cd',
    'ndvi_vari_vegetation',
    'pixel_diff_cva'
);

-- 4. Verify only the 3 models remain
SELECT id, script_id, channel_name, category FROM public.alert_channel_catalogue ORDER BY id;
