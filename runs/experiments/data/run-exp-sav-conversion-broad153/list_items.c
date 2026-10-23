/* Read actual list captions. This never changes game state or writes memory. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int wanted_x;
static BOOL CALLBACK child(HWND h, LPARAM unused) {
  char cls[128]; RECT r;
  GetClassNameA(h,cls,sizeof(cls)); GetWindowRect(h,&r);
  if(!strstr(cls,"ListBox") || r.left!=wanted_x) return TRUE;
  LRESULT count=SendMessageA(h,LB_GETCOUNT,0,0);
  for(int i=0;i<count;i++) {
    char text[1024]={0};
    if(SendMessageA(h,LB_GETTEXTLEN,i,0)<sizeof(text)) {
      SendMessageA(h,LB_GETTEXT,i,(LPARAM)text);
      printf("%d\t%s\n",i,text);
    }
  }
  return FALSE;
}
struct target {const char *title; HWND hwnd;};
static BOOL CALLBACK top(HWND h,LPARAM value) {
  struct target *t=(struct target*)value; char text[512]={0};
  if(!IsWindowVisible(h))return TRUE;
  GetWindowTextA(h,text,sizeof(text));
  if(strcmp(text,t->title)==0){t->hwnd=h;return FALSE;}return TRUE;
}
int main(int argc,char **argv) {
  if(argc!=3)return 2;
  struct target t={argv[1],NULL};wanted_x=atoi(argv[2]);
  EnumWindows(top,(LPARAM)&t);if(!t.hwnd)return 1;
  EnumChildWindows(t.hwnd,child,0);return 0;
}
