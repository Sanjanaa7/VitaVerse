#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using VitaVerse;

namespace VitaVerse.Editor
{
    /// <summary>
    /// One-click scene setup for VitaVerse Phase 2.
    ///
    /// Phase 2 architecture:
    ///   • Unity shows ONLY the full-screen 360° panorama — no HUD overlay.
    ///   • All clinician UI is in the browser at http://127.0.0.1:8000/demo
    ///   • SceneEnvironmentManager polls /active-environment every 1.2s and
    ///     auto-switches between all 7 panorama environments.
    ///   • All 7 panoramas load from disk at runtime — nothing assigned in Inspector.
    /// </summary>
    public static class VitaVerseSceneSetup
    {
        [MenuItem("VitaVerse/Auto-Setup Scene (One-Click)")]
        public static void SetupFullScene()
        {
            Debug.Log("[VitaVerse] Setting up Phase 2 scene...");

            // ── 1. Clean up any Phase 1 GameObjects ──────────────────────
            string[] toClean = {
                "VitaVerse_Canvas", "EventSystem", "VitaVerse_SystemManager"
            };
            foreach (var name in toClean)
            {
                var obj = GameObject.Find(name);
                if (obj != null) Object.DestroyImmediate(obj);
            }

            // ── 2. VR Viewing Camera ──────────────────────────────────────
            Camera cam = Camera.main;
            if (cam == null)
            {
                GameObject camObj = new GameObject("Main Camera");
                cam = camObj.AddComponent<Camera>();
                camObj.tag = "MainCamera";
            }
            cam.transform.position = new Vector3(0f, 1.4f, 0f);
            cam.transform.rotation = Quaternion.identity;
            cam.clearFlags         = CameraClearFlags.Skybox;
            cam.nearClipPlane      = 0.05f;
            cam.farClipPlane       = 1000f;
            cam.fieldOfView        = 80f;

            if (cam.GetComponent<VRCameraController>() == null)
                cam.gameObject.AddComponent<VRCameraController>();

            // ── 3. Directional Light ──────────────────────────────────────
#if UNITY_2023_1_OR_NEWER
            Light dirLight = Object.FindAnyObjectByType<Light>();
#else
            Light dirLight = Object.FindObjectOfType<Light>();
#endif
            if (dirLight == null || dirLight.type != LightType.Directional)
            {
                GameObject lo = new GameObject("Directional Light");
                dirLight      = lo.AddComponent<Light>();
                dirLight.type = LightType.Directional;
            }
            dirLight.color                = new Color(1.0f, 0.96f, 0.88f);
            dirLight.intensity            = 1.05f;
            dirLight.transform.rotation   = Quaternion.Euler(48f, -30f, 0f);

            // ── 4. System Manager GameObject ─────────────────────────────
            GameObject master = GameObject.Find("VitaVerse_SystemManager")
                             ?? new GameObject("VitaVerse_SystemManager");

            ApiConnectionManager apiMgr = master.GetComponent<ApiConnectionManager>()
                                       ?? master.AddComponent<ApiConnectionManager>();

            SceneEnvironmentManager sceneMgr = master.GetComponent<SceneEnvironmentManager>()
                                            ?? master.AddComponent<SceneEnvironmentManager>();
            sceneMgr.mainDirectionalLight = dirLight;

            ComfortManager comfortMgr = master.GetComponent<ComfortManager>()
                                     ?? master.AddComponent<ComfortManager>();
            comfortMgr.apiManager   = apiMgr;
            comfortMgr.sceneManager = sceneMgr;

            // ── 5. Load initial environment ───────────────────────────────
            sceneMgr.SwitchToEnvironment("Pool");

            Debug.Log("[VitaVerse] Phase 2 scene setup complete.");
            EditorUtility.DisplayDialog(
                "VitaVerse Phase 2 — Setup Complete ✓",
                "Scene configured for 360° VR Streaming.\n\n" +
                "7 ENVIRONMENTS (auto-loaded at runtime):\n" +
                "  CALM    → Tranquil Pool\n" +
                "  CALM    → Blue Lagoon\n" +
                "  ADJUST  → Umhlanga Beach Sunrise\n" +
                "  ADJUST  → Rogaland Night Sky\n" +
                "  ADJUST  → Sky on Fire Sunset\n" +
                "  SUPPORT → Kerala Heritage Home\n" +
                "  SUPPORT → Misty Pine Forest\n\n" +
                "DUAL-SCREEN SETUP:\n" +
                "  • Browser → http://127.0.0.1:8000/demo\n" +
                "  • Unity shows only the 360° panorama\n" +
                "  • Click any environment card in browser to stream\n\n" +
                "CONTROLS in Play Mode:\n" +
                "  Mouse drag → Look 360°\n" +
                "  WASD / Arrow keys → Pan & tilt\n" +
                "  [R] → Reset view",
                "Got it — Press Play!");
        }
    }
}
#endif
