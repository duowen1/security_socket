#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog

import socket
import ssl
import os
import json
import struct
import threading

##上传文件线程
def uploadfile(upfilename):
    with open(upfilename,'rb') as f:#需要使用非阻塞式，上传大文件会卡住  
        data=f.read()
        ssock.sendall(data)

##下载文件线程
def downloadthread(argu):
    recv_len=0
    filesize=argu[1]
    #接收文件
    with open("C:\\Users\\xsw\\Desktop\\"+argu[0],"wb") as f:
        while recv_len<filesize:
            if filesize-recv_len>1024:
                recv_mesg=ssock.recv(1024)
                f.write(recv_mesg)
                recv_len+=len(recv_mesg)
            else:
                recv_mesg=ssock.recv(filesize-recv_len)
                recv_len+=len(recv_mesg)
                f.write(recv_mesg)
        tkinter.messagebox.showinfo("提示",argu[0]+"下载完成")



context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations('D:\\vs_project\\ssl\\cert\\ca.crt')
sock=socket.create_connection(('49.232.53.79',9443))
ssock=context.wrap_socket(sock,server_hostname='SERVER')


#注册按钮事件
def sign_up():
    #点击注册
    def usr_login():
        newname=new_name.get()
        if len(newname)==0 or len(newname)>=10:
            tkinter.messagebox.showerror("错误","用户名长度不符合规定")
            return
        newpassword=new_pwd.get()
        newpasswordconfirm=new_pwd_confirm.get()
        print(newpassword)
        print(newpasswordconfirm)
        if newpassword != newpasswordconfirm:
            tkinter.messagebox.showerror("错误","口令与确认口令不一致")
            return
        userinfo={'username':newname,'password':newpassword}
        Tosend='S'+json.dumps(userinfo)
        ssock.send(Tosend.encode('utf-8'))
        result=ssock.recv(1024).decode('utf-8')
        if result[0]=='T':
            tkinter.messagebox.showinfo("注册","注册成功")
        else:
            tkinter.messagebox.showerror("错误","注册失败")
        

    window_sign_up=tk.Toplevel(window)
    window_sign_up.geometry("300x200")
    window_sign_up.title("注册")

    new_name=tk.StringVar()
    tk.Label(window_sign_up,text='用户名').place(x=10,y=10)
    entry_new_name=tk.Entry(window_sign_up,textvariable=new_name)
    entry_new_name.place(x=130,y=10)

    new_pwd=tk.StringVar()
    tk.Label(window_sign_up,text='口令').place(x=10,y=50)
    entry_usr_pwd=tk.Entry(window_sign_up,textvariable=new_pwd,show='*')
    entry_usr_pwd.place(x=130,y=50)

    new_pwd_confirm=tk.StringVar()
    tk.Label(window_sign_up,text='确认口令').place(x=10,y=90)
    entry_usr_pwd_confirm=tk.Entry(window_sign_up,textvariable=new_pwd_confirm,show='*')
    entry_usr_pwd_confirm.place(x=130,y=90)

    button_confirm_sign_up=tk.Button(window_sign_up,text='注册',command=usr_login)
    button_confirm_sign_up.place(x=80,y=120)


window = tk.Tk()

window.title("青团网盘")
window.geometry('1000x500')
window.configure(background='white')

photo=tk.PhotoImage(file='C:\\Users\\xsw\\Desktop\\banner.png')
imgLabel=tk.Label(window,image=photo)
imgLabel.pack()

QRCode=tk.PhotoImage(file='C:\\Users\\xsw\\Desktop\\qrcode.png')
qrlabel=tk.Label(window,image=QRCode)
qrlabel.place(x=100,y=150)

label_user=tk.Label(window,text='用户名')
label_pswd=tk.Label(window,text='口令')

label_user.place(x=510,y=170)
label_pswd.place(x=510,y=210)

var_usr_name=tk.StringVar()
entry_usr_name=tk.Entry(window,textvariable=var_usr_name)
entry_usr_name.place(x=620,y=175)

var_usr_pwd=tk.StringVar()
entry_usr_pwd=tk.Entry(window,textvariable=var_usr_pwd,show='*')
entry_usr_pwd.place(x=620,y=215)

#登陆按钮事件
def sign_on():
    username=var_usr_name.get()
    userpassword=var_usr_pwd.get()
    if (len(username)*len(userpassword))==0:
        tkinter.messagebox.showerror("错误","用户名或密码不能为空")
        return

    userinfo={'username':username,'password':userpassword,}
    info='L'+json.dumps(userinfo)

    ssock.send(info.encode('utf-8'))
    

    result=ssock.recv(1024).decode('utf-8')
    
    if result[0]=='F':
        tkinter.messagebox.showerror("错误","用户名或者密码错误")
        return
    elif result[0]=='T':
        

        temp=result[1:]#去掉回复头
        print(temp)

        time=temp[0:10]
        print(time)
        rand=temp[10:20]
        print(rand)
        l=int(temp[20])
        print(l)
        username=temp[21:21+l]
        print(username)
        global cookie
        cookie=temp[0:21+l]
        fileinfodictstr=temp[21+l:]
        fileinfodict=json.loads(fileinfodictstr)
        print(fileinfodict)
        

        global window
        username=var_usr_name.get()
        window.destroy()
        title=username+'的网盘空间'
        file_process=tk.Tk()
        file_process.title(title)
        file_process.geometry('750x320')

        def openfile():
            filename=tk.filedialog.askopenfilename()
            var_file_path.set(filename)
        

        def upload():
            try:
                fileinfo=os.stat(var_file_path.get())
            except FileNotFoundError:
                tkinter.messagebox.showerror("错误","文件路径有误")
                return
            filesize=fileinfo.st_size
            filename=os.path.basename(var_file_path.get())
            fileinfodict={'cookie':cookie,'filename':filename,'filesize':filesize,}
            filestr=json.dumps(fileinfodict)

            Tosend='U'+filestr
            print (Tosend)
            ssock.send(Tosend.encode('utf-8'))

            upfilename=var_file_path.get()
            th=threading.Thread(target=uploadfile,args=(upfilename,),name='uploadthread')
            
            #with open(var_file_path.get(),'rb') as f:#需要使用非阻塞式，上传大文件会卡住  
                #data=f.read()
                #ssock.sendall(data)
            th.start()
            filelist.insert(tk.END,filename)
        
        def delete():
            i=filelist.curselection()
            filename=filelist.get(i)
            deletedict={'cookie':cookie,'filename':filename,}
            Tosend='D'+json.dumps(deletedict)
            ssock.send(Tosend.encode('utf-8'))
            filelist.delete(i)

        def download():
            i=filelist.curselection()
            filename=filelist.get(i)
            downdict={'cookie':cookie,'filename':filename,}
            Tosend='X'+json.dumps(downdict)
            ssock.send(Tosend.encode('utf-8'))

            back=ssock.recv(1024).decode('utf-8')
            if back[0]=='T':
                dic=json.loads(back[1:])
                filesize=dic['filesize']
                argu=[filename,filesize]
                th_download=threading.Thread(target=downloadthread,args=(argu,))
                th_download.start()

            else:
                tkinter.messagebox.showerror("错误","服务器拒绝了您的请求")
                os._exit(0)


        v=tk.StringVar()
        filelist=tk.Listbox(file_process,listvariable=v)
        v.set(tuple(fileinfodict['filelist']))
        filelist.place(x=20,y=80,width=700)
        
        button_open_file=tk.Button(file_process,text='请选择文件',command=openfile)
        button_open_file.place(x=550,y=20)

        file_label=tk.Label(file_process,text='已选择文件:')
        file_label.place(x=20,y=20)

        var_file_path=tk.StringVar()
        entry_file_path=tk.Entry(file_process,textvariable=var_file_path)
        entry_file_path.place(x=100,y=20,width=400)

        button_upload=tk.Button(file_process,text='上传',command=upload)
        button_upload.place(x=650,y=20)

        button_delete=tk.Button(file_process,text='删除',command=delete)
        button_delete.place(x=20,y=280)

        button_download=tk.Button(file_process,text='下载',command=download)
        button_download.place(x=80,y=280)

        file_process.mainloop()


button_sign_on = tk.Button(window, text='登录',command=sign_on,width=20,bg="DeepSkyBlue")
button_sign_up = tk.Button(window, text='注册',command=sign_up,width=20)

button_sign_on.place(x=620,y=240)
button_sign_up.place(x=620,y=280)

cookie=''

window.mainloop()