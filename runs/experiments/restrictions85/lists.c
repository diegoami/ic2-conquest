/* Read-only list/combo contents and selection. No state-changing messages. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
static BOOL CALLBACK child(HWND h,LPARAM ignored){
 char cls[128]="";RECT r;GetClassNameA(h,cls,128);GetWindowRect(h,&r);
 int combo=!strcmp(cls,"TComboBox");if(strcmp(cls,"TListBox")&&!combo)return TRUE;
 int n=SendMessage(h,combo?CB_GETCOUNT:LB_GETCOUNT,0,0),sel=SendMessage(h,combo?CB_GETCURSEL:LB_GETCURSEL,0,0);
 printf("LIST\t%ld\t%ld\t%d\t%d\t%s\n",r.left,r.top,n,sel,cls);
 for(int i=0;i<n;i++){char text[2048]="";SendMessage(h,combo?CB_GETLBTEXT:LB_GETTEXT,i,(LPARAM)text);printf("ROW\t%d\t",i);for(char*p=text;*p;p++)printf("%02x",(unsigned char)*p);puts("");}
 return TRUE;}
struct search{const char*title;HWND h;};
static BOOL CALLBACK top(HWND h,LPARAM p){struct search*s=(struct search*)p;char text[512]="";GetWindowTextA(h,text,512);if(IsWindowVisible(h)&&!strcmp(text,s->title)){s->h=h;return FALSE;}return TRUE;}
int main(int argc,char**argv){if(argc!=2)return 2;struct search s={argv[1],NULL};EnumWindows(top,(LPARAM)&s);if(!s.h)return 1;EnumChildWindows(s.h,child,0);return 0;}
