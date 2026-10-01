/* Enumerate a window's controls and print one per line:
 *
 *     <class> TAB <text> TAB <x> TAB <y> TAB <width> TAB <height>
 *
 * x, y are screen coordinates (GetWindowRect). Wine draws a dialog's controls
 * itself and does not make them X windows, and their positions depend on the
 * font and DPI, so the order driver reads them from the running game instead of
 * hardcoding them. Build with the 32-bit mingw compiler for the win32 prefix:
 *
 *     i686-w64-mingw32-gcc -O2 -o win_controls.exe win_controls.c
 *     wine win_controls.exe "Army recruits"
 */
#include <windows.h>
#include <stdio.h>

static BOOL CALLBACK dump(HWND h, LPARAM lp)
{
    char cls[128] = "", txt[512] = "";
    RECT r;
    GetClassNameA(h, cls, sizeof cls);
    GetWindowTextA(h, txt, sizeof txt);
    if (GetWindowRect(h, &r))
        printf("%s\t%s\t%ld\t%ld\t%ld\t%ld\n", cls, txt,
               (long)r.left, (long)r.top, (long)(r.right - r.left), (long)(r.bottom - r.top));
    return TRUE;
}

int main(int argc, char **argv)
{
    HWND h;
    if (argc < 2) {
        fprintf(stderr, "usage: win_controls <window-title>\n");
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
