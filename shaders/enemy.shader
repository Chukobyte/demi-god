shader_type sprite;

uniform float flash_amount = 0.0f;
uniform float split_min = -1.0f;
uniform float split_max = -1.0f;

void fragment() {
    if (UV.y > split_min && UV.y < split_max) {
        COLOR.a = 0.0f;
    } else {
        vec3 flash_color = vec3(240.0f, 247.0f, 243.0f);
        COLOR.rgb = mix(COLOR.rgb, vec3(255.0f) / flash_color, flash_amount);
    }
}
