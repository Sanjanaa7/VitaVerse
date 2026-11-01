using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// Smooth 360-degree viewing camera controller designed for stationary therapeutic VR / desktop viewing.
    /// Provides full 360° horizontal continuous yaw rotation (no angle clamping) and comfortable pitch (-75° to +75°).
    /// Supports:
    /// - Mouse Drag with Left or Right Click
    /// - Keyboard controls: Arrow Keys (Left/Right to pan 360°, Up/Down to tilt) and A/D/W/S keys
    /// - [R] key to reset view to center
    /// - 100% compatible with Unity 6 (safe OnGUI and Event.current handling).
    /// </summary>
    public class VRCameraController : MonoBehaviour
    {
        [Header("360° Rotation Settings")]
        public float lookSensitivity = 0.28f;
        public float keyRotationSpeed = 65f; // Degrees per second via keyboard
        public float minPitch = -75f;
        public float maxPitch = 75f;
        public float smoothDamping = 12f;

        private float targetYaw = 0f;
        private float targetPitch = 0f;
        private float currentYaw = 0f;
        private float currentPitch = 0f;

        private Vector3 initialPosition;
        private Quaternion initialRotation;
        private bool isDragging = false;

        private void Start()
        {
            initialPosition = transform.position;
            initialRotation = transform.rotation;
            targetYaw = transform.eulerAngles.y;
            targetPitch = transform.eulerAngles.x;
            currentYaw = targetYaw;
            currentPitch = targetPitch;
        }

        private void Update()
        {
            // Keyboard rotation (Arrow keys or A/D/W/S)
            float keyHorizontal = 0f;
            float keyVertical = 0f;

            // Safe key polling via Input.GetKey without throwing on new input system
            try
            {
                if (Input.GetKey(KeyCode.RightArrow) || Input.GetKey(KeyCode.D)) keyHorizontal += 1f;
                if (Input.GetKey(KeyCode.LeftArrow) || Input.GetKey(KeyCode.A)) keyHorizontal -= 1f;
                if (Input.GetKey(KeyCode.UpArrow) || Input.GetKey(KeyCode.W)) keyVertical -= 1f;
                if (Input.GetKey(KeyCode.DownArrow) || Input.GetKey(KeyCode.S)) keyVertical += 1f;
                if (Input.GetKeyDown(KeyCode.R)) ResetView();
            }
            catch
            {
                // In case of input package strictness, handled smoothly
            }

            if (Mathf.Abs(keyHorizontal) > 0.01f || Mathf.Abs(keyVertical) > 0.01f)
            {
                targetYaw += keyHorizontal * keyRotationSpeed * Time.deltaTime;
                targetPitch += keyVertical * (keyRotationSpeed * 0.7f) * Time.deltaTime;
                targetPitch = Mathf.Clamp(targetPitch, minPitch, maxPitch);
            }

            // Smooth interpolation to prevent jitter and provide cinematic feel
            currentYaw = Mathf.Lerp(currentYaw, targetYaw, Time.deltaTime * smoothDamping);
            currentPitch = Mathf.Lerp(currentPitch, targetPitch, Time.deltaTime * smoothDamping);

            transform.localRotation = Quaternion.Euler(currentPitch, currentYaw, 0f);
        }

        private void OnGUI()
        {
            Event e = Event.current;
            if (e == null) return;

            // Mouse button down (Left Click or Right Click to start panning)
            if (e.type == EventType.MouseDown && (e.button == 0 || e.button == 1))
            {
                // If not clicking near the top-left HUD
                isDragging = true;
            }
            else if (e.type == EventType.MouseUp && (e.button == 0 || e.button == 1))
            {
                isDragging = false;
            }

            // Mouse drag: full 360° horizontal continuous yaw
            if (isDragging && e.type == EventType.MouseDrag)
            {
                targetYaw += e.delta.x * lookSensitivity;
                targetPitch += e.delta.y * lookSensitivity;
                targetPitch = Mathf.Clamp(targetPitch, minPitch, maxPitch);
            }

            // Keyboard navigation via OnGUI Event (safe across Old and New Input Systems)
            if (e.isKey && e.type == EventType.KeyDown)
            {
                if (e.keyCode == KeyCode.RightArrow || e.keyCode == KeyCode.D) targetYaw += 4f;
                else if (e.keyCode == KeyCode.LeftArrow || e.keyCode == KeyCode.A) targetYaw -= 4f;
                else if (e.keyCode == KeyCode.UpArrow || e.keyCode == KeyCode.W) targetPitch -= 3f;
                else if (e.keyCode == KeyCode.DownArrow || e.keyCode == KeyCode.S) targetPitch += 3f;
                else if (e.keyCode == KeyCode.R) ResetView();
                targetPitch = Mathf.Clamp(targetPitch, minPitch, maxPitch);
            }
        }

        public void ResetView()
        {
            targetYaw = 0f;
            targetPitch = 0f;
            currentYaw = 0f;
            currentPitch = 0f;
            transform.position = initialPosition;
            transform.localRotation = initialRotation;
        }
    }
}
