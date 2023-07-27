shader_type sprite;

uniform vec4 outline_color = vec4(1.0f, 1.0f, 1.0f, 1.0f);
uniform float outline_width = 0.0f;

vec4 getOutlineColor(vec4 currentColor, vec4 outlineColor, float outlineWidth, vec2 uv, sampler2D textureSampler, vec2 inTextureSize, vec4 textureDrawSource) {
    float PI = 3.14159265359f;
    int SAMPLES = 32;

    float outlineAlpha = 0.0f;
    float angle = 0.0f;
    for (int i = 0; i < SAMPLES; i++) {
        angle += 1.0f / (float(SAMPLES) / 2.0f) * PI;
        vec2 testPoint = vec2((outlineWidth / inTextureSize.x) * cos(angle), (outlineWidth / inTextureSize.y) * sin(angle));
		testPoint = clamp(UV + testPoint, textureDrawSource.xy, textureDrawSource.zw);
		float sampledAlpha = texture(textureSampler,  testPoint).a;
		outlineAlpha = max(outlineAlpha, sampledAlpha);
    }
    vec4 outColor = mix(vec4(0.0), outlineColor, outlineAlpha);
	outColor = mix(outColor, currentColor, currentColor.a);

    return outColor;
}

void fragment() {
    vec4 textureDrawSource = vec4(0.0f, 0.0f, TEXTURE_SIZE.x, TEXTURE_SIZE.y);
    COLOR = getOutlineColor(COLOR, outline_color, outline_width, UV, TEXTURE, TEXTURE_SIZE, textureDrawSource);
}
