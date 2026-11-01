using System;
using UnityEngine;
using UnityEngine.UI;

namespace VitaVerse
{
    /// <summary>
    /// Professional glassmorphic clinical biofeedback HUD for VitaVerse.
    /// Features vital sign monitors (SpO2, HR, HRV), real-time color-coded ranges,
    /// animated heart rate pulse, scenario pills, high-visibility text, and one-click Hide/Show controls.
    /// Compatible with both standard and new Unity Input Systems.
    /// </summary>
    public class HealthcareHUD : MonoBehaviour
    {
        [Header("Manager Reference")]
        public ComfortManager comfortManager;

        [Header("State")]
        public float spo2Value = 98.0f;
        public float hrValue = 72.0f;
        public float hrvValue = 65.0f;

        [Header("UI Visibility")]
        public bool isVisible = true;
        public KeyCode toggleKey = KeyCode.H;

        // Dynamic UI Component References
        private GameObject hudPanel;
        private GameObject floatingShowBtn;
        private Slider spo2Slider;
        private Slider hrSlider;
        private Slider hrvSlider;
        private Text spo2Text;
        private Text hrText;
        private Text hrvText;
        private Text statusMessageText;
        private Text resultBadgeText;
        private Text resultSceneText;
        private Text confidenceText;
        private GameObject safetyBanner;
        private Text safetyBannerText;
        private Image resultBadgeBg;
        private Button predictBtn;
        private Text predictBtnText;

        // Animated heart pulse
        private float heartBeatTimer = 0f;
        private RectTransform heartIconTransform;

        private void Awake()
        {
            FixEventSystemInputModule();
        }

        private void Start()
        {
#if UNITY_2023_1_OR_NEWER
            if (comfortManager == null) comfortManager = FindAnyObjectByType<ComfortManager>();
#else
            if (comfortManager == null) comfortManager = FindObjectOfType<ComfortManager>();
#endif

            // Configure canvas scaler for crisp, high-visibility rendering
            CanvasScaler scaler = GetComponentInParent<CanvasScaler>();
            if (scaler != null)
            {
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1366, 768);
                scaler.matchWidthOrHeight = 0.5f;
                scaler.dynamicPixelsPerUnit = 2f;
            }

            BuildModernHUD();
        }

        private void FixEventSystemInputModule()
        {
            try
            {
#if UNITY_2023_1_OR_NEWER
                var es = FindAnyObjectByType<UnityEngine.EventSystems.EventSystem>();
#else
                var es = FindObjectOfType<UnityEngine.EventSystems.EventSystem>();
#endif
                if (es != null)
                {
                    var newModType = Type.GetType("UnityEngine.InputSystem.UI.InputSystemUIInputModule, Unity.InputSystem");
                    if (newModType != null)
                    {
                        var oldMod = es.GetComponent<UnityEngine.EventSystems.StandaloneInputModule>();
                        if (oldMod != null)
                        {
                            Destroy(oldMod);
                            es.gameObject.AddComponent(newModType);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[HealthcareHUD] EventSystem check: {ex.Message}");
            }
        }

        private void Update()
        {
            heartBeatTimer += Time.deltaTime * (hrValue / 60.0f) * 2.0f;
            if (heartIconTransform != null)
            {
                float scale = 1.0f + Mathf.Sin(heartBeatTimer * Mathf.PI) * 0.12f;
                heartIconTransform.localScale = new Vector3(scale, scale, 1.0f);
            }
        }

        private void OnGUI()
        {
            Event e = Event.current;
            if (e != null && e.type == EventType.KeyDown)
            {
                if (e.keyCode == toggleKey)
                {
                    ToggleVisibility();
                }
                else if (e.keyCode == KeyCode.Escape)
                {
                    OnStopClicked();
                }
            }
        }

        public void ToggleVisibility()
        {
            SetUIVisible(!isVisible);
        }

        public void SetUIVisible(bool visible)
        {
            isVisible = visible;
            if (hudPanel != null) hudPanel.SetActive(isVisible);
            if (floatingShowBtn != null) floatingShowBtn.SetActive(!isVisible);
        }

        public void OnStopClicked()
        {
            comfortManager?.ManualSwitchScene("Pool");
            SetStatusMessage("Session paused. Rest environment activated.");
        }

        public void LoadScenario(float spo2, float hr, float hrv)
        {
            spo2Value = spo2;
            hrValue = hr;
            hrvValue = hrv;

            if (spo2Slider != null) spo2Slider.value = spo2;
            if (hrSlider != null) hrSlider.value = hr;
            if (hrvSlider != null) hrvSlider.value = hrv;

            UpdateVitalLabels();
            SetStatusMessage("Loaded simulated demo scenario. Ready to predict.");
        }

        public void RequestPrediction()
        {
            if (predictBtn != null) predictBtn.interactable = false;
            if (predictBtnText != null) predictBtnText.text = "ANALYZING VITALS...";
            SetStatusMessage("Querying local AI model (127.0.0.1:8000)...");

            PatientPredictionRequest req = new PatientPredictionRequest
            {
                spo2 = (float)Math.Round(spo2Value, 1),
                hr = (float)Math.Round(hrValue, 0),
                hrv = (float)Math.Round(hrvValue, 0)
            };

            comfortManager?.RequestPrediction(req);
        }

        public void UpdateResult(string comfortClass, string sceneName, float confidence, string safetyAlert)
        {
            if (predictBtn != null) predictBtn.interactable = true;
            if (predictBtnText != null) predictBtnText.text = "PREDICT COMFORT LEVEL  ►";

            string cls = comfortClass.ToUpper();
            if (resultBadgeText != null) resultBadgeText.text = $"COMFORT CLASSIFICATION:  {cls}";
            if (resultSceneText != null) resultSceneText.text = $"Active 360° Scene:  <b>{sceneName}</b>  ({confidence * 100:F1}% confidence)";
            if (confidenceText != null) confidenceText.text = $"Confidence: {confidence * 100:F1}%";

            // Update badge color glow
            if (resultBadgeBg != null)
            {
                if (cls == "CALM")
                    resultBadgeBg.color = new Color(0.06f, 0.45f, 0.28f, 0.95f);
                else if (cls == "ADJUST")
                    resultBadgeBg.color = new Color(0.10f, 0.35f, 0.65f, 0.95f);
                else
                    resultBadgeBg.color = new Color(0.60f, 0.32f, 0.08f, 0.95f);
            }

            // Safety alert banner
            bool hasAlert = !string.IsNullOrEmpty(safetyAlert);
            if (safetyBanner != null) safetyBanner.SetActive(hasAlert);
            if (safetyBannerText != null) safetyBannerText.text = safetyAlert;

            SetStatusMessage($"AI matched comfort state '{cls}' $\\rightarrow$ Environment: {sceneName}");
        }

        public void SetStatusMessage(string msg)
        {
            if (statusMessageText != null) statusMessageText.text = msg;
        }

        private void UpdateVitalLabels()
        {
            if (spo2Text != null)
            {
                string status = (spo2Value >= 95f) ? "<color=#34d399>Optimal</color>" : (spo2Value >= 92f) ? "<color=#fbbf24>Borderline</color>" : "<color=#ef4444>Critical</color>";
                spo2Text.text = $"<b>SpO₂ Saturation:</b>  <color=#38bdf8>{spo2Value:F1}%</color>  ({status})";
            }
            if (hrText != null)
            {
                string status = (hrValue <= 80f && hrValue >= 60f) ? "<color=#34d399>Resting</color>" : (hrValue > 95f) ? "<color=#ef4444>Elevated</color>" : "<color=#60a5fa>Normal</color>";
                hrText.text = $"<b>Heart Rate:</b>  <color=#f43f5e>{hrValue:F0} BPM</color>  ({status})";
            }
            if (hrvText != null)
            {
                string tone = (hrvValue >= 50f) ? "<color=#34d399>High Tone</color>" : (hrvValue >= 30f) ? "<color=#60a5fa>Moderate</color>" : "<color=#f59e0b>Low Tone</color>";
                hrvText.text = $"<b>Heart Rate Variability (HRV):</b>  <color=#a78bfa>{hrvValue:F0} ms</color>  ({tone})";
            }
        }

        #region Procedural UI Hierarchy Builder
        private void BuildModernHUD()
        {
            Canvas canvas = GetComponent<Canvas>();
            if (canvas == null) return;

            // Sprites
            Sprite panelSprite = UIAssetGenerator.CreateGlowBorderSprite(128, 128, 16, 2, new Color(0.25f, 0.55f, 0.90f, 0.85f), new Color(0.06f, 0.10f, 0.17f, 0.96f));
            Sprite buttonSprite = UIAssetGenerator.CreateRoundedRectSprite(64, 64, 10, new Color(0.14f, 0.55f, 0.95f, 1f));
            Sprite pillSprite = UIAssetGenerator.CreateRoundedRectSprite(64, 64, 8, new Color(0.12f, 0.18f, 0.28f, 0.95f));
            Sprite badgeSprite = UIAssetGenerator.CreateGlowBorderSprite(64, 64, 10, 2, new Color(0.30f, 0.70f, 0.90f, 0.8f), new Color(0.08f, 0.14f, 0.24f, 0.95f));
            Sprite circleKnob = UIAssetGenerator.CreateCircleSprite(28, Color.white);
            Sprite closeBtnSprite = UIAssetGenerator.CreateCircleSprite(32, new Color(0.25f, 0.32f, 0.45f, 0.95f));

            // Unity 6+ removed Arial.ttf and throws ArgumentException — must use LegacyRuntime.ttf
            Font defaultFont = null;
            try { defaultFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf"); } catch {}
            if (defaultFont == null)
            {
                try { defaultFont = Resources.GetBuiltinResource<Font>("Arial.ttf"); } catch {}
            }
            if (defaultFont == null)
            {
                try { defaultFont = Resources.FindObjectsOfTypeAll<Font>()[0]; } catch {}
            }
            if (defaultFont == null) Debug.LogWarning("[HealthcareHUD] No font found — text may not render.");

            // ── 1. Floating Persistent "SHOW UI" Pill (visible when HUD is closed) ──
            floatingShowBtn = CreateUIElement("FloatingShowBtn", canvas.transform, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(25f, -25f), new Vector2(160f, 40f));
            Button showBtn = floatingShowBtn.AddComponent<Button>();
            Image showImg = floatingShowBtn.AddComponent<Image>();
            showImg.sprite = pillSprite;
            showImg.type = Image.Type.Sliced;
            showImg.color = new Color(0.08f, 0.14f, 0.24f, 0.95f);

            GameObject showTxtObj = CreateUIElement("Text", floatingShowBtn.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            Text showTxt = showTxtObj.AddComponent<Text>();
            showTxt.font = defaultFont;
            showTxt.fontSize = 13;
            showTxt.fontStyle = FontStyle.Bold;
            showTxt.color = new Color(0.38f, 0.82f, 1.0f);
            showTxt.alignment = TextAnchor.MiddleCenter;
            showTxt.text = "👁  SHOW HUD [H]";
            showBtn.onClick.AddListener(() => SetUIVisible(true));
            floatingShowBtn.SetActive(false); // starts hidden while HUD is open

            // ── 2. Main High-Visibility Dashboard Card ──
            hudPanel = new GameObject("ModernHUD_Card");
            hudPanel.transform.SetParent(canvas.transform, false);

            RectTransform rtPanel = hudPanel.AddComponent<RectTransform>();
            rtPanel.anchorMin = new Vector2(0f, 0.5f);
            rtPanel.anchorMax = new Vector2(0f, 0.5f);
            rtPanel.pivot = new Vector2(0f, 0.5f);
            rtPanel.anchoredPosition = new Vector2(25f, 0f);
            rtPanel.sizeDelta = new Vector2(460f, 660f);

            Image panelImg = hudPanel.AddComponent<Image>();
            panelImg.sprite = panelSprite;
            panelImg.type = Image.Type.Sliced;

            // ── 3. Close / Hide Button on Card (Top Right) ──
            GameObject closeBtnObj = CreateUIElement("CloseButton", hudPanel.transform, new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(-15f, -15f), new Vector2(32f, 32f));
            Button closeBtn = closeBtnObj.AddComponent<Button>();
            Image closeImg = closeBtnObj.AddComponent<Image>();
            closeImg.sprite = closeBtnSprite;
            closeImg.color = new Color(0.20f, 0.28f, 0.40f, 0.95f);

            GameObject closeTxtObj = CreateUIElement("CloseText", closeBtnObj.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            Text closeTxt = closeTxtObj.AddComponent<Text>();
            closeTxt.font = defaultFont;
            closeTxt.fontSize = 16;
            closeTxt.fontStyle = FontStyle.Bold;
            closeTxt.color = Color.white;
            closeTxt.alignment = TextAnchor.MiddleCenter;
            closeTxt.text = "✕";
            closeBtn.onClick.AddListener(() => SetUIVisible(false));

            // ── 4. Card Header ──
            GameObject headerObj = CreateUIElement("Header", hudPanel.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0f, 1f), new Vector2(24f, -18f), new Vector2(-70f, 50f));
            Text titleTxt = headerObj.AddComponent<Text>();
            titleTxt.font = defaultFont;
            titleTxt.fontSize = 20;
            titleTxt.fontStyle = FontStyle.Bold;
            titleTxt.color = Color.white;
            titleTxt.horizontalOverflow = HorizontalWrapMode.Overflow;
            titleTxt.verticalOverflow = VerticalWrapMode.Overflow;
            titleTxt.text = "VitaVerse  <size=12><color=#38bdf8>CLINICAL VR CONSOLE</color></size>\n<size=11><color=#94a3b8>AI Adaptive Comfort & Distraction</color></size>";

            // ── 5. Vitals Sliders (Generous Spacing, Big Fonts) ──
            float startY = -82f;
            float spacingY = 64f;

            // SpO2
            spo2Slider = CreateVitalSlider("SpO2", hudPanel.transform, new Vector2(24f, startY), "SpO₂ Saturation", 70f, 100f, spo2Value, new Color(0.06f, 0.78f, 0.58f), circleKnob, defaultFont, out spo2Text);
            spo2Slider.onValueChanged.AddListener((v) => { spo2Value = v; UpdateVitalLabels(); });

            // HR
            hrSlider = CreateVitalSlider("HR", hudPanel.transform, new Vector2(24f, startY - spacingY), "Heart Rate", 40f, 180f, hrValue, new Color(0.96f, 0.28f, 0.40f), circleKnob, defaultFont, out hrText);
            hrSlider.onValueChanged.AddListener((v) => { hrValue = v; UpdateVitalLabels(); });

            // HRV
            hrvSlider = CreateVitalSlider("HRV", hudPanel.transform, new Vector2(24f, startY - spacingY * 2), "HRV Index", 5f, 180f, hrvValue, new Color(0.60f, 0.45f, 0.98f), circleKnob, defaultFont, out hrvText);
            hrvSlider.onValueChanged.AddListener((v) => { hrvValue = v; UpdateVitalLabels(); });

            UpdateVitalLabels();

            // ── 6. Predict Button (Large & Bold) ──
            float btnY = startY - spacingY * 3 - 6f;
            GameObject btnObj = CreateUIElement("PredictButton", hudPanel.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, btnY), new Vector2(-48f, 44f));
            predictBtn = btnObj.AddComponent<Button>();
            Image btnImg = btnObj.AddComponent<Image>();
            btnImg.sprite = buttonSprite;
            btnImg.type = Image.Type.Sliced;
            btnImg.color = new Color(0.12f, 0.55f, 0.96f);

            GameObject btnTxtObj = CreateUIElement("BtnText", btnObj.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            predictBtnText = btnTxtObj.AddComponent<Text>();
            predictBtnText.font = defaultFont;
            predictBtnText.fontSize = 14;
            predictBtnText.fontStyle = FontStyle.Bold;
            predictBtnText.alignment = TextAnchor.MiddleCenter;
            predictBtnText.color = Color.white;
            predictBtnText.horizontalOverflow = HorizontalWrapMode.Overflow;
            predictBtnText.text = "PREDICT COMFORT LEVEL  ►";
            predictBtn.onClick.AddListener(RequestPrediction);

            // ── 7. Clinical Scenarios Header ──
            float scnTitleY = btnY - 50f;
            GameObject scnTitleObj = CreateUIElement("ScenariosLabel", hudPanel.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, scnTitleY), new Vector2(-48f, 20f));
            Text scnTitleTxt = scnTitleObj.AddComponent<Text>();
            scnTitleTxt.font = defaultFont;
            scnTitleTxt.fontSize = 12;
            scnTitleTxt.fontStyle = FontStyle.Bold;
            scnTitleTxt.color = new Color(0.55f, 0.78f, 0.98f);
            scnTitleTxt.horizontalOverflow = HorizontalWrapMode.Overflow;
            scnTitleTxt.text = "SIMULATED CLINICAL SCENARIOS (Click to test):";

            // ── 8. Scenario Buttons (Tall, High-Contrast, Easy to Click) ──
            float pillY = scnTitleY - 26f;
            float pillGap = 42f;

            CreateScenarioPill("Scn1", hudPanel.transform, new Vector2(0f, pillY), "<color=#34d399>●</color>  <b>Scenario 1: Calm Patient</b>  (98% / 68 bpm / 75ms)", pillSprite, defaultFont, () => { LoadScenario(98f, 68f, 75f); RequestPrediction(); });
            CreateScenarioPill("Scn2", hudPanel.transform, new Vector2(0f, pillY - pillGap), "<color=#38bdf8>●</color>  <b>Scenario 2: Mild Restless</b>  (94.5% / 88 bpm / 38ms)", pillSprite, defaultFont, () => { LoadScenario(94.5f, 88f, 38f); RequestPrediction(); });
            CreateScenarioPill("Scn3", hudPanel.transform, new Vector2(0f, pillY - pillGap * 2), "<color=#fbbf24>●</color>  <b>Scenario 3: Sensory Distress</b>  (90% / 112 bpm / 19ms)", pillSprite, defaultFont, () => { LoadScenario(90f, 112f, 19f); RequestPrediction(); });

            // ── 9. Comfort Classification Result Card ──
            float badgeY = pillY - pillGap * 2 - 50f;
            GameObject badgeCard = CreateUIElement("ResultBadgeCard", hudPanel.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, badgeY), new Vector2(-48f, 68f));
            resultBadgeBg = badgeCard.AddComponent<Image>();
            resultBadgeBg.sprite = badgeSprite;
            resultBadgeBg.type = Image.Type.Sliced;
            resultBadgeBg.color = new Color(0.08f, 0.35f, 0.50f, 0.90f);

            GameObject resTxtObj = CreateUIElement("ResText", badgeCard.transform, new Vector2(0f, 0.5f), new Vector2(1f, 1f), new Vector2(0.5f, 0.75f), new Vector2(0f, -6f), new Vector2(-20f, 24f));
            resultBadgeText = resTxtObj.AddComponent<Text>();
            resultBadgeText.font = defaultFont;
            resultBadgeText.fontSize = 14;
            resultBadgeText.fontStyle = FontStyle.Bold;
            resultBadgeText.alignment = TextAnchor.MiddleCenter;
            resultBadgeText.color = Color.white;
            resultBadgeText.horizontalOverflow = HorizontalWrapMode.Overflow;
            resultBadgeText.text = "COMFORT: READY  (Click Predict)";

            GameObject scnTxtObj = CreateUIElement("SceneText", badgeCard.transform, new Vector2(0f, 0f), new Vector2(1f, 0.5f), new Vector2(0.5f, 0.25f), new Vector2(0f, 6f), new Vector2(-20f, 24f));
            resultSceneText = scnTxtObj.AddComponent<Text>();
            resultSceneText.font = defaultFont;
            resultSceneText.fontSize = 12;
            resultSceneText.alignment = TextAnchor.MiddleCenter;
            resultSceneText.color = new Color(0.85f, 0.94f, 1.0f);
            resultSceneText.horizontalOverflow = HorizontalWrapMode.Overflow;
            resultSceneText.text = "Active 360° Scene:  <b>Tranquil Pool</b>";

            // Status message
            float statusY = badgeY - 76f;
            GameObject statusObj = CreateUIElement("StatusMessage", hudPanel.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, statusY), new Vector2(-48f, 24f));
            statusMessageText = statusObj.AddComponent<Text>();
            statusMessageText.font = defaultFont;
            statusMessageText.fontSize = 11;
            statusMessageText.color = new Color(0.70f, 0.80f, 0.92f);
            statusMessageText.alignment = TextAnchor.MiddleCenter;
            statusMessageText.horizontalOverflow = HorizontalWrapMode.Overflow;
            statusMessageText.text = "Ready. Connected to http://127.0.0.1:8000";

            // ── 10. Bottom Action Row ──
            float botY = statusY - 32f;
            CreateSmallActionBtn("HideBtn", hudPanel.transform, new Vector2(-105f, botY), "✕ Hide HUD [H]", pillSprite, defaultFont, () => SetUIVisible(false));
            CreateSmallActionBtn("StopBtn", hudPanel.transform, new Vector2(105f, botY), "◼ Pause [Esc]", pillSprite, defaultFont, OnStopClicked);

            // ── 11. Floating 360 Navigation Hint Bar (Bottom Center) ──
            GameObject navHint = CreateUIElement("NavHintBar", canvas.transform, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 18f), new Vector2(650f, 32f));
            Image navBg = navHint.AddComponent<Image>();
            navBg.sprite = pillSprite;
            navBg.type = Image.Type.Sliced;
            navBg.color = new Color(0.06f, 0.10f, 0.18f, 0.90f);

            GameObject navTxtObj = CreateUIElement("Text", navHint.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            Text navTxt = navTxtObj.AddComponent<Text>();
            navTxt.font = defaultFont;
            navTxt.fontSize = 12;
            navTxt.color = new Color(0.92f, 0.96f, 1.0f);
            navTxt.alignment = TextAnchor.MiddleCenter;
            navTxt.horizontalOverflow = HorizontalWrapMode.Overflow;
            navTxt.text = "<b>360° Panorama:</b> Click & Drag Mouse or Arrow Keys / WASD  |  <b>[H]</b> Hide UI  |  <b>[R]</b> Reset View";
        }

        private Slider CreateVitalSlider(string id, Transform parent, Vector2 pos, string labelText, float min, float max, float cur, Color accentColor, Sprite knobSprite, Font font, out Text labelOut)
        {
            GameObject container = CreateUIElement($"Vital_{id}", parent, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, pos.y), new Vector2(-48f, 54f));

            // Label
            GameObject lblObj = CreateUIElement("Label", container.transform, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(0f, 20f));
            labelOut = lblObj.AddComponent<Text>();
            labelOut.font = font;
            labelOut.fontSize = 13;
            labelOut.fontStyle = FontStyle.Bold;
            labelOut.color = new Color(0.95f, 0.98f, 1.0f);
            labelOut.horizontalOverflow = HorizontalWrapMode.Overflow;
            labelOut.text = labelText;

            // Slider track
            GameObject sliderObj = CreateUIElement("Slider", container.transform, new Vector2(0f, 0f), new Vector2(1f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 6f), new Vector2(0f, 22f));
            Slider slider = sliderObj.AddComponent<Slider>();
            slider.minValue = min;
            slider.maxValue = max;
            slider.value = cur;

            // Background line
            GameObject bgLine = CreateUIElement("Background", sliderObj.transform, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(0f, 10f));
            Image bgImg = bgLine.AddComponent<Image>();
            bgImg.color = new Color(0.12f, 0.18f, 0.28f, 0.95f);

            // Fill Area
            GameObject fillArea = CreateUIElement("FillArea", sliderObj.transform, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), new Vector2(0f, 0.5f), Vector2.zero, new Vector2(-22f, 10f));
            GameObject fill = CreateUIElement("Fill", fillArea.transform, Vector2.zero, Vector2.one, new Vector2(0f, 0.5f), Vector2.zero, Vector2.zero);
            Image fillImg = fill.AddComponent<Image>();
            fillImg.color = accentColor;
            slider.fillRect = fill.GetComponent<RectTransform>();

            // Handle
            GameObject handleArea = CreateUIElement("HandleSlideArea", sliderObj.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(-22f, 0f));
            GameObject handle = CreateUIElement("Handle", handleArea.transform, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(24f, 24f));
            Image handleImg = handle.AddComponent<Image>();
            handleImg.sprite = knobSprite;
            handleImg.color = Color.white;
            slider.handleRect = handle.GetComponent<RectTransform>();
            slider.targetGraphic = handleImg;

            return slider;
        }

        private void CreateScenarioPill(string name, Transform parent, Vector2 pos, string label, Sprite bgSprite, Font font, UnityEngine.Events.UnityAction action)
        {
            GameObject pill = CreateUIElement(name, parent, new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, pos.y), new Vector2(-48f, 36f));
            Button btn = pill.AddComponent<Button>();
            Image img = pill.AddComponent<Image>();
            img.sprite = bgSprite;
            img.type = Image.Type.Sliced;
            img.color = new Color(0.14f, 0.20f, 0.32f, 0.96f);

            GameObject txtObj = CreateUIElement("Label", pill.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(-24f, 0f));
            Text txt = txtObj.AddComponent<Text>();
            txt.font = font;
            txt.fontSize = 12;
            txt.fontStyle = FontStyle.Bold;
            txt.color = Color.white;
            txt.alignment = TextAnchor.MiddleLeft;
            txt.horizontalOverflow = HorizontalWrapMode.Overflow;
            txt.verticalOverflow = VerticalWrapMode.Overflow;
            txt.text = label;

            btn.onClick.AddListener(action);
        }

        private void CreateSmallActionBtn(string name, Transform parent, Vector2 pos, string label, Sprite bgSprite, Font font, UnityEngine.Events.UnityAction action)
        {
            GameObject btnObj = CreateUIElement(name, parent, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), pos, new Vector2(145f, 32f));
            Button btn = btnObj.AddComponent<Button>();
            Image img = btnObj.AddComponent<Image>();
            img.sprite = bgSprite;
            img.type = Image.Type.Sliced;
            img.color = new Color(0.20f, 0.28f, 0.40f, 0.95f);

            GameObject txtObj = CreateUIElement("Label", btnObj.transform, Vector2.zero, Vector2.one, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            Text txt = txtObj.AddComponent<Text>();
            txt.font = font;
            txt.fontSize = 12;
            txt.fontStyle = FontStyle.Bold;
            txt.color = new Color(0.90f, 0.95f, 1.0f);
            txt.alignment = TextAnchor.MiddleCenter;
            txt.horizontalOverflow = HorizontalWrapMode.Overflow;
            txt.text = label;

            btn.onClick.AddListener(action);
        }

        private GameObject CreateUIElement(string name, Transform parent, Vector2 anchorMin, Vector2 anchorMax, Vector2 pivot, Vector2 anchoredPos, Vector2 sizeDelta)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            RectTransform rt = go.AddComponent<RectTransform>();
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.pivot = pivot;
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = sizeDelta;
            return go;
        }
        #endregion
    }
}
