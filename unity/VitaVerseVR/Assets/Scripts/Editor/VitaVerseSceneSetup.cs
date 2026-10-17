#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;
using VitaVerse;

namespace VitaVerse.Editor
{
    /// <summary>
    /// One-click scene setup for VitaVerse AI 360 Panorama Experience.
    /// Creates Camera, Lighting, System Manager, and Clinical HUD.
    /// Auto-detects any garden_360 / forest_360 / sunset_360 images in Assets.
    /// </summary>
    public static class VitaVerseSceneSetup
    {
        [MenuItem("VitaVerse/Auto-Setup Scene (One-Click)")]
        public static void SetupFullScene()
        {
            Debug.Log("[VitaVerse] Setting up AI 360 Panorama scene...");

            // ── 1. Stationary VR Viewing Camera ──────────────────────
            Camera cam = Camera.main;
            if (cam == null)
            {
                GameObject camObj = new GameObject("Main Camera");
                cam = camObj.AddComponent<Camera>();
                camObj.tag = "MainCamera";
            }
            cam.transform.position = new Vector3(0f, 1.4f, 0f);
            cam.transform.rotation = Quaternion.identity;
            cam.clearFlags = CameraClearFlags.Skybox;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 1000f;
            cam.fieldOfView = 80f;

            if (cam.GetComponent<VRCameraController>() == null)
                cam.gameObject.AddComponent<VRCameraController>();

            // ── 2. Directional Light ──────────────────────────────────
#if UNITY_2023_1_OR_NEWER
            Light dirLight = Object.FindAnyObjectByType<Light>();
#else
            Light dirLight = Object.FindObjectOfType<Light>();
#endif
            if (dirLight == null || dirLight.type != LightType.Directional)
            {
                GameObject lo = new GameObject("Directional Light");
                dirLight = lo.AddComponent<Light>();
                dirLight.type = LightType.Directional;
            }
            dirLight.color = new Color(1.0f, 0.96f, 0.88f);
            dirLight.intensity = 1.05f;
            dirLight.transform.rotation = Quaternion.Euler(48f, -30f, 0f);

            // ── 3. System Manager ─────────────────────────────────────
            GameObject master = GameObject.Find("VitaVerse_SystemManager")
                                ?? new GameObject("VitaVerse_SystemManager");

            ComfortManager comfortMgr = master.GetComponent<ComfortManager>()
                                        ?? master.AddComponent<ComfortManager>();

            ApiConnectionManager apiMgr = master.GetComponent<ApiConnectionManager>()
                                          ?? master.AddComponent<ApiConnectionManager>();

            SceneEnvironmentManager sceneMgr = master.GetComponent<SceneEnvironmentManager>()
                                               ?? master.AddComponent<SceneEnvironmentManager>();
            sceneMgr.mainDirectionalLight = dirLight;

            // Auto-assign any 360 panorama images already in the project
            AssignPanoramaImages(sceneMgr);

            comfortMgr.apiManager  = apiMgr;
            comfortMgr.sceneManager = sceneMgr;

            // ── 4. Canvas & Healthcare HUD ────────────────────────────
#if UNITY_2023_1_OR_NEWER
            Canvas canvas = Object.FindAnyObjectByType<Canvas>();
#else
            Canvas canvas = Object.FindObjectOfType<Canvas>();
#endif
            if (canvas == null)
            {
                GameObject co = new GameObject("VitaVerse_Canvas");
                canvas = co.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                var scaler = co.AddComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1366, 768);
                scaler.matchWidthOrHeight = 0.5f;
                scaler.dynamicPixelsPerUnit = 2f;
                co.AddComponent<GraphicRaycaster>();
            }
            else
            {
                var scaler = canvas.GetComponent<CanvasScaler>();
                if (scaler != null)
                {
                    scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                    scaler.referenceResolution = new Vector2(1366, 768);
                    scaler.matchWidthOrHeight = 0.5f;
                    scaler.dynamicPixelsPerUnit = 2f;
                }
            }

            // Safe EventSystem with support for both Old and New Input System
            GameObject esObj = GameObject.Find("EventSystem");
            if (esObj == null) esObj = new GameObject("EventSystem");

            if (esObj.GetComponent<UnityEngine.EventSystems.EventSystem>() == null)
                esObj.AddComponent<UnityEngine.EventSystems.EventSystem>();

            var newModType = System.Type.GetType("UnityEngine.InputSystem.UI.InputSystemUIInputModule, Unity.InputSystem");
            if (newModType != null)
            {
                var oldMod = esObj.GetComponent<UnityEngine.EventSystems.StandaloneInputModule>();
                if (oldMod != null) Object.DestroyImmediate(oldMod);
                if (esObj.GetComponent(newModType) == null)
                    esObj.AddComponent(newModType);
            }
            else
            {
                if (esObj.GetComponent<UnityEngine.EventSystems.StandaloneInputModule>() == null)
                    esObj.AddComponent<UnityEngine.EventSystems.StandaloneInputModule>();
            }

            HealthcareHUD hud = canvas.GetComponent<HealthcareHUD>()
                                ?? canvas.gameObject.AddComponent<HealthcareHUD>();
            hud.comfortManager = comfortMgr;
            comfortMgr.hud = hud;

            // ── 5. Apply initial environment ──────────────────────────
            sceneMgr.SwitchToEnvironment("Pool");

            Debug.Log("[VitaVerse] Setup complete.");
            EditorUtility.DisplayDialog(
                "VitaVerse — Setup Complete ✓",
                "Scene is ready with 360° Panoramas!\n\n" +
                "ENVIRONMENTS ACTIVE:\n" +
                "1. Calm    → Tranquil Pool (pool_360.jpg)\n" +
                "2. Adjust  → Umhlanga Beach Sunrise (beach_360.jpg)\n" +
                "3. Support → Kerala Heritage Home (home_360.jpg)\n\n" +
                "CONTROLS when in Play Mode:\n" +
                "• Mouse drag → Look 360°\n" +
                "• Arrow Keys / WASD → Pan & tilt\n" +
                "• [H] → Toggle HUD\n" +
                "• [R] → Reset view",
                "Got it — Press Play!");
        }

        private static void AssignPanoramaImages(SceneEnvironmentManager mgr)
        {
            mgr.aiPoolPanorama = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Panoramas/pool_360.jpg");
            if (mgr.aiPoolPanorama == null) mgr.aiPoolPanorama = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Panoramas/pool_8k.exr");
            if (mgr.aiPoolPanorama == null) TryAssign("pool", ref mgr.aiPoolPanorama);

            mgr.aiBeachPanorama = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Panoramas/beach_360.jpg");
            if (mgr.aiBeachPanorama == null) mgr.aiBeachPanorama = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Panoramas/umhlanga_sunrise_8k.exr");
            if (mgr.aiBeachPanorama == null) TryAssign("beach", ref mgr.aiBeachPanorama);

            mgr.aiHomePanorama = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Panoramas/home_360.jpg");
            if (mgr.aiHomePanorama == null) TryAssign("home", ref mgr.aiHomePanorama);

            EditorUtility.SetDirty(mgr);
            Debug.Log($"[VitaVerse] Panoramas assigned: Pool={(mgr.aiPoolPanorama != null)}, Beach={(mgr.aiBeachPanorama != null)}, Home={(mgr.aiHomePanorama != null)}");
        }

        private static void TryAssign(string assetName, ref Texture2D field)
        {
            string[] guids = AssetDatabase.FindAssets($"{assetName} t:Texture2D");
            if (guids.Length > 0)
            {
                string path = AssetDatabase.GUIDToAssetPath(guids[0]);
                Texture2D tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (tex != null)
                {
                    field = tex;
                    Debug.Log($"[VitaVerse] Auto-assigned panorama: {path}");
                }
            }
        }
    }
}
#endif
