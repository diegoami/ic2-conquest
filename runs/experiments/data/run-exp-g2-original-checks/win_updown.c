/* Print every up-down (spin) control of a window: class, x, y, w, h, range min, range max, position, from UDM_GETRANGE / UDM_GETPOS.
 *   i686-w64-mingw32-gcc -O2 -o win_updown.exe win_updown.c ; wine win_updown.exe "Split unit"
 * (rule 6: the dialog's real spinner range is asked of the control, not inferred from key presses). */
#include <windows.h>
#include <stdio.h>
#include <string.h>
static BOOL CALLBACK dump(HWND h, LPARAM lp)
{
    char cls[128] = ""; RECT r;
    GetClassNameA(h, cls, sizeof cls);
    if (strstr(cls, "UpDown") || strstr(cls, "updown")) {
        LRESULT rg = SendMessageA(h, WM_USER + 102, 0, 0);        /* UDM_GETRANGE: LOWORD max, HIWORD min */
        LRESULT ps = SendMessageA(h, WM_USER + 104, 0, 0);        /* UDM_GETPOS: LOWORD pos, HIWORD error */
        GetWindowRect(h, &r);
        printf("%s\t%ld\t%ld\t%ld\t%ld\tmin=%d\tmax=%d\tpos=%d\terr=%d\n", cls, (long)r.left, (long)r.top, (long)(r.right - r.left), (long)(r.bottom - r.top),
               (short)HIWORD(rg), (short)LOWORD(rg), (short)LOWORD(ps), (int)HIWORD(ps));
    }
    return TRUE;
}
struct find { const char *title; HWND found; };
static BOOL CALLBACK pick(HWND h, LPARAM lp)
{
    struct find *f = (struct find *)lp; char txt[512] = "";
    if (!IsWindowVisible(h)) return TRUE;
    GetWindowTextA(h, txt, sizeof txt);
    if (strcmp(txt, f->title) == 0) { f->found = h; return FALSE; }
    return TRUE;
}
int main(int argc, char **argv)
{
    struct find f;
    if (argc < 2) return 2;
    f.title = argv[1]; f.found = NULL;
    EnumWindows(pick, (LPARAM)&f);
    if (!f.found) { fprintf(stderr, "visible window not found: %s\n", argv[1]); return 1; }
    EnumChildWindows(f.found, dump, 0);
    return 0;
}
