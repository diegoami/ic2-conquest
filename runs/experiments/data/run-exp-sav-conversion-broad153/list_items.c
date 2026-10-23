/* Read actual list captions. This never changes game state or writes memory. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int wanted_x;
static HWND selected;
static long selected_top;
static BOOL CALLBACK child(HWND h, LPARAM unused) {
  char cls[128]; RECT r;
  GetClassNameA(h,cls,sizeof(cls)); GetWindowRect(h,&r);
  if(strcmp(cls,"TListBox")!=0 || r.left!=wanted_x) return TRUE;
  if(!selected || r.top<selected_top){selected=h;selected_top=r.top;}
  return TRUE;
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
  selected=NULL;selected_top=0;
  EnumChildWindows(t.hwnd,child,0);if(!selected)return 3;
  LRESULT count=SendMessageA(selected,LB_GETCOUNT,0,0);
  fprintf(stderr,"selected list top=%ld count=%ld style=%lx\n",selected_top,(long)count,(unsigned long)GetWindowLongA(selected,GWL_STYLE));
  for(int i=0;i<count;i++) {
    char text[4096]={0};WCHAR wide[1024]={0};LRESULT length=SendMessageW(selected,LB_GETTEXTLEN,i,0);
    if(length>=0 && length<1024) {
      SendMessageW(selected,LB_GETTEXT,i,(LPARAM)wide);
      WideCharToMultiByte(CP_UTF8,0,wide,-1,text,sizeof(text),NULL,NULL);
      printf("%d\t%s\n",i,text);
    }
  }
  return 0;
}
