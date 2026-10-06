/* Read-only state of a window's child controls (the leaders-form experiment; harness/win_controls.c is not edited).
 * one line per child: class TAB text(WM_GETTEXT) TAB x TAB y TAB w TAB h TAB enabled TAB visible TAB check(BM_GETCHECK or -) TAB limit(EM_GETLIMITTEXT or -) TAB selstart TAB selend TAB focus TAB style(hex)
 * Only visible top-level windows with the exact title are used (never a hidden window of the same title).
 *   i686-w64-mingw32-gcc -O2 -o win_state.exe win_state.c ; wine win_state.exe "Human and computer leaders" */
#include <windows.h>
#include <stdio.h>
#include <string.h>
static HWND focus_hwnd;
static BOOL CALLBACK dump(HWND h, LPARAM lp)
{
    char cls[128] = "", txt[1024] = "";
    RECT r; LRESULT chk = -1, lim = -1; DWORD s0 = 0, s1 = 0; int isbtn, isedit;
    GetClassNameA(h, cls, sizeof cls);
    SendMessageA(h, WM_GETTEXT, sizeof txt, (LPARAM)txt);
    isbtn = strstr(cls, "CheckBox") || strstr(cls, "RadioButton");
    isedit = strstr(cls, "Edit") != NULL;
    if (isbtn) chk = SendMessageA(h, BM_GETCHECK, 0, 0);
    if (isedit) { lim = SendMessageA(h, EM_GETLIMITTEXT, 0, 0); SendMessageA(h, EM_GETSEL, (WPARAM)&s0, (LPARAM)&s1); }
    if (GetWindowRect(h, &r))
        printf("%s\t%s\t%ld\t%ld\t%ld\t%ld\t%d\t%d\t%ld\t%ld\t%lu\t%lu\t%d\t%lx\n", cls, txt, (long)r.left, (long)r.top, (long)(r.right - r.left), (long)(r.bottom - r.top),
               IsWindowEnabled(h) ? 1 : 0, IsWindowVisible(h) ? 1 : 0, (long)chk, (long)lim, (unsigned long)s0, (unsigned long)s1, h == focus_hwnd ? 1 : 0, (unsigned long)GetWindowLongA(h, GWL_STYLE));
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
    struct find f; GUITHREADINFO gi;
    if (argc < 2) { fprintf(stderr, "usage: win_state <window-title>\n"); return 2; }
    f.title = argv[1]; f.found = NULL;
    EnumWindows(pick, (LPARAM)&f);
    if (!f.found) { fprintf(stderr, "visible window not found: %s\n", argv[1]); return 1; }
    memset(&gi, 0, sizeof gi); gi.cbSize = sizeof gi;
    GetGUIThreadInfo(GetWindowThreadProcessId(f.found, NULL), &gi);
    focus_hwnd = gi.hwndFocus;
    EnumChildWindows(f.found, dump, 0);
    return 0;
}
