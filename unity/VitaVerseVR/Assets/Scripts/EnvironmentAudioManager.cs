using System.Collections.Generic;
using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// VitaVerse Ambient Environment Audio Manager.
    /// Manages looped 2D ambient soundscapes for therapeutic VR environments.
    /// Custom clinician uploads remain silent as per clinical protocol.
    /// </summary>
    public class EnvironmentAudioManager : MonoBehaviour
    {
        [Header("Audio Settings")]
        public AudioSource audioSource;
        [Range(0f, 1f)]
        public float ambientVolume = 0.7f;

        private readonly Dictionary<string, AudioClip> clipMap = new Dictionary<string, AudioClip>();
        private bool isMemoryAudioActive = false;
        private AudioClip memoryAudioClip = null;
        private string currentEnvKey = "Pool";

        private void Awake()
        {
            if (audioSource == null)
            {
                audioSource = GetComponent<AudioSource>();
                if (audioSource == null)
                {
                    audioSource = gameObject.AddComponent<AudioSource>();
                }
            }

            audioSource.loop = true;
            audioSource.playOnAwake = false;
            audioSource.spatialBlend = 0f; // 2D stereo ambient
            audioSource.volume = ambientVolume;

            // Load clips from Resources/Audio/EnvironmentSounds
            LoadClip("Pool", "Audio/EnvironmentSounds/PoolWater");
            LoadClip("Home", "Audio/EnvironmentSounds/BirdsChirping");
            LoadClip("Beach", "Audio/EnvironmentSounds/BeachSound");
            LoadClip("BlueLagoon", "Audio/EnvironmentSounds/BeachSound");
            LoadClip("NightSky", "Audio/EnvironmentSounds/SkySound");
            LoadClip("SunsetFire", "Audio/EnvironmentSounds/SkySound");
            LoadClip("MistyPines", "Audio/EnvironmentSounds/WinterForest");
        }

        private void LoadClip(string key, string path)
        {
            AudioClip clip = Resources.Load<AudioClip>(path);
            if (clip != null)
            {
                clipMap[key] = clip;
            }
        }

        public void PlaySound(string envKey)
        {
            if (!string.IsNullOrEmpty(envKey)) currentEnvKey = envKey;
            if (audioSource == null) return;

            // If Memory Audio Therapy is active, it plays across all scenarios and environments
            if (isMemoryAudioActive && memoryAudioClip != null)
            {
                if (audioSource.clip != memoryAudioClip || !audioSource.isPlaying)
                {
                    audioSource.clip = memoryAudioClip;
                    audioSource.volume = ambientVolume;
                    audioSource.Play();
                }
                return;
            }

            if (string.IsNullOrEmpty(envKey) || envKey.StartsWith("custom_"))
            {
                audioSource.Stop();
                return;
            }

            if (clipMap.TryGetValue(envKey, out AudioClip clip) && clip != null)
            {
                if (audioSource.clip != clip || !audioSource.isPlaying)
                {
                    audioSource.clip = clip;
                    audioSource.volume = ambientVolume;
                    audioSource.Play();
                }
            }
            else
            {
                audioSource.Stop();
            }
        }

        public void SetMemoryAudio(AudioClip clip, bool active)
        {
            memoryAudioClip = clip;
            isMemoryAudioActive = active;

            if (active && clip != null)
            {
                if (audioSource != null)
                {
                    audioSource.clip = clip;
                    audioSource.volume = ambientVolume;
                    if (!audioSource.isPlaying) audioSource.Play();
                }
            }
            else if (!active)
            {
                PlaySound(currentEnvKey);
            }
        }

        public void DisableMemoryAudio(string fallbackEnvKey = null)
        {
            isMemoryAudioActive = false;
            memoryAudioClip = null;
            PlaySound(fallbackEnvKey ?? currentEnvKey);
        }

        public void StopSound()
        {
            if (audioSource != null && audioSource.isPlaying)
            {
                audioSource.Stop();
            }
        }
    }
}

