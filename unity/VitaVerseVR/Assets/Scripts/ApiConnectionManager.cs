using System;
using System.Text;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace VitaVerse
{
    [System.Serializable]
    public class PatientPredictionRequest
    {
        public float spo2;
        public float hr;
        public float hrv;
    }

    [System.Serializable]
    public class PatientPredictionResponse
    {
        public string comfort_class;
        public string scene;
        public string scene_description;
        public float confidence;
        public bool demo_only;
        public string message;
        public string safety_advisory;
        public string timestamp;
    }

    [System.Serializable]
    public class HealthResponse
    {
        public string status;
        public bool model_loaded;
        public string model_type;
    }

    /// <summary>
    /// Manages network communication between the Unity VR client and the local Python FastAPI backend.
    /// Runs strictly on localhost (http://127.0.0.1:8000).
    /// </summary>
    public class ApiConnectionManager : MonoBehaviour
    {
        [Header("API Configuration")]
        [Tooltip("Base URL for the local Python FastAPI service.")]
        public string baseUrl = "http://127.0.0.1:8000";

        [Tooltip("Request timeout in seconds.")]
        public int timeoutSeconds = 6;

        public bool IsBusy { get; private set; } = false;

        /// <summary>
        /// Sends an asynchronous health check to the Python backend.
        /// </summary>
        public void CheckApiHealth(Action<bool, string> callback)
        {
            StartCoroutine(CheckHealthRoutine(callback));
        }

        private IEnumerator CheckHealthRoutine(Action<bool, string> callback)
        {
            string url = $"{baseUrl}/health";
            using (UnityWebRequest req = UnityWebRequest.Get(url))
            {
                req.timeout = timeoutSeconds;
                yield return req.SendWebRequest();

                if (req.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        HealthResponse resp = JsonUtility.FromJson<HealthResponse>(req.downloadHandler.text);
                        if (resp != null && resp.model_loaded)
                        {
                            callback?.Invoke(true, "Backend Connected (Model Ready)");
                        }
                        else
                        {
                            callback?.Invoke(false, "Backend Connected, but Model is not loaded.");
                        }
                    }
                    catch (Exception)
                    {
                        callback?.Invoke(true, "Backend Online");
                    }
                }
                else
                {
                    string err = req.error;
                    if (req.result == UnityWebRequest.Result.ConnectionError)
                    {
                        err = "Unable to connect to 127.0.0.1:8000. Is run_backend.bat running?";
                    }
                    callback?.Invoke(false, err);
                }
            }
        }

        /// <summary>
        /// Sends physiological parameters to /predict and receives comfort classification & scene mapping.
        /// </summary>
        public void PredictComfort(
            PatientPredictionRequest requestData,
            Action<PatientPredictionResponse> onSuccess,
            Action<string> onError)
        {
            if (IsBusy)
            {
                onError?.Invoke("A prediction request is already in progress. Please wait.");
                return;
            }

            StartCoroutine(PredictRoutine(requestData, onSuccess, onError));
        }

        private IEnumerator PredictRoutine(
            PatientPredictionRequest requestData,
            Action<PatientPredictionResponse> onSuccess,
            Action<string> onError)
        {
            IsBusy = true;
            string url = $"{baseUrl}/predict";
            string jsonBody = JsonUtility.ToJson(requestData);

            using (UnityWebRequest req = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                req.uploadHandler = new UploadHandlerRaw(bodyRaw);
                req.downloadHandler = new DownloadHandlerBuffer();
                req.SetRequestHeader("Content-Type", "application/json");
                req.timeout = timeoutSeconds;

                yield return req.SendWebRequest();

                IsBusy = false;

                if (req.result == UnityWebRequest.Result.Success)
                {
                    string responseText = req.downloadHandler.text;
                    try
                    {
                        PatientPredictionResponse resp = JsonUtility.FromJson<PatientPredictionResponse>(responseText);
                        if (resp != null && !string.IsNullOrEmpty(resp.comfort_class))
                        {
                            onSuccess?.Invoke(resp);
                        }
                        else
                        {
                            onError?.Invoke("Received malformed prediction data from server.");
                        }
                    }
                    catch (Exception ex)
                    {
                        onError?.Invoke($"Failed to parse JSON response: {ex.Message}");
                    }
                }
                else
                {
                    string errorDetail = req.error;
                    if (req.responseCode == 422)
                    {
                        errorDetail = $"Validation Error (422): Physiological values outside acceptable bounds.\n{req.downloadHandler.text}";
                    }
                    else if (req.responseCode == 503)
                    {
                        errorDetail = "Service Unavailable (503): Model file is missing or still loading.";
                    }
                    else if (req.result == UnityWebRequest.Result.ConnectionError)
                    {
                        errorDetail = "Connection Error: Cannot reach local Python backend on http://127.0.0.1:8000.\nPlease launch run_backend.bat first.";
                    }
                    onError?.Invoke(errorDetail);
                }
            }
        }
    }
}
