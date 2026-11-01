using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

namespace VitaVerse
{
    /// <summary>
    /// VitaVerse Phase 2 — 360° Environment Manager.
    ///
    /// Supports all 7 panorama environments (3 original + 4 new EXR).
    /// Polls http://127.0.0.1:8000/active-environment every 1.2s.
    /// When the clinician changes scene in the browser console, Unity
    /// auto-switches the skybox within ~1.2 seconds — no HUD needed.
    ///
    /// Unity shows ONLY the full-screen 360° panorama.
    /// All UI is on the browser (Dual-Screen Clinician Console at /demo).
    /// </summary>
    public class SceneEnvironmentManager : MonoBehaviour
    {
        [Header("Backend")]
        public string backendUrl = "http://127.0.0.1:8000";
        public float pollIntervalSeconds = 1.2f;

        [Header("Lighting")]
        public Light mainDirectionalLight;

        [Header("Audio")]
        public EnvironmentAudioManager audioManager;

        [Header("State (Read-Only)")]
        public string currentEnvironmentName = "Pool";
        public string currentComfortClass    = "calm";
        public bool   isBackendConnected     = false;

        // ── Internal state ──────────────────────────────────────────────
        private Material  skyboxMat;
        private string    lastLoadedScene = "";
        private Dictionary<string, Texture2D> textureCache = new Dictionary<string, Texture2D>();

        // ── All 7 environment definitions ───────────────────────────────
        [Serializable]
        private class EnvDef
        {
            public string sceneName;
            public string file;
            public string fallbackFile;
            public string comfortClass;
            public Color  lightColor;
            public float  lightIntensity;
            public Vector3 lightRotation;
            public Color  fogColor;
            public float  fogDensity;
            public Color  ambientSky;
            public Color  ambientEquator;
            public Color  ambientGround;
        }

        private static readonly Dictionary<string, EnvDef> Environments = new Dictionary<string, EnvDef>
        {
            ["Pool"] = new EnvDef
            {
                sceneName = "Pool", file = "pool_360.jpg", fallbackFile = "pool_8k.exr",
                comfortClass = "calm",
                lightColor = new Color(0.96f, 0.98f, 1.0f), lightIntensity = 1.15f,
                lightRotation = new Vector3(50f, -25f, 0f),
                fogColor = new Color(0.75f, 0.88f, 0.96f), fogDensity = 0.0015f,
                ambientSky = new Color(0.60f, 0.82f, 0.96f),
                ambientEquator = new Color(0.75f, 0.90f, 0.95f),
                ambientGround  = new Color(0.18f, 0.38f, 0.45f)
            },
            ["Beach"] = new EnvDef
            {
                sceneName = "Beach", file = "beach_360.jpg", fallbackFile = "umhlanga_sunrise_8k.exr",
                comfortClass = "adjust",
                lightColor = new Color(1.0f, 0.94f, 0.86f), lightIntensity = 1.25f,
                lightRotation = new Vector3(38f, 30f, 0f),
                fogColor = new Color(0.85f, 0.88f, 0.92f), fogDensity = 0.0018f,
                ambientSky = new Color(0.55f, 0.76f, 0.92f),
                ambientEquator = new Color(0.92f, 0.88f, 0.80f),
                ambientGround  = new Color(0.65f, 0.58f, 0.45f)
            },
            ["Home"] = new EnvDef
            {
                sceneName = "Home", file = "home_360.jpg", fallbackFile = null,
                comfortClass = "support",
                lightColor = new Color(1.0f, 0.88f, 0.72f), lightIntensity = 0.65f,
                lightRotation = new Vector3(30f, 0f, 0f),
                fogColor = new Color(0.78f, 0.68f, 0.56f), fogDensity = 0.003f,
                ambientSky = new Color(0.85f, 0.72f, 0.55f),
                ambientEquator = new Color(0.65f, 0.50f, 0.36f),
                ambientGround  = new Color(0.38f, 0.22f, 0.16f)
            },
            ["BlueLagoon"] = new EnvDef
            {
                sceneName = "BlueLagoon", file = "blue_lagoon_4k.exr", fallbackFile = null,
                comfortClass = "calm",
                lightColor = new Color(0.80f, 0.95f, 1.0f), lightIntensity = 1.1f,
                lightRotation = new Vector3(45f, -10f, 0f),
                fogColor = new Color(0.60f, 0.88f, 0.96f), fogDensity = 0.0012f,
                ambientSky = new Color(0.40f, 0.75f, 0.95f),
                ambientEquator = new Color(0.55f, 0.82f, 0.92f),
                ambientGround  = new Color(0.10f, 0.30f, 0.55f)
            },
            ["MistyPines"] = new EnvDef
            {
                sceneName = "MistyPines", file = "misty_pines_4k.exr", fallbackFile = null,
                comfortClass = "support",
                lightColor = new Color(0.88f, 0.92f, 0.88f), lightIntensity = 0.70f,
                lightRotation = new Vector3(25f, 15f, 0f),
                fogColor = new Color(0.78f, 0.84f, 0.80f), fogDensity = 0.004f,
                ambientSky = new Color(0.60f, 0.72f, 0.62f),
                ambientEquator = new Color(0.48f, 0.58f, 0.50f),
                ambientGround  = new Color(0.22f, 0.30f, 0.24f)
            },
            ["NightSky"] = new EnvDef
            {
                sceneName = "NightSky", file = "rogland_clear_night_4k.exr", fallbackFile = null,
                comfortClass = "adjust",
                lightColor = new Color(0.62f, 0.72f, 0.95f), lightIntensity = 0.40f,
                lightRotation = new Vector3(15f, 180f, 0f),
                fogColor = new Color(0.08f, 0.10f, 0.22f), fogDensity = 0.0005f,
                ambientSky = new Color(0.10f, 0.12f, 0.30f),
                ambientEquator = new Color(0.12f, 0.14f, 0.28f),
                ambientGround  = new Color(0.04f, 0.05f, 0.12f)
            },
            ["SunsetFire"] = new EnvDef
            {
                sceneName = "SunsetFire", file = "the_sky_is_on_fire_4k.exr", fallbackFile = null,
                comfortClass = "adjust",
                lightColor = new Color(1.0f, 0.72f, 0.32f), lightIntensity = 1.30f,
                lightRotation = new Vector3(12f, 45f, 0f),
                fogColor = new Color(0.95f, 0.58f, 0.22f), fogDensity = 0.002f,
                ambientSky = new Color(0.90f, 0.50f, 0.18f),
                ambientEquator = new Color(0.80f, 0.36f, 0.12f),
                ambientGround  = new Color(0.30f, 0.12f, 0.04f)
            }
        };

        // ── JSON response from /active-environment ──────────────────────
        [Serializable]
        private class ActiveEnvResponse
        {
            public string scene_name;
            public string comfort_class;
            public string scene_file;
            public string photo_url;
            public string display_name;
            public bool   memory_audio_active;
            public string memory_audio_url;
            public string memory_audio_title;
        }

        private bool   lastMemoryAudioActive = false;
        private string lastMemoryAudioUrl = "";

        // ── Unity lifecycle ─────────────────────────────────────────────
        private void Awake()
        {
            Shader skyShader = Shader.Find("Skybox/Panoramic");
            if (skyShader != null)
            {
                skyboxMat = new Material(skyShader);
                if (skyboxMat.HasProperty("_Exposure"))  skyboxMat.SetFloat("_Exposure", 1.0f);
                if (skyboxMat.HasProperty("_ImageType")) skyboxMat.SetFloat("_ImageType", 0f);
            }
            else
            {
                Shader fallback = Shader.Find("Unlit/Texture");
                if (fallback != null) skyboxMat = new Material(fallback);
            }

            if (audioManager == null)
            {
                audioManager = GetComponent<EnvironmentAudioManager>();
                if (audioManager == null)
                {
                    audioManager = gameObject.AddComponent<EnvironmentAudioManager>();
                }
            }
        }

        private void Start()
        {
            SwitchToEnvironment("Pool");
            StartCoroutine(PollBackend());
        }

        // ── Backend polling loop ────────────────────────────────────────
        private IEnumerator PollBackend()
        {
            string endpoint = $"{backendUrl.TrimEnd('/')}/active-environment";

            while (true)
            {
                using (UnityWebRequest req = UnityWebRequest.Get(endpoint))
                {
                    req.timeout = 2;
                    yield return req.SendWebRequest();

                    if (req.result == UnityWebRequest.Result.Success)
                    {
                        isBackendConnected = true;
                        try
                        {
                            ActiveEnvResponse res = JsonUtility.FromJson<ActiveEnvResponse>(req.downloadHandler.text);
                            if (res != null && !string.IsNullOrEmpty(res.scene_name))
                            {
                                string targetKey = !string.IsNullOrEmpty(res.scene_file) ? res.scene_file : res.scene_name;
                                if (targetKey != lastLoadedScene)
                                {
                                    if (Environments.ContainsKey(res.scene_name))
                                    {
                                        SwitchToEnvironment(res.scene_name);
                                    }
                                    else
                                    {
                                        StartCoroutine(ApplyCustomUpload(res));
                                    }
                                }

                                // Check Memory Audio Therapy state (plays across all scenarios & environments)
                                if (res.memory_audio_active != lastMemoryAudioActive ||
                                   (res.memory_audio_active && res.memory_audio_url != lastMemoryAudioUrl))
                                {
                                    lastMemoryAudioActive = res.memory_audio_active;
                                    lastMemoryAudioUrl = res.memory_audio_url;

                                    if (res.memory_audio_active && !string.IsNullOrEmpty(res.memory_audio_url))
                                    {
                                        StartCoroutine(DownloadAndPlayMemoryAudio(res.memory_audio_url));
                                    }
                                    else
                                    {
                                        if (audioManager != null)
                                        {
                                            audioManager.DisableMemoryAudio(currentEnvironmentName);
                                        }
                                    }
                                }
                            }
                        }
                        catch { }
                    }
                    else
                    {
                        isBackendConnected = false;
                    }
                }
                yield return new WaitForSeconds(pollIntervalSeconds);
            }
        }

        // ── Memory Audio Therapy Streamer ──────────────────────────────
        private IEnumerator DownloadAndPlayMemoryAudio(string audioUrl)
        {
            Debug.Log($"[SceneEnvironmentManager] Streaming Memory Audio Therapy from: {audioUrl}");
            using (UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip(audioUrl, AudioType.MPEG))
            {
                www.timeout = 10;
                yield return www.SendWebRequest();
                if (www.result == UnityWebRequest.Result.Success)
                {
                    AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
                    if (clip != null && audioManager != null)
                    {
                        clip.name = "MemoryAudioTherapy";
                        audioManager.SetMemoryAudio(clip, true);
                        Debug.Log("[SceneEnvironmentManager] Memory Audio Therapy playing in VR headset.");
                    }
                }
                else
                {
                    Debug.LogWarning($"[SceneEnvironmentManager] Failed to stream memory audio: {www.error}");
                }
            }
        }

        // ── Custom uploaded 360° photo handler ──────────────────────────
        private IEnumerator ApplyCustomUpload(ActiveEnvResponse res)
        {
            Texture2D tex = null;
            string filename = !string.IsNullOrEmpty(res.scene_file) ? res.scene_file : res.scene_name;

            // 1. Try loading directly from local Assets/Panoramas (mirrored by backend)
            if (!string.IsNullOrEmpty(filename))
            {
                tex = LoadFromDisk(filename);
            }

            // 2. If not immediately on disk, download via HTTP photo_url
            if (tex == null && !string.IsNullOrEmpty(res.photo_url))
            {
                Debug.Log($"[SceneEnvironmentManager] Streaming custom 360° photo from: {res.photo_url}");
                using (UnityWebRequest imgReq = UnityWebRequest.Get(res.photo_url))
                {
                    imgReq.timeout = 8;
                    yield return imgReq.SendWebRequest();
                    if (imgReq.result == UnityWebRequest.Result.Success && imgReq.downloadHandler != null)
                    {
                        byte[] bytes = imgReq.downloadHandler.data;
                        Texture2D downloaded = new Texture2D(2, 2, TextureFormat.RGB24, false);
                        if (downloaded.LoadImage(bytes))
                        {
                            downloaded.wrapMode = TextureWrapMode.Repeat;
                            downloaded.filterMode = FilterMode.Bilinear;
                            tex = downloaded;
                        }
                    }
                    else
                    {
                        Debug.LogWarning($"[SceneEnvironmentManager] Download error: {imgReq.error}");
                    }
                }
            }

            if (tex != null)
            {
                // Balanced, natural therapeutic lighting
                if (mainDirectionalLight != null)
                {
                    mainDirectionalLight.color = new Color(1.0f, 0.98f, 0.94f);
                    mainDirectionalLight.intensity = 1.1f;
                    mainDirectionalLight.transform.rotation = Quaternion.Euler(46f, -22f, 0f);
                }

                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = new Color(0.65f, 0.75f, 0.85f);
                RenderSettings.ambientEquatorColor = new Color(0.72f, 0.75f, 0.80f);
                RenderSettings.ambientGroundColor = new Color(0.24f, 0.24f, 0.28f);
                RenderSettings.fog = false;

                if (skyboxMat != null)
                {
                    skyboxMat.mainTexture = tex;
                    RenderSettings.skybox = skyboxMat;
                    DynamicGI.UpdateEnvironment();
                }

                lastLoadedScene = filename;
                currentEnvironmentName = !string.IsNullOrEmpty(res.display_name) ? res.display_name : res.scene_name;
                currentComfortClass = !string.IsNullOrEmpty(res.comfort_class) ? res.comfort_class : "calm";
                if (audioManager != null) audioManager.StopSound();
                Debug.Log($"[SceneEnvironmentManager] Custom photo active in VR: {currentEnvironmentName}");
            }
        }

        // ── Public API: switch environment by scene name or comfort class ─
        public void SwitchToEnvironment(string name)
        {
            if (string.IsNullOrEmpty(name)) return;

            // Resolve name → EnvDef
            EnvDef env = null;

            // Try exact key first
            if (Environments.TryGetValue(name, out env))
            {
                // found
            }
            else
            {
                // Try case-insensitive match on sceneName or comfortClass
                string lower = name.Trim().ToLower();
                foreach (var kvp in Environments)
                {
                    if (kvp.Key.ToLower() == lower || kvp.Value.comfortClass == lower)
                    {
                        env = kvp.Value;
                        break;
                    }
                }
            }

            // Fallback to Pool
            if (env == null) env = Environments["Pool"];

            ApplyEnvironment(env);
            lastLoadedScene = env.sceneName;
            currentEnvironmentName = env.sceneName;
            currentComfortClass    = env.comfortClass;
            Debug.Log($"[SceneEnvironmentManager] → {env.sceneName} ({env.comfortClass})");
        }

        // ── Apply lighting + skybox for a given environment ─────────────
        private void ApplyEnvironment(EnvDef env)
        {
            // Lighting
            if (mainDirectionalLight != null)
            {
                mainDirectionalLight.color     = env.lightColor;
                mainDirectionalLight.intensity  = env.lightIntensity;
                mainDirectionalLight.transform.rotation = Quaternion.Euler(env.lightRotation);
            }

            // Ambient
            RenderSettings.ambientMode       = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor    = env.ambientSky;
            RenderSettings.ambientEquatorColor = env.ambientEquator;
            RenderSettings.ambientGroundColor  = env.ambientGround;

            // Fog
            RenderSettings.fog        = true;
            RenderSettings.fogMode    = FogMode.Exponential;
            RenderSettings.fogColor   = env.fogColor;
            RenderSettings.fogDensity = env.fogDensity;

            // Skybox texture
            Texture2D tex = GetTexture(env);
            if (tex != null && skyboxMat != null)
            {
                skyboxMat.mainTexture = tex;
                RenderSettings.skybox = skyboxMat;
                DynamicGI.UpdateEnvironment();
            }

            if (audioManager != null)
            {
                audioManager.PlaySound(env.sceneName);
            }
        }

        // ── Texture loading with RAM cache ───────────────────────────────
        private Texture2D GetTexture(EnvDef env)
        {
            // 1. RAM cache
            if (textureCache.TryGetValue(env.sceneName, out Texture2D cached))
                return cached;

            // 2. Try primary file
            Texture2D tex = LoadFromDisk(env.file);

            // 3. Try fallback file
            if (tex == null && !string.IsNullOrEmpty(env.fallbackFile))
                tex = LoadFromDisk(env.fallbackFile);

            // 4. Procedural fallback
            if (tex == null)
                tex = PanoramicSkyGenerator.GenerateGardenPanorama();

            if (tex != null)
                textureCache[env.sceneName] = tex;

            return tex;
        }

        private Texture2D LoadFromDisk(string filename)
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
                        tex.wrapMode   = TextureWrapMode.Repeat;
                        tex.filterMode = FilterMode.Bilinear;
                        Debug.Log($"[SceneEnvironmentManager] Loaded: {filename}");
                        return tex;
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[SceneEnvironmentManager] Cannot load {filename}: {ex.Message}");
            }
            return null;
        }

        private void OnDestroy()
        {
            foreach (var t in textureCache.Values)
                if (t != null) Destroy(t);
            textureCache.Clear();
            if (skyboxMat != null) Destroy(skyboxMat);
        }
    }
}
