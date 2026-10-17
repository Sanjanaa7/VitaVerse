================================================================================
VitaVerse — AI 360 Panorama Environments (Configured & Ready)
================================================================================

All 3 high-resolution 360° equirectangular panoramas are now fully processed,
tonemapped, and placed right here in this folder:

────────────────────────────────────────────────────────────────────────────────
ACTIVE ENVIRONMENT MAPPING (Comfort Class → Scene)
────────────────────────────────────────────────────────────────────────────────

1. pool_360.jpg (4096 x 2048 high-definition equirectangular)
   Comfort Class : CALM  (SpO₂ ≥ 95%, HR 60–80 bpm, HRV ≥ 50 ms)
   Scene Name    : Tranquil Pool
   Source        : pool_8k.exr (Tonemapped HDR, refreshing crystal azure daylight)
   Clinical Role : Optimal baseline relaxation, parasympathetic vagal dominance.

2. beach_360.jpg (4096 x 2048 high-definition equirectangular)
   Comfort Class : ADJUST  (SpO₂ 90–94.5%, HR 81–95 bpm, HRV 30–49 ms)
   Scene Name    : Umhlanga Beach Sunrise
   Source        : umhlanga_sunrise_8k.exr (Poly Haven coastal sunrise ocean waves)
   Clinical Role : Moderate sensory recalibration for restlessness and autonomic fluctuation.

3. home_360.jpg (3840 x 1920 4K high-definition equirectangular)
   Comfort Class : SUPPORT  (SpO₂ < 92%, HR > 95 bpm, HRV < 30 ms)
   Scene Name    : Kerala Heritage Home
   Source        : VirtualTourEasy (Ref: Bfn4KNHKvK)
                   https://viewer.virtualtoureasy.com/?r=Bfn4KNHKvK
   Clinical Role : Grounding, low-stimulation refuge with traditional teakwood pillars,
                   hanging wooden swing, and gentle courtyard daylight.

────────────────────────────────────────────────────────────────────────────────
AUTO-SETUP & RUNNING IN UNITY
────────────────────────────────────────────────────────────────────────────────

1. In Unity Editor:
   Click the top menu:
     ► VitaVerse → Auto-Setup Scene (One-Click)

2. The setup script auto-detects:
     • pool_360.jpg   → Assigned to aiPoolPanorama (Calm)
     • beach_360.jpg  → Assigned to aiBeachPanorama (Adjust)
     • home_360.jpg   → Assigned to aiHomePanorama (Support)

3. Press the Unity [Play] button:
     • Look around 360° with Mouse Click & Drag or WASD / Arrow keys
     • Press [H] to hide/show the glassmorphic Healthcare HUD
     • Click Scenario 1 (Calm), Scenario 2 (Adjust), or Scenario 3 (Support)
     • The 360° panorama environment transitions dynamically with the ML prediction!
