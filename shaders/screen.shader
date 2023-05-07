shader_type screen;

uniform float brightness = 1.0f;

vec3 drawVignette(vec3 color, vec2 uv)  {
    float vignette = uv.x * uv.y * ( 1.0 - uv.x ) * ( 1.0 - uv.y );
    vignette = clamp( pow( 16.0 * vignette, 0.3 ), 0.0, 1.0 );
    color *= vignette;
    return color;
}

vec3 drawScanlines(vec3 color, vec2 uv)  {
    vec2 windowSizeHalved = textureSize(TEXTURE, 0) / 2.0f;
    float scanline = clamp(0.95f + 0.05f * cos(3.14f * (uv.y + 0.008f * TIME) * windowSizeHalved.y * 1.0f), 0.0f, 1.0f);
    float grille = 0.85f + 0.15f * clamp(1.5f * cos(3.14f * uv.x * windowSizeHalved.x * 1.0f), 0.0f, 1.0f);
    color *= scanline * grille * 1.2f;
    return color;
}

void fragment() {
//    COLOR.rgb = drawVignette(COLOR.rgb, UV);
    COLOR.rgb = drawScanlines(COLOR.rgb, UV);
    COLOR.rgb *= brightness;
}
