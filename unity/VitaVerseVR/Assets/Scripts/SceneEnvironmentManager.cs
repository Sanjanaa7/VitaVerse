using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// AI 360 Panorama Environment Manager for VitaVerse Phase 1.
    ///
    /// Comfort Class → Environment mapping:
    ///   calm    → Peaceful Botanical Garden  (garden_360)
    ///   adjust  → Serene Tropical Beach      (beach_360)
    ///   support → Tranquil Heritage Home     (home_360)
    ///
    /// Assign equirectangular 360° JPG/PNG images in the Inspector.
    /// If no image is assigned, PanoramicSkyGenerator provides a procedural fallback.
    /// </summary>
    public class SceneEnvironmentManager : MonoBehaviour
    {
        [Header("AI 360 Panoramas — Drop Equirectangular JPG/PNG here")]
        [Tooltip("CALM: Tranquil Pool — pool_360.jpg (from pool_8k.exr)")]
        public Texture2D aiPoolPanorama;
        public Texture2D aiGardenPanorama; // legacy fallback

        [Tooltip("ADJUST: Umhlanga Beach Sunrise — beach_360.jpg (from umhlanga_sunrise_8k.exr)")]
        public Texture2D aiBeachPanorama;

        [Tooltip("SUPPORT: Kerala Heritage Home — home_360.jpg (from VirtualTourEasy Bfn4KNHKvK)")]
        public Texture2D aiHomePanorama;

        [Header("Lighting")]
        public Light mainDirectionalLight;

        [Header("State (Read-Only)")]
        public string currentEnvironmentName = "Pool";

        private Material skyboxMat;

        private void Awake()
        {
            Shader skyShader = Shader.Find("Skybox/Panoramic");
            if (skyShader != null)
            {
                skyboxMat = new Material(skyShader);
                if (skyboxMat.HasProperty("_Exposure"))  skyboxMat.SetFloat("_Exposure", 1.1f);
                if (skyboxMat.HasProperty("_ImageType")) skyboxMat.SetFloat("_ImageType", 0f); // 360°
            }
            else
            {
                Shader fallback = Shader.Find("Unlit/Texture");
                if (fallback != null) skyboxMat = new Material(fallback);
            }
        }

        private void Start()
        {
            // Preload 360 panorama files if not assigned in Inspector
            GetOrLoadPanorama(ref aiPoolPanorama, "pool_360.jpg", "pool_8k.exr", null);
            GetOrLoadPanorama(ref aiBeachPanorama, "beach_360.jpg", "umhlanga_sunrise_8k.exr", null);
            GetOrLoadPanorama(ref aiHomePanorama, "home_360.jpg", null, null);

            SwitchToEnvironment("Pool");
        }

        /// <summary>
        /// Called by ComfortManager when a new ML comfort class is received.
        /// Accepts both environment name and comfort class string.
        /// </summary>
        public void SwitchToEnvironment(string name)
        {
            if (string.IsNullOrEmpty(name)) return;

            switch (name.Trim().ToLower())
            {
                case "pool":
                case "garden":
                case "calm":
                    ApplyPoolEnvironment();
                    currentEnvironmentName = "Pool";
                    break;

                case "beach":
                case "sunrise":
                case "forest":
                case "adjust":
                    ApplyBeachEnvironment();
                    currentEnvironmentName = "Beach";
                    break;

                case "home":
                case "lowstimulation":
                case "sunset":
                case "support":
                    ApplyHomeEnvironment();
                    currentEnvironmentName = "Home";
                    break;

                default:
                    ApplyPoolEnvironment();
                    currentEnvironmentName = "Pool";
                    break;
            }

            Debug.Log($"[SceneEnvironmentManager] Environment → {currentEnvironmentName}");
        }

        // ─────────────────────────────────────────────────────────────
        // CALM: Tranquil Pool
        //   Bright refreshing daylight, crystal azure water reflections
        // ─────────────────────────────────────────────────────────────
        private void ApplyPoolEnvironment()
        {
            if (mainDirectionalLight != null)
            {
                mainDirectionalLight.color = new Color(0.96f, 0.98f, 1.0f);
                mainDirectionalLight.intensity = 1.15f;
                mainDirectionalLight.transform.rotation = Quaternion.Euler(50f, -25f, 0f);
            }

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor     = new Color(0.60f, 0.82f, 0.96f);
            RenderSettings.ambientEquatorColor  = new Color(0.75f, 0.90f, 0.95f);
            RenderSettings.ambientGroundColor   = new Color(0.18f, 0.38f, 0.45f);

            RenderSettings.fog = true;
            RenderSettings.fogMode    = FogMode.Exponential;
            RenderSettings.fogColor   = new Color(0.75f, 0.88f, 0.96f);
            RenderSettings.fogDensity = 0.0015f;

            Texture2D tex = GetOrLoadPanorama(ref aiPoolPanorama, "pool_360.jpg", "pool_8k.exr", () => PanoramicSkyGenerator.GenerateGardenPanorama());
            ApplySkybox(tex);
        }

        // ─────────────────────────────────────────────────────────────
        // ADJUST: Umhlanga Beach Sunrise
        //   Warm morning coastal horizon, soft sea-breeze ambient
        // ─────────────────────────────────────────────────────────────
        private void ApplyBeachEnvironment()
        {
            if (mainDirectionalLight != null)
            {
                mainDirectionalLight.color = new Color(1.0f, 0.94f, 0.86f);
                mainDirectionalLight.intensity = 1.25f;
                mainDirectionalLight.transform.rotation = Quaternion.Euler(38f, 30f, 0f);
            }

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor     = new Color(0.55f, 0.76f, 0.92f);
            RenderSettings.ambientEquatorColor  = new Color(0.92f, 0.88f, 0.80f);
            RenderSettings.ambientGroundColor   = new Color(0.65f, 0.58f, 0.45f);

            RenderSettings.fog = true;
            RenderSettings.fogMode    = FogMode.Exponential;
            RenderSettings.fogColor   = new Color(0.85f, 0.88f, 0.92f);
            RenderSettings.fogDensity = 0.0018f;

            Texture2D tex = GetOrLoadPanorama(ref aiBeachPanorama, "beach_360.jpg", "umhlanga_sunrise_8k.exr", () => PanoramicSkyGenerator.GenerateBeachPanorama());
            ApplySkybox(tex);
        }

        // ─────────────────────────────────────────────────────────────
        // SUPPORT: Kerala Heritage Home (from VirtualTourEasy Bfn4KNHKvK)
        //   Warm indoor ambient, teakwood tones, soft courtyard natural light
        // ─────────────────────────────────────────────────────────────
        private void ApplyHomeEnvironment()
        {
            if (mainDirectionalLight != null)
            {
                mainDirectionalLight.color = new Color(1.0f, 0.88f, 0.72f);
                mainDirectionalLight.intensity = 0.65f;
                mainDirectionalLight.transform.rotation = Quaternion.Euler(30f, 0f, 0f);
            }

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor     = new Color(0.85f, 0.72f, 0.55f);
            RenderSettings.ambientEquatorColor  = new Color(0.65f, 0.50f, 0.36f);
            RenderSettings.ambientGroundColor   = new Color(0.38f, 0.22f, 0.16f);

            RenderSettings.fog = true;
            RenderSettings.fogMode    = FogMode.Exponential;
            RenderSettings.fogColor   = new Color(0.78f, 0.68f, 0.56f);
            RenderSettings.fogDensity = 0.003f;

            Texture2D tex = GetOrLoadPanorama(ref aiHomePanorama, "home_360.jpg", null, () => PanoramicSkyGenerator.GenerateHomePanorama());
            ApplySkybox(tex);
        }

        private Texture2D GetOrLoadPanorama(ref Texture2D assignedTex, string primaryFile, string fallbackFile, System.Func<Texture2D> proceduralFallback)
        {
            if (assignedTex != null) return assignedTex;

            assignedTex = LoadTextureFromDisk(primaryFile);
            if (assignedTex != null) return assignedTex;

            if (!string.IsNullOrEmpty(fallbackFile))
            {
                assignedTex = LoadTextureFromDisk(fallbackFile);
                if (assignedTex != null) return assignedTex;
            }

            if (aiGardenPanorama != null) return aiGardenPanorama;

            return proceduralFallback != null ? proceduralFallback() : null;
        }

        private Texture2D LoadTextureFromDisk(string filename)
        {
            try
            {
                string path = System.IO.Path.Combine(Application.dataPath, "Panoramas", filename);
                if (System.IO.File.Exists(path))
                {
                    byte[] bytes = System.IO.File.ReadAllBytes(path);
                    Texture2D tex = new Texture2D(2, 2, TextureFormat.RGB24, false);
                    if (tex.LoadImage(bytes))
                    {
                        tex.wrapMode = TextureWrapMode.Repeat;
                        tex.filterMode = FilterMode.Bilinear;
                        Debug.Log($"[SceneEnvironmentManager] Auto-loaded 360 panorama: {filename}");
                        return tex;
                    }
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning($"[SceneEnvironmentManager] Could not load {filename}: {ex.Message}");
            }
            return null;
        }

        // ─────────────────────────────────────────────────────────────
        // Apply equirectangular texture to Unity Panoramic Skybox
        // ─────────────────────────────────────────────────────────────
        private void ApplySkybox(Texture2D tex)
        {
            if (tex == null || skyboxMat == null) return;
            skyboxMat.mainTexture = tex;
            RenderSettings.skybox = skyboxMat;
            DynamicGI.UpdateEnvironment();
        }
    }
}
