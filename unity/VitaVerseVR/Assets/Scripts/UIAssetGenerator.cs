using UnityEngine;

namespace VitaVerse
{
    /// <summary>
    /// Generates sleek, modern UI textures (rounded corners, glow borders, soft gradients)
    /// entirely in memory at runtime. Enables a professional glassmorphic healthcare UI
    /// without requiring any paid or downloaded asset store packages.
    /// </summary>
    public static class UIAssetGenerator
    {
        public static Sprite CreateRoundedRectSprite(int width = 64, int height = 64, int cornerRadius = 14, Color fillColor = default)
        {
            if (fillColor == default) fillColor = Color.white;
            Texture2D tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            tex.filterMode = FilterMode.Bilinear;

            Color transparent = new Color(0, 0, 0, 0);

            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    // Check corners
                    int cx = (x < cornerRadius) ? cornerRadius : (x >= width - cornerRadius) ? width - cornerRadius - 1 : x;
                    int cy = (y < cornerRadius) ? cornerRadius : (y >= height - cornerRadius) ? height - cornerRadius - 1 : y;

                    float dist = Vector2.Distance(new Vector2(x, y), new Vector2(cx, cy));
                    if (dist > cornerRadius)
                    {
                        tex.SetPixel(x, y, transparent);
                    }
                    else if (dist > cornerRadius - 1.5f)
                    {
                        // Anti-aliasing edge
                        float alpha = Mathf.Clamp01(cornerRadius - dist);
                        Color c = fillColor;
                        c.a *= alpha;
                        tex.SetPixel(x, y, c);
                    }
                    else
                    {
                        tex.SetPixel(x, y, fillColor);
                    }
                }
            }
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, width, height), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(cornerRadius, cornerRadius, cornerRadius, cornerRadius));
        }

        public static Sprite CreateGlowBorderSprite(int width = 64, int height = 64, int cornerRadius = 14, int borderWidth = 2, Color borderColor = default, Color fillColor = default)
        {
            if (borderColor == default) borderColor = new Color(0.22f, 0.55f, 0.85f, 0.9f);
            if (fillColor == default) fillColor = new Color(0.06f, 0.09f, 0.14f, 0.88f);

            Texture2D tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            tex.filterMode = FilterMode.Bilinear;

            Color transparent = new Color(0, 0, 0, 0);

            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    int cx = (x < cornerRadius) ? cornerRadius : (x >= width - cornerRadius) ? width - cornerRadius - 1 : x;
                    int cy = (y < cornerRadius) ? cornerRadius : (y >= height - cornerRadius) ? height - cornerRadius - 1 : y;

                    float dist = Vector2.Distance(new Vector2(x, y), new Vector2(cx, cy));

                    if (dist > cornerRadius)
                    {
                        tex.SetPixel(x, y, transparent);
                    }
                    else if (dist >= cornerRadius - borderWidth)
                    {
                        tex.SetPixel(x, y, borderColor);
                    }
                    else
                    {
                        tex.SetPixel(x, y, fillColor);
                    }
                }
            }
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, width, height), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(cornerRadius, cornerRadius, cornerRadius, cornerRadius));
        }

        public static Sprite CreateCircleSprite(int diameter = 32, Color fillColor = default)
        {
            if (fillColor == default) fillColor = Color.white;
            Texture2D tex = new Texture2D(diameter, diameter, TextureFormat.RGBA32, false);
            tex.filterMode = FilterMode.Bilinear;

            float radius = (diameter - 1) * 0.5f;
            Vector2 center = new Vector2(radius, radius);
            Color transparent = new Color(0, 0, 0, 0);

            for (int y = 0; y < diameter; y++)
            {
                for (int x = 0; x < diameter; x++)
                {
                    float dist = Vector2.Distance(new Vector2(x, y), center);
                    if (dist > radius)
                    {
                        tex.SetPixel(x, y, transparent);
                    }
                    else if (dist > radius - 1.2f)
                    {
                        float alpha = Mathf.Clamp01(radius - dist);
                        Color c = fillColor;
                        c.a *= alpha;
                        tex.SetPixel(x, y, c);
                    }
                    else
                    {
                        tex.SetPixel(x, y, fillColor);
                    }
                }
            }
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, diameter, diameter), new Vector2(0.5f, 0.5f), 100f);
        }
    }
}
