using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// VitaVerse Phase 2 — Master Coordinator.
    ///
    /// Unity shows ONLY the full-screen 360° panorama.
    /// All clinician UI is on the browser at http://127.0.0.1:8000/demo
    ///
    /// This script:
    ///  1. Checks backend health on startup
    ///  2. Bridges ApiConnectionManager ↔ SceneEnvironmentManager
    ///  3. SceneEnvironmentManager polls /active-environment itself every 1.2s
    ///     so manual browser button presses auto-switch Unity scene too.
    /// </summary>
    public class ComfortManager : MonoBehaviour
    {
        [Header("Subsystems")]
        public ApiConnectionManager   apiManager;
        public SceneEnvironmentManager sceneManager;

        [Header("State (Read-Only)")]
        public string activeComfortClass = "calm";
        public string activeScenePreset  = "Pool";

        private void Start()
        {
            if (apiManager   == null) apiManager   = GetComponent<ApiConnectionManager>();
            if (sceneManager == null) sceneManager = GetComponent<SceneEnvironmentManager>();

            CheckBackendConnection();
        }

        public void CheckBackendConnection()
        {
            if (apiManager == null) return;

            apiManager.CheckApiHealth((success, msg) =>
            {
                if (success)
                    Debug.Log($"[ComfortManager] Backend connected: {msg}");
                else
                    Debug.LogWarning($"[ComfortManager] Backend offline: {msg} — SceneManager will retry via poll.");
            });
        }

        /// <summary>
        /// Trigger a predict call from scene scripting if needed.
        /// In Phase 2, the browser console is the primary input.
        /// </summary>
        public void RequestPrediction(PatientPredictionRequest request)
        {
            if (apiManager == null)
            {
                Debug.LogError("[ComfortManager] ApiConnectionManager not configured.");
                return;
            }

            apiManager.PredictComfort(
                request,
                onSuccess: HandlePredictionSuccess,
                onError:   HandlePredictionError
            );
        }

        private void HandlePredictionSuccess(PatientPredictionResponse response)
        {
            activeComfortClass = response.comfort_class;
            activeScenePreset  = response.scene;

            Debug.Log($"[ComfortManager] Prediction: class='{response.comfort_class}', " +
                      $"scene='{response.scene}', conf={response.confidence * 100:F1}%");

            if (sceneManager != null)
                sceneManager.SwitchToEnvironment(response.scene);
        }

        private void HandlePredictionError(string errorMessage)
        {
            Debug.LogError($"[ComfortManager] Prediction failed: {errorMessage}");
        }

        public void ManualSwitchScene(string targetScene)
        {
            if (sceneManager != null)
                sceneManager.SwitchToEnvironment(targetScene);

            Debug.Log($"[ComfortManager] Manual switch → {targetScene}");
        }
    }
}
