/* Post WM_SYSCOMMAND/SC_CLOSE (what a click on a window's X button makes the window receive) to the visible top-level window whose title starts with
 * the given prefix and is wider than 100 px (the game's main form). Prints the window handle and the title; exit 1 if none.
 *   i686-w64-mingw32-gcc -O2 -o ~/ic2-work/win_close.exe win_close.c ; wine win_close.exe "Imperial Conquest 2"
 * Why: Xvfb runs without a window manager, so there is no X button to click (rule 6: the substitute is recorded, not hidden). */
#include <windows.h>
#include <stdio.h>
#include <string.h>
struct find { const char *prefix; HWND found; char title[256]; };
static BOOL CALLBACK pick(HWND h, LPARAM lp)
{
    struct find *f = (struct find *)lp; char txt[256] = ""; RECT r;
    if (!IsWindowVisible(h)) return TRUE;
    GetWindowTextA(h, txt, sizeof txt); GetWindowRect(h, &r);
    if (strncmp(txt, f->prefix, strlen(f->prefix)) == 0 && (r.right - r.left) > 100) { f->found = h; strcpy(f->title, txt); return FALSE; }
    return TRUE;
}
int main(int argc, char **argv)
{
    struct find f;
    if (argc < 2) return 2;
    f.prefix = argv[1]; f.found = NULL; f.title[0] = 0;
    EnumWindows(pick, (LPARAM)&f);
    if (!f.found) { fprintf(stderr, "no such window: %s\n", argv[1]); return 1; }
    PostMessageA(f.found, WM_SYSCOMMAND, SC_CLOSE, 0);
    printf("posted WM_SYSCOMMAND SC_CLOSE to %p: %s\n", (void *)f.found, f.title);
    return 0;
}
