/* Print the range of every trackbar in a window:
 *
 *     <class> TAB <min> TAB <max> TAB <pos> TAB <line size> TAB <page size>
 *
 * The values come from the control itself (TBM_GETRANGEMIN/MAX, GETPOS, GETLINESIZE, GETPAGESIZE), so a
 * slider's real range is measured, not assumed from the keys that move it.
 *
 *     i686-w64-mingw32-gcc -O2 -o win_slider.exe win_slider.c
 *     wine win_slider.exe "Change tax level"
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static BOOL CALLBACK dump(HWND h, LPARAM lp)
{
    char cls[128] = "";
    GetClassNameA(h, cls, sizeof cls);
    if (strstr(cls, "rackBar") || strstr(cls, "rackbar"))
        printf("%s\t%ld\t%ld\t%ld\t%ld\t%ld\n", cls,
               (long)SendMessageA(h, WM_USER + 1, 0, 0),    /* TBM_GETRANGEMIN */
               (long)SendMessageA(h, WM_USER + 2, 0, 0),    /* TBM_GETRANGEMAX */
               (long)SendMessageA(h, WM_USER + 0, 0, 0),    /* TBM_GETPOS */
               (long)SendMessageA(h, 0x0418, 0, 0),         /* TBM_GETLINESIZE */
               (long)SendMessageA(h, 0x0416, 0, 0));        /* TBM_GETPAGESIZE */
    return TRUE;
}

int main(int argc, char **argv)
{
    HWND h;
    if (argc < 2) {
        fprintf(stderr, "usage: win_slider <window-title>\n");
        return 2;
    }
    h = FindWindowA(NULL, argv[1]);
    if (!h) {
        fprintf(stderr, "window not found: %s\n", argv[1]);
        return 1;
    }
    EnumChildWindows(h, dump, 0);
    return 0;
}
