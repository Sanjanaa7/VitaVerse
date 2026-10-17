using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// Master coordinator for the VitaVerse Phase 1 system.
    /// Bridges Healthcare HUD, API network calls, Comfort ML inference, and 360° Panorama switching.
    /// </summary>
    public class ComfortManager : MonoBehaviour
    {
        [Header("Subsystems")]
        public ApiConnectionManager apiManager;
        public SceneEnvironmentManager sceneManager;
        public HealthcareHUD hud;

        [Header("State")]
        public string activeComfortClass = "calm";
        public string activeScenePreset = "Pool";

        private void Start()
        {
            if (apiManager == null) apiManager = GetComponent<ApiConnectionManager>();
            if (sceneManager == null) sceneManager = GetComponent<SceneEnvironmentManager>();
#if UNITY_2023_1_OR_NEWER
            if (hud == null) hud = FindAnyObjectByType<HealthcareHUD>();
#else
            if (hud == null) hud = FindObjectOfType<HealthcareHUD>();
#endif
            CheckBackendConnection();
        }

        public void CheckBackendConnection()
        {
            if (apiManager != null)
            {
                hud?.SetStatusMessage("Connecting to local AI model (http://127.0.0.1:8000)...");
                apiManager.CheckApiHealth((success, msg) =>
                {
                    if (success)
                    {
                        hud?.SetStatusMessage($"[Connected] {msg}");
                    }
                    else
                    {
                        hud?.SetStatusMessage($"[Offline] {msg}");
                    }
                });
            }
        }

        public void RequestPrediction(PatientPredictionRequest request)
        {
            if (apiManager == null)
            {
                hud?.SetStatusMessage("Error: ApiConnectionManager not configured.");
                return;
            }

            apiManager.PredictComfort(
                request,
                onSuccess: HandlePredictionSuccess,
                onError: HandlePredictionError
            );
        }

        private void HandlePredictionSuccess(PatientPredictionResponse response)
        {
            activeComfortClass = response.comfort_class;
            activeScenePreset = response.scene;

            Debug.Log($"[ComfortManager] Prediction: class='{response.comfort_class}', scene='{response.scene}', conf={response.confidence * 100:F1}%");

            // 1. Switch 360° AI Panorama environment
            if (sceneManager != null)
            {
                sceneManager.SwitchToEnvironment(response.scene);
            }

            // 2. Update Healthcare HUD
            if (hud != null)
            {
                hud.UpdateResult(response.comfort_class, response.scene, response.confidence, response.safety_advisory);
            }
        }

        private void HandlePredictionError(string errorMessage)
        {
            Debug.LogError($"[ComfortManager] Prediction failed: {errorMessage}");
            if (hud != null)
            {
                hud.SetStatusMessage($"Request Failed: {errorMessage}");
            }
        }

        public void ManualSwitchScene(string targetScene)
        {
            if (sceneManager != null)
            {
                sceneManager.SwitchToEnvironment(targetScene);
            }
            if (hud != null)
            {
                hud.SetStatusMessage($"Manual Environment: {targetScene}");
            }
        }
    }
}
