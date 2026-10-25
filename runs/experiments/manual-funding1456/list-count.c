/* Read-only LB_GETCOUNT for the visible original provider list. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
static BOOL CALLBACK child(HWND h, LPARAM unused) {
 char cls[128]="";GetClassNameA(h,cls,sizeof(cls));
 if(!strcmp(cls,"TListBox"))printf("%ld\n",(long)SendMessage(h,LB_GETCOUNT,0,0));
 return TRUE;
}
static BOOL CALLBACK top(HWND h, LPARAM title) {
 char text[512]="";GetWindowTextA(h,text,sizeof(text));
 if(IsWindowVisible(h)&&!strcmp(text,(char*)title)){EnumChildWindows(h,child,0);return FALSE;}
 return TRUE;
}
int main(int argc,char **argv){if(argc!=2)return 2;EnumWindows(top,(LPARAM)argv[1]);return 0;}
