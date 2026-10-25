/* Read-only window/control inspection; no command messages or state changes. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
static BOOL CALLBACK child(HWND h, LPARAM unused) {
    char cls[128] = "", text[512] = ""; RECT r;
    GetClassNameA(h, cls, sizeof(cls)); GetWindowTextA(h, text, sizeof(text));
    GetWindowRect(h, &r);
    printf("%s\t%s\t%ld\t%ld\t%ld\t%ld\t%d\t%d", cls,text,
        r.left,r.top,r.right-r.left,r.bottom-r.top,IsWindowEnabled(h),IsWindowVisible(h));
    if (!strcmp(cls,"TListBox")) {
        POINT o={0,0};ClientToScreen(h,&o);
        printf("\t%ld\t%ld\t%ld\t%ld\t%ld",(long)SendMessage(h,LB_GETCOUNT,0,0),
            (long)SendMessage(h,LB_GETITEMHEIGHT,0,0),(long)SendMessage(h,LB_GETTOPINDEX,0,0),o.x,o.y);
    }
    printf("\n");
    return TRUE;
}
struct search { const char *title; HWND found; };
static BOOL CALLBACK top(HWND h, LPARAM p) {
    struct search *s=(struct search*)p; char text[512]="";
    GetWindowTextA(h,text,sizeof(text));
    if (IsWindowVisible(h) && !strcmp(text,s->title)) {s->found=h;return FALSE;}
    return TRUE;
}
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    struct search s={argv[1],NULL}; EnumWindows(top,(LPARAM)&s);
    if(!s.found)return 1;
    EnumChildWindows(s.found,child,0);return 0;
}
