// SPDX-License-Identifier: GPL-2.0-only
//Copyright (C) 2023 Bardia Moshiri <fakeshell@bardia.tech>

#include <stdio.h>
#include <minui/minui.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

int main() {
    freopen("/dev/null", "w", stderr);

    if (gr_init(false) != 0) {
        printf("Failed to initialize minui\n");
        return -1;
    }

    int width = gr_fb_width();
    int height = gr_fb_height();

    printf("Display resolution: %dx%d\n", width, height);

    mkdir("/var/lib/droidian", 0755);
    mkdir("/var/lib/droidian/phosh-notch", 0755);

    FILE *width_file = fopen("/var/lib/droidian/phosh-notch/width", "w");
    if (width_file == NULL) {
        printf("Failed to open width file\n");
        return -1;
    }
    fprintf(width_file, "%d\n", width);
    fclose(width_file);

    FILE *height_file = fopen("/var/lib/droidian/phosh-notch/height", "w");
    if (height_file == NULL) {
        printf("Failed to open height file\n");
        return -1;
    }
    fprintf(height_file, "%d\n", height);
    fclose(height_file);

    gr_exit();

    return 0;
}
