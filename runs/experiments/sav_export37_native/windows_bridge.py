"""HWND-specific original Windows UI bridge; all invocations retained exclusively."""
import argparse,base64,json,subprocess
from pathlib import Path
PS='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
CS=r'''
using System; using System.Collections.Generic; using System.Text; using System.Runtime.InteropServices;
public class Native {
 public delegate bool EnumProc(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb,IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h,EnumProc cb,IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,StringBuilder b,int c);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,StringBuilder b,int c);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetMenu(IntPtr h);
 [DllImport("user32.dll")] public static extern int GetMenuItemCount(IntPtr m);
 [DllImport("user32.dll")] public static extern IntPtr GetSubMenu(IntPtr m,int i);
 [DllImport("user32.dll")] public static extern uint GetMenuItemID(IntPtr m,int i);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetMenuString(IntPtr m,uint i,StringBuilder b,int c,uint f);
 [DllImport("user32.dll")] public static extern IntPtr PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,string l);
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern int GetScrollPos(IntPtr h,int bar);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
 [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(uint a,bool inherit,uint pid);
 [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr p,IntPtr at,byte[] b,int size,out IntPtr read);
 [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
 public struct Rect {public int Left,Top,Right,Bottom;}
 public static object Row(IntPtr h){uint pid;GetWindowThreadProcessId(h,out pid);var b=new StringBuilder(1024);GetWindowText(h,b,1024);var c=new StringBuilder(128);GetClassName(h,c,128);Rect r;GetWindowRect(h,out r);return new {handle=h.ToInt64(),pid=pid,cls=c.ToString(),text=b.ToString(),visible=IsWindowVisible(h),id=GetDlgCtrlID(h),left=r.Left,top=r.Top,width=r.Right-r.Left,height=r.Bottom-r.Top};}
 public static object[] Windows(uint pid,bool children){var list=new List<object>();EnumWindows((h,p)=>{uint found;GetWindowThreadProcessId(h,out found);if(found==pid){list.Add(Row(h));if(children)EnumChildWindows(h,(ch,cp)=>{list.Add(Row(ch));return true;},IntPtr.Zero);}return true;},IntPtr.Zero);return list.ToArray();}
 public static void Check(IntPtr h,uint pid){uint found;GetWindowThreadProcessId(h,out found);if(found!=pid)throw new Exception("HWND PID mismatch");}
 public static object[] Menus(IntPtr h){var list=new List<object>();Walk(GetMenu(h),"",list);return list.ToArray();}
 static void Walk(IntPtr menu,string path,List<object> list){if(menu==IntPtr.Zero)return;int n=GetMenuItemCount(menu);for(int i=0;i<n;i++){var b=new StringBuilder(256);GetMenuString(menu,(uint)i,b,256,0x400);string label=path+"/"+b.ToString();list.Add(new {path=label,id=GetMenuItemID(menu,i)});Walk(GetSubMenu(menu,i),label,list);}}
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--action',required=True,choices=['launch','enumerate','menu','command','text','click','capture','read','message','snapshot']);p.add_argument('--pid',type=int,default=0);p.add_argument('--hwnd',type=int,default=0);p.add_argument('--value',default='');p.add_argument('--address',type=lambda s:int(s,0));p.add_argument('--size',type=int,default=2);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 prefix="$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false); Add-Type -TypeDefinition @'\n"+CS+"\n'@;\n"
 quoted=lambda s:"'"+s.replace("'","''")+"'"
 if a.action=='launch':
  body="if (@(Get-Process | Where-Object {$_.ProcessName -like '*Conquest*'}).Count -ne 0) {throw 'Existing Conquest process; no launch'}; $p=Start-Process -FilePath 'C:\\Users\\diego\\Documents\\imp_conq_original\\Imperial Conquest 2.exe' -WorkingDirectory 'C:\\Users\\diego\\Documents\\imp_conq_original' -PassThru; @{pid=$p.Id} | ConvertTo-Json -Compress"
 else:
  assert a.pid>0
  body=f"$gamePid={a.pid}; $game=Get-Process -Id $gamePid; if ($game.Path -ne 'C:\\Users\\diego\\Documents\\imp_conq_original\\Imperial Conquest 2.exe') {{throw 'Wrong executable path'}}; $h=[IntPtr]{a.hwnd};\n"
  if a.action=='enumerate':body+='[Native]::Windows($gamePid,$true) | ConvertTo-Json -Depth 8 -Compress'
  elif a.action=='read':
   assert a.address is not None and a.address>0 and 0<a.size<=16
   body+=f"$p=[Native]::OpenProcess(0x410,$false,$gamePid); try {{$b=New-Object byte[] {a.size};$read=[IntPtr]::Zero;if(-not [Native]::ReadProcessMemory($p,[IntPtr]{a.address},$b,$b.Length,[ref]$read)){{throw 'RPM failed'}};@{{address={a.address};bytes=$b;read=$read.ToInt64()}}|ConvertTo-Json -Compress}} finally {{[void][Native]::CloseHandle($p)}}"
  elif a.action=='snapshot':
   body+=r'''
$p=[Native]::OpenProcess(0x410,$false,$gamePid);
function ReadBytes([long]$at,[int]$size){$b=New-Object byte[] $size;$got=[IntPtr]::Zero;if(-not [Native]::ReadProcessMemory($p,[IntPtr]$at,$b,$size,[ref]$got)){throw 'RPM failed'};return ,$b}
function W([long]$at){[BitConverter]::ToInt16((ReadBytes $at 2),0)}
function D([long]$at){[BitConverter]::ToUInt32((ReadBytes $at 4),0)}
try {$unit=D 0x45e740;$current=W 0x4a0320;$r=New-Object Native+Rect;[void][Native]::GetClientRect([IntPtr]1838558,[ref]$r);@{current=$current;selected_army=W 0x4a0328;selected_fleet=W 0x4a032a;selected_cell_x=W ($unit+0x21a);selected_cell_y=W ($unit+0x21c);unit_army=W ($unit+0x220);unit_fleet=W ($unit+0x224);tax=W (0x474670+$current*1172+0x44a);offer_source=W 0x49f008;offer_type=W 0x49f00a;armies=W 0x4a0324;fleets=W 0x4a0326;week=W 0x4a0330;year=W 0x4a0332;season=W 0x4a032e;viewport_x=W (0x474670+$current*1172+0x488);viewport_y=W (0x474670+$current*1172+0x486);client_width=$r.Right;client_height=$r.Bottom} | ConvertTo-Json -Compress}finally{[void][Native]::CloseHandle($p)}
'''
  else:
   body+='[Native]::Check($h,$gamePid);\n'
   if a.action=='menu':body+='[Native]::Menus($h)|ConvertTo-Json -Depth 6 -Compress'
   elif a.action=='command':body+=f"[void][Native]::PostMessage($h,0x111,[IntPtr]{int(a.value)},[IntPtr]::Zero); @{{posted=$true}}|ConvertTo-Json -Compress"
   elif a.action=='text':body+=f"[void][Native]::SendMessage($h,0xC,[IntPtr]::Zero,{quoted(a.value)}); @{{set=$true}}|ConvertTo-Json -Compress"
   elif a.action=='click':body+="[void][Native]::PostMessage($h,0xF5,[IntPtr]::Zero,[IntPtr]::Zero); @{posted=$true}|ConvertTo-Json -Compress"
   elif a.action=='message':
    msg,w,l=[int(x,0) for x in a.value.split(',')];assert msg in (0x10,0x201,0x202,0x100,0x101,0x133,0x400,0x401)
    body+=f"[void][Native]::PostMessage($h,{msg},[IntPtr]{w},[IntPtr]{l}); @{{posted=$true}}|ConvertTo-Json -Compress"
   elif a.action=='capture':
    assert a.value.replace(chr(92),'/').startswith('C:/Users/diego/Documents/ic2-tax-native/20261018T085043Z/')
    body+=f"Add-Type -AssemblyName System.Drawing;$file={quoted(a.value)};if(Test-Path -LiteralPath $file){{throw 'Existing capture'}};$r=New-Object Native+Rect;[void][Native]::GetWindowRect($h,[ref]$r);$b=New-Object Drawing.Bitmap ($r.Right-$r.Left),($r.Bottom-$r.Top);$g=[Drawing.Graphics]::FromImage($b);$dc=$g.GetHdc();try {{$ok=[Native]::PrintWindow($h,$dc,2)}}finally{{$g.ReleaseHdc($dc)}};$b.Save($file,[Drawing.Imaging.ImageFormat]::Png);$g.Dispose();$b.Dispose();@{{captured=$ok;path=$file}}|ConvertTo-Json -Compress"
 result=subprocess.run([PS,'-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode((prefix+body).encode('utf-16le')).decode()],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=40)
 if a.action=='enumerate' and result.returncode==0:
  rows=json.loads(result.stdout)
  if isinstance(rows,dict):rows=[rows]
  for row in rows:
   if row['cls']=='TPremierForm':row['text']='Imperial Conquest 2 [dynamic turn/commander caption redacted]'
  result.stdout=json.dumps(rows)
 record=dict(action=a.action,pid=a.pid,hwnd=a.hwnd,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
 with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps(record))
 if result.returncode:raise SystemExit(result.returncode)
if __name__=='__main__':main()
