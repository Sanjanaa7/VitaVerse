using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// Generates high-definition, photorealistic 360° equirectangular panoramas
    /// with mathematically seamless 360-degree continuity (using periodic sin/cos coordinates).
    /// Creates realistic horizons with layered mountain silhouettes, Rayleigh atmospheric scattering,
    /// solar corona glow, and cloud strata.
    /// Supports both Unity's native Skybox/Panoramic and inverted 360° photosphere domes.
    /// </summary>
    public static class PanoramicSkyGenerator
    {
        private static Texture2D _cachedGardenPano;
        private static Texture2D _cachedBeachPano;
        private static Texture2D _cachedHomePano;
        private static Texture2D _cachedForestPano;
        private static Texture2D _cachedSunsetPano;

        /// <summary>
        /// Creates a 360° panoramic skydome GameObject enveloping the scene,
        /// and optionally sets RenderSettings.skybox if Skybox/Panoramic is available.
        /// </summary>
        public static GameObject CreatePhotosphereDome(string name, Transform parent, Texture2D panoramaTexture, float radius = 320f)
        {
            GameObject dome = new GameObject(name);
            dome.transform.SetParent(parent);
            dome.transform.position = Vector3.zero;

            MeshFilter mf = dome.AddComponent<MeshFilter>();
            MeshRenderer mr = dome.AddComponent<MeshRenderer>();

            // Generate high-fidelity inverted sphere mesh with inward-facing normals
            mf.sharedMesh = CreateInvertedSphereMesh(radius, 48, 32);

            // Select shader
            Shader shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (shader == null) shader = Shader.Find("Unlit/Texture");
            if (shader == null) shader = Shader.Find("Mobile/Unlit (Supports Lightmap)");
            if (shader == null) shader = Shader.Find("Diffuse");

            Material mat = new Material(shader) { name = $"{name}_Mat" };
            mat.mainTexture = panoramaTexture;
            mr.sharedMaterial = mat;

            // Also attempt to configure native Unity Panoramic Skybox
            Shader skyboxShader = Shader.Find("Skybox/Panoramic");
            if (skyboxShader != null)
            {
                Material skyMat = new Material(skyboxShader);
                skyMat.mainTexture = panoramaTexture;
                if (skyMat.HasProperty("_Exposure")) skyMat.SetFloat("_Exposure", 1.05f);
                if (skyMat.HasProperty("_ImageType")) skyMat.SetFloat("_ImageType", 0f); // 360 degrees
                RenderSettings.skybox = skyMat;
            }

            return dome;
        }

        #region Garden 360° Photorealistic Panorama
        /// <summary>
        /// Generates a realistic 360° equirectangular panorama for the Botanical Garden:
        /// Warm morning sunlight, azure zenith, distant layered emerald mountain ranges,
        /// cherry blossom horizon hints, and soft cumulus clouds.
        /// 100% seamless horizontally across all 360 degrees.
        /// </summary>
        public static Texture2D GenerateGardenPanorama(int width = 1536, int height = 768)
        {
            if (_cachedGardenPano != null) return _cachedGardenPano;

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.wrapMode = TextureWrapMode.Repeat;
            tex.filterMode = FilterMode.Bilinear;

            Color zenithBlue = new Color(0.18f, 0.44f, 0.82f); // Deep morning zenith
            Color midSkyAzure = new Color(0.52f, 0.72f, 0.92f); // Mid-sky azure
            Color horizonMist = new Color(0.86f, 0.92f, 0.97f); // Soft horizon mist
            Color sunHazeGold = new Color(1.0f, 0.92f, 0.74f); // Morning sunlight corona
            Color sunCore = new Color(1.0f, 1.0f, 0.98f); // Bright sun core

            Color mountainSnow = new Color(0.85f, 0.90f, 0.96f); // Distant snow caps
            Color mountainFar = new Color(0.38f, 0.52f, 0.58f); // Distant blue-tinted peaks
            Color mountainMid = new Color(0.24f, 0.40f, 0.30f); // Forested ridge
            Color valleyFoothills = new Color(0.18f, 0.32f, 0.18f); // Close foothills
            Color meadowFloor = new Color(0.16f, 0.30f, 0.15f);

            // Sun position (East-Southeast, slightly above horizon)
            Vector2 sunDir = new Vector2(0.32f, 0.58f);

            Color[] pixels = new Color[width * height];

            for (int y = 0; y < height; y++)
            {
                float v = (float)y / (height - 1); // 0 (Nadir) to 1 (Zenith)
                for (int x = 0; x < width; x++)
                {
                    float u = (float)x / (width - 1); // 0 to 1 (360 degrees)

                    // Seamless periodic coordinates for noise
                    float rad = u * Mathf.PI * 2f;
                    float cosU = Mathf.Cos(rad);
                    float sinU = Mathf.Sin(rad);

                    Color col;

                    if (v >= 0.47f)
                    {
                        // Sky Hemisphere with Rayleigh scattering gradient
                        float skyT = (v - 0.47f) / 0.53f;
                        if (skyT < 0.45f)
                        {
                            col = Color.Lerp(horizonMist, midSkyAzure, skyT / 0.45f);
                        }
                        else
                        {
                            col = Color.Lerp(midSkyAzure, zenithBlue, (skyT - 0.45f) / 0.55f);
                        }

                        // Seamless Cumulus clouds using 2D cylinder projection
                        float cloudNoise1 = Mathf.PerlinNoise(cosU * 1.8f + 2f, sinU * 1.8f + 2f) * 0.6f;
                        float cloudNoise2 = Mathf.PerlinNoise(cosU * 4.5f + v * 3f, sinU * 4.5f + v * 3f) * 0.4f;
                        float clouds = cloudNoise1 + cloudNoise2;

                        if (clouds > 0.48f && v < 0.88f)
                        {
                            float cloudAlpha = Mathf.SmoothStep(0.48f, 0.72f, clouds) * (1f - skyT * 0.4f) * 0.75f;
                            col = Color.Lerp(col, Color.white, cloudAlpha);
                        }

                        // Sun Disk & Golden Corona Bloom
                        float dx = Mathf.Min(Mathf.Abs(u - sunDir.x), 1f - Mathf.Abs(u - sunDir.x));
                        float dy = v - sunDir.y;
                        float distToSun = Mathf.Sqrt(dx * dx * 4f + dy * dy);

                        if (distToSun < 0.35f)
                        {
                            float bloom = 1f - (distToSun / 0.35f);
                            bloom = Mathf.Pow(bloom, 2.2f);
                            col = Color.Lerp(col, sunHazeGold, bloom * 0.90f);

                            if (distToSun < 0.045f)
                            {
                                float coreGlow = 1f - (distToSun / 0.045f);
                                col = Color.Lerp(col, sunCore, coreGlow);
                            }
                        }
                    }
                    else
                    {
                        // Seamless 360 Mountain Ridges using trigonometric harmonics
                        float mtn1 = 0.47f + sinU * 0.035f + Mathf.Cos(rad * 3f) * 0.02f + Mathf.Sin(rad * 7f) * 0.01f;
                        float mtn2 = 0.43f + Mathf.Cos(rad * 2f + 1f) * 0.04f + Mathf.Sin(rad * 5f) * 0.015f;
                        float mtn3 = 0.39f + Mathf.Sin(rad * 4f) * 0.03f + Mathf.Cos(rad * 9f) * 0.012f;

                        if (v > mtn1)
                        {
                            // Distant peak / snow cap
                            col = (v > mtn1 - 0.015f && mtn1 > 0.48f) ? mountainSnow : mountainFar;
                        }
                        else if (v > mtn2)
                        {
                            col = mountainMid;
                        }
                        else if (v > mtn3)
                        {
                            col = valleyFoothills;
                        }
                        else
                        {
                            col = meadowFloor;
                        }

                        // Atmospheric Aerial Perspective Fog
                        float fogT = Mathf.Clamp01((v - 0.36f) / 0.12f);
                        col = Color.Lerp(col, horizonMist, (1f - fogT) * 0.38f);
                    }

                    pixels[y * width + x] = col;
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            _cachedGardenPano = tex;
            return tex;
        }
        #endregion

        #region Forest 360° Photorealistic Panorama
        /// <summary>
        /// Generates a realistic 360° equirectangular panorama for the Quiet Forest:
        /// Towering alpine snow peaks, layers of dense conifer ridges wrapping 360 degrees,
        /// diffused cool canopy sky with cirrus cloud veils.
        /// </summary>
        public static Texture2D GenerateForestPanorama(int width = 1536, int height = 768)
        {
            if (_cachedForestPano != null) return _cachedForestPano;

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.wrapMode = TextureWrapMode.Repeat;
            tex.filterMode = FilterMode.Bilinear;

            Color zenithSlate = new Color(0.20f, 0.35f, 0.42f); // Alpine slate blue
            Color midSkyMist = new Color(0.55f, 0.68f, 0.72f); // Diffused cool canopy
            Color horizonHaze = new Color(0.78f, 0.85f, 0.86f); // Soft mountain mist

            Color snowPeaks = new Color(0.90f, 0.94f, 0.96f);
            Color alpineRockFar = new Color(0.28f, 0.36f, 0.42f);
            Color darkPineRidgeMid = new Color(0.12f, 0.24f, 0.16f);
            Color foregroundCanopy = new Color(0.08f, 0.18f, 0.10f);
            Color forestLoam = new Color(0.06f, 0.12f, 0.08f);

            Color[] pixels = new Color[width * height];

            for (int y = 0; y < height; y++)
            {
                float v = (float)y / (height - 1);
                for (int x = 0; x < width; x++)
                {
                    float u = (float)x / (width - 1);
                    float rad = u * Mathf.PI * 2f;
                    float cosU = Mathf.Cos(rad);
                    float sinU = Mathf.Sin(rad);

                    Color col;

                    if (v >= 0.46f)
                    {
                        float skyT = (v - 0.46f) / 0.54f;
                        col = Color.Lerp(horizonHaze, zenithSlate, Mathf.Pow(skyT, 0.85f));

                        // Wispy alpine cirrus streaks
                        float cirrus = Mathf.PerlinNoise(cosU * 3f + 1f, sinU * 3f + v * 2f);
                        if (cirrus > 0.55f)
                        {
                            float alpha = (cirrus - 0.55f) * 1.8f * (1f - skyT * 0.4f);
                            col = Color.Lerp(col, new Color(0.92f, 0.95f, 0.98f), alpha * 0.4f);
                        }
                    }
                    else
                    {
                        // 360 Alpine Peaks & Pine Ridges
                        float alpine1 = 0.48f + Mathf.Abs(sinU) * 0.06f + Mathf.Cos(rad * 4f) * 0.035f + Mathf.Sin(rad * 8f) * 0.015f;
                        float pine2 = 0.44f + Mathf.Cos(rad * 3f + 0.8f) * 0.04f + Mathf.Sin(rad * 9f) * 0.02f;
                        float pine3 = 0.40f + Mathf.Sin(rad * 5f) * 0.03f + Mathf.Cos(rad * 12f) * 0.015f;

                        if (v > pine2)
                        {
                            // Snow on high alpine summits
                            col = (v > alpine1 - 0.02f && alpine1 > 0.49f) ? snowPeaks : alpineRockFar;
                        }
                        else if (v > pine3)
                        {
                            col = darkPineRidgeMid;
                        }
                        else if (v > 0.34f)
                        {
                            col = foregroundCanopy;
                        }
                        else
                        {
                            col = forestLoam;
                        }

                        // Atmospheric mountain fog
                        float fogT = Mathf.Clamp01((v - 0.34f) / 0.12f);
                        col = Color.Lerp(col, horizonHaze, (1f - fogT) * 0.45f);
                    }

                    pixels[y * width + x] = col;
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            _cachedForestPano = tex;
            return tex;
        }
        #endregion

        #region Sunset 360° Photorealistic Panorama
        /// <summary>
        /// Generates a realistic 360° equirectangular panorama for the Low-Stimulation Sunset:
        /// Glowing twilight sky (violet zenith to flaming amber-gold at horizon), setting sun disk,
        /// purple mountain silhouettes across 360 degrees, and golden water mirror reflection.
        /// </summary>
        public static Texture2D GenerateSunsetPanorama(int width = 1536, int height = 768)
        {
            if (_cachedSunsetPano != null) return _cachedSunsetPano;

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.wrapMode = TextureWrapMode.Repeat;
            tex.filterMode = FilterMode.Bilinear;

            Color zenithIndigo = new Color(0.12f, 0.08f, 0.26f); // Deep evening violet
            Color midSkyDusk = new Color(0.48f, 0.18f, 0.38f); // Rich dusk magenta
            Color sunsetAmber = new Color(0.96f, 0.52f, 0.20f); // Radiant golden amber
            Color horizonGlow = new Color(1.0f, 0.78f, 0.42f); // Horizon warmth
            Color sunDisk = new Color(1.0f, 0.95f, 0.85f); // Glowing sunset sphere

            Color mountainFar = new Color(0.24f, 0.14f, 0.32f); // Purple silhouette
            Color mountainNear = new Color(0.16f, 0.09f, 0.22f); // Deep violet ridge
            Color fjordWater = new Color(0.14f, 0.10f, 0.22f); // Calm reflecting water
            Color waterReflection = new Color(0.85f, 0.45f, 0.25f); // Sun path shimmer

            Vector2 sunPos = new Vector2(0.50f, 0.48f); // Center front horizon

            Color[] pixels = new Color[width * height];

            for (int y = 0; y < height; y++)
            {
                float v = (float)y / (height - 1);
                for (int x = 0; x < width; x++)
                {
                    float u = (float)x / (width - 1);
                    float rad = u * Mathf.PI * 2f;
                    float cosU = Mathf.Cos(rad);
                    float sinU = Mathf.Sin(rad);

                    Color col;

                    if (v >= 0.46f)
                    {
                        float skyT = (v - 0.46f) / 0.54f;
                        if (skyT < 0.32f)
                        {
                            col = Color.Lerp(horizonGlow, sunsetAmber, skyT / 0.32f);
                        }
                        else if (skyT < 0.65f)
                        {
                            col = Color.Lerp(sunsetAmber, midSkyDusk, (skyT - 0.32f) / 0.33f);
                        }
                        else
                        {
                            col = Color.Lerp(midSkyDusk, zenithIndigo, (skyT - 0.65f) / 0.35f);
                        }

                        // Evening twilight clouds with golden undersides
                        float cloudNoise = Mathf.PerlinNoise(cosU * 2.5f + 3f, sinU * 2.5f + v * 3.5f);
                        if (cloudNoise > 0.46f && v < 0.82f)
                        {
                            float alpha = Mathf.SmoothStep(0.46f, 0.70f, cloudNoise) * 0.7f;
                            Color cloudCol = Color.Lerp(sunsetAmber, midSkyDusk, skyT);
                            col = Color.Lerp(col, cloudCol, alpha);
                        }

                        // Sun Disk and Corona Bloom
                        float dx = Mathf.Min(Mathf.Abs(u - sunPos.x), 1f - Mathf.Abs(u - sunPos.x));
                        float dy = v - sunPos.y;
                        float distToSun = Mathf.Sqrt(dx * dx * 3.8f + dy * dy);

                        if (distToSun < 0.38f)
                        {
                            float bloom = 1f - (distToSun / 0.38f);
                            bloom = Mathf.Pow(bloom, 2.5f);
                            col = Color.Lerp(col, horizonGlow, bloom * 0.95f);

                            if (distToSun < 0.045f)
                            {
                                float core = 1f - (distToSun / 0.045f);
                                col = Color.Lerp(col, sunDisk, core);
                            }
                        }
                    }
                    else
                    {
                        // 360 Fjord Mountain Profiles
                        float mtn1 = 0.46f + Mathf.Sin(rad * 2f) * 0.045f + Mathf.Cos(rad * 5f) * 0.02f;
                        float mtn2 = 0.42f + Mathf.Cos(rad * 3f + 1.2f) * 0.035f;

                        if (v > mtn1)
                        {
                            col = mountainFar;
                        }
                        else if (v > mtn2)
                        {
                            col = mountainNear;
                        }
                        else
                        {
                            col = fjordWater;

                            // Sun reflection column on water
                            float dxSun = Mathf.Abs(u - sunPos.x);
                            if (dxSun < 0.12f)
                            {
                                float shimmer = 1f - (dxSun / 0.12f);
                                float wave = Mathf.PerlinNoise(u * 80f, v * 120f);
                                col = Color.Lerp(col, waterReflection, shimmer * wave * 0.65f);
                            }
                        }

                        // Horizon dusk haze
                        float fogT = Mathf.Clamp01((v - 0.34f) / 0.12f);
                        col = Color.Lerp(col, sunsetAmber, (1f - fogT) * 0.35f);
                    }

                    pixels[y * width + x] = col;
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            _cachedSunsetPano = tex;
            return tex;
        }
        #endregion

        #region Beach 360° Fallback Panorama
        /// <summary>
        /// Procedural fallback: Serene tropical beach — turquoise ocean, white sand, clear sky.
        /// Used when no AI beach_360 image is assigned.
        /// </summary>
        public static Texture2D GenerateBeachPanorama(int width = 1536, int height = 768)
        {
            if (_cachedBeachPano != null) return _cachedBeachPano;

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.wrapMode = TextureWrapMode.Repeat;
            tex.filterMode = FilterMode.Bilinear;

            Color zenithBlue  = new Color(0.30f, 0.62f, 0.90f);
            Color midSkyLight = new Color(0.60f, 0.82f, 0.96f);
            Color horizonHaze = new Color(0.88f, 0.94f, 0.98f);
            Color oceanDeep   = new Color(0.08f, 0.40f, 0.55f);
            Color oceanShallow= new Color(0.20f, 0.65f, 0.70f);
            Color sandColor   = new Color(0.90f, 0.84f, 0.68f);

            Color[] pixels = new Color[width * height];

            for (int y = 0; y < height; y++)
            {
                float v = (float)y / (height - 1);
                for (int x = 0; x < width; x++)
                {
                    float u = (float)x / (width - 1);
                    float rad = u * Mathf.PI * 2f;
                    Color col;

                    if (v < 0.50f)
                    {
                        // Sky
                        float skyT = (0.50f - v) / 0.50f;
                        col = Color.Lerp(horizonHaze, Color.Lerp(midSkyLight, zenithBlue, skyT), skyT);

                        // Sun (high noon, front)
                        float dx = Mathf.Min(Mathf.Abs(u - 0.5f), 1f - Mathf.Abs(u - 0.5f));
                        float dy = v - 0.15f;
                        float dist = Mathf.Sqrt(dx * dx * 4f + dy * dy);
                        if (dist < 0.25f)
                        {
                            float bloom = Mathf.Pow(1f - dist / 0.25f, 2.5f);
                            col = Color.Lerp(col, Color.white, bloom * 0.95f);
                        }
                    }
                    else if (v < 0.62f)
                    {
                        // Ocean
                        float ot = (v - 0.50f) / 0.12f;
                        col = Color.Lerp(oceanShallow, oceanDeep, ot);
                        // Specular glints
                        float glint = Mathf.PerlinNoise(u * 60f, v * 40f);
                        if (glint > 0.72f) col = Color.Lerp(col, Color.white, (glint - 0.72f) * 2f);
                    }
                    else
                    {
                        // Sandy shore ground
                        col = sandColor;
                    }

                    pixels[y * width + x] = col;
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            _cachedBeachPano = tex;
            return tex;
        }
        #endregion

        #region Heritage Home 360° Fallback Panorama
        /// <summary>
        /// Procedural fallback: Warm indoor Kerala heritage home ambience.
        /// Used when no AI home_360 image is assigned.
        /// </summary>
        public static Texture2D GenerateHomePanorama(int width = 1536, int height = 768)
        {
            if (_cachedHomePano != null) return _cachedHomePano;

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            tex.wrapMode = TextureWrapMode.Repeat;
            tex.filterMode = FilterMode.Bilinear;

            Color ceilingWood   = new Color(0.28f, 0.16f, 0.08f);
            Color upperWall     = new Color(0.88f, 0.82f, 0.74f);
            Color lowerWall     = new Color(0.72f, 0.62f, 0.50f);
            Color pillarTeak    = new Color(0.35f, 0.18f, 0.09f);
            Color redOxideFloor = new Color(0.62f, 0.18f, 0.12f);
            Color courtLight    = new Color(1.0f, 0.92f, 0.78f);

            Color[] pixels = new Color[width * height];

            for (int y = 0; y < height; y++)
            {
                float v = (float)y / (height - 1);
                for (int x = 0; x < width; x++)
                {
                    float u = (float)x / (width - 1);
                    float rad = u * Mathf.PI * 2f;
                    Color col;

                    if (v < 0.22f)
                    {
                        // Wooden carved ceiling
                        float grainN = Mathf.PerlinNoise(u * 30f, v * 8f);
                        col = Color.Lerp(ceilingWood, new Color(0.38f, 0.22f, 0.12f), grainN);
                        // Courtyard skylight centre glow
                        float cx = Mathf.Abs(u - 0.5f);
                        if (cx < 0.12f && v < 0.18f)
                        {
                            col = Color.Lerp(col, courtLight, (0.12f - cx) / 0.12f * 0.9f);
                        }
                    }
                    else if (v < 0.55f)
                    {
                        // Walls + pillars
                        float wallN = Mathf.PerlinNoise(u * 6f, v * 4f);
                        col = Color.Lerp(upperWall, lowerWall, (v - 0.22f) / 0.33f);
                        // Vertical pillar bands every ~1/6 of circumference
                        float pillarPhase = Mathf.Abs(Mathf.Sin(rad * 3f));
                        if (pillarPhase > 0.88f)
                        {
                            col = Color.Lerp(col, pillarTeak, (pillarPhase - 0.88f) / 0.12f);
                        }
                    }
                    else
                    {
                        // Red oxide tiled floor
                        float tileN = Mathf.PerlinNoise(u * 20f, v * 20f) * 0.15f;
                        col = Color.Lerp(redOxideFloor, new Color(0.70f, 0.24f, 0.18f), tileN);
                    }

                    // Warm ambient fill
                    col = Color.Lerp(col, courtLight, 0.08f);
                    pixels[y * width + x] = col;
                }
            }

            tex.SetPixels(pixels);
            tex.Apply();
            _cachedHomePano = tex;
            return tex;
        }
        #endregion

        /// <summary>
        /// Generates an inverted sphere mesh with normals pointing inward so it is visible from the inside.
        /// </summary>
        private static Mesh CreateInvertedSphereMesh(float radius, int longitudeSegments, int latitudeSegments)
        {
            Mesh mesh = new Mesh { name = "PhotosphereDomeMesh" };

            int vertCount = (longitudeSegments + 1) * (latitudeSegments + 1);
            Vector3[] vertices = new Vector3[vertCount];
            Vector3[] normals = new Vector3[vertCount];
            Vector2[] uvs = new Vector2[vertCount];
            int[] triangles = new int[longitudeSegments * latitudeSegments * 6];

            int idx = 0;
            for (int lat = 0; lat <= latitudeSegments; lat++)
            {
                float theta = (float)lat / latitudeSegments * Mathf.PI;
                float sinTheta = Mathf.Sin(theta);
                float cosTheta = Mathf.Cos(theta);

                for (int lon = 0; lon <= longitudeSegments; lon++)
                {
                    float phi = (float)lon / longitudeSegments * 2f * Mathf.PI;
                    float sinPhi = Mathf.Sin(phi);
                    float cosPhi = Mathf.Cos(phi);

                    Vector3 normal = new Vector3(sinTheta * sinPhi, cosTheta, sinTheta * cosPhi);
                    vertices[idx] = normal * radius;
                    normals[idx] = -normal; // Pointing inward
                    uvs[idx] = new Vector2((float)lon / longitudeSegments, 1f - (float)lat / latitudeSegments);
                    idx++;
                }
            }

            int triIdx = 0;
            for (int lat = 0; lat < latitudeSegments; lat++)
            {
                for (int lon = 0; lon < longitudeSegments; lon++)
                {
                    int current = lat * (longitudeSegments + 1) + lon;
                    int next = current + longitudeSegments + 1;

                    // Clockwise winding when looking from inside
                    triangles[triIdx++] = current;
                    triangles[triIdx++] = next;
                    triangles[triIdx++] = current + 1;

                    triangles[triIdx++] = current + 1;
                    triangles[triIdx++] = next;
                    triangles[triIdx++] = next + 1;
                }
            }

            mesh.vertices = vertices;
            mesh.normals = normals;
            mesh.uv = uvs;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();

            return mesh;
        }
    }
}
