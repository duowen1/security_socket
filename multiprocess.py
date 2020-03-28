#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import ssl
import os
from multiprocessing import Process,Lock
import time
import datetime
import json
import struct
import random
import threading

##用户下载线程
def downloadthread(filename):
    with open(filename,'rb') as f:
        data=f.read()
    client_socket.sendall(data)

##用户上传线程
##这个多线程实现的没什么意义
def upthread(fileI):
    print("start upload")
    filesize=fileI[1]
    print(filesize)
    recv_len=0
    with open(fileI[0],"wb") as f:
        while recv_len<filesize:
            if (filesize-recv_len)>1024:
                recv_mesg=client_socket.recv(1024)
                f.write(recv_mesg)
                recv_len+=len(recv_mesg)
                print(recv_len/filesize)
            else:
                recv_mesg=client_socket.recv(filesize-recv_len)
                recv_len+=len(recv_mesg)
                f.write(recv_mesg)
    print("uploadfinish")



def talk(client_socket):
    with open('/home/ubuntu/users.txt','r') as f:
        data=f.read()

    userlist=json.loads(data)
    while True:
        data=client_socket.recv(1024).decode('utf-8')
        function_char=data[0]
        head=data[1:]
        #如果是登录命令
        if function_char=='L':
            userinfo=json.loads(head)
            #验证用户名密码是否正确
            if (userinfo['username'] not in userlist) or (userinfo['password'] !=userlist[userinfo['username']]):
                #密码错误，返回错误码0
                answer_value='F'
                client_socket.send(answer_value.encode('utf-8'))
            else:
                #密码正确，返回正确码+cookie+文件列表
                #cookie由时间戳+随机数+用户名组成
                answer_value='T'
                t=time.time()
                ran=random.randint(1000000000,9999999999)#十位数的随机数
                username=userinfo['username']
                cookie="%d%d%d%s"%(t,ran,len(username),username)
                cookielist.append(cookie)
                folderfile=[]
                for i in os.walk("/home/ubuntu/"+username):
                    folderfile+=i[2]
                file_nums=len(folderfile)
                folderdic={'numoffile':file_nums,'filelist':folderfile}
                back=answer_value+cookie+json.dumps(folderdic,ensure_ascii=False)
                client_socket.send(back.encode('utf-8'))    
                            
        #如果是上传文件命令
        elif function_char=='U':
            fileinfo=json.loads(head)
            print(fileinfo)
            ##cookie验证正确
            if checkcookie(fileinfo['cookie']):
                username=getusernamefromcookie(fileinfo['cookie'])
                filename=fileinfo['filename']
                filesize=fileinfo['filesize']

                fileI=["/home/ubuntu/"+username+"/"+filename,filesize]

                th_uploading=threading.Thread(target=upthread,args=(fileI,))
                th_uploading.start()
                th_uploading.join()

                t=int(time.time())
                log='%d '%t+username+' new '+filename+'\n'
                lock.acquire()
                with open('/home/ubuntu/log','a') as f:
                    f.write(log)
                lock.release()
                               
            else:
                answer_value=struct.pack("B",0)
                client_socket.send(answer_value)
        #如果是删除文件命令        
        elif function_char=='D':
            fileinfo=json.loads(head)
            if checkcookie(fileinfo['cookie']):
                username=getusernamefromcookie(fileinfo['cookie'])
                filename=fileinfo['filename']
                filepath="/home/ubuntu/"+username+"/"+filename
                os.remove(filepath)

                t=int(time.time())
                log='%d '%t+username+' delete '+filename+'\n'
                lock.acquire()
                with open('/home/ubuntu/log','a') as f:
                    f.write(log)
                lock.release()

            else:
                pass
        #如果是注册用户
        elif function_char=='S':
            userinfo=json.loads(head)
            if userinfo['username'] in userlist:
                #用户名已存在
                result='F'
                client_socket.send(result.encode('utf-8'))
            else:
                #用户名不存在
                userlist[userinfo['username']]=userinfo['password']
                os.mkdir("/home/ubuntu/"+userinfo['username'])
                writetofile=json.dumps(userlist)
                with open("/home/ubuntu/users.txt","w") as f:
                    f.write(writetofile)
                result='T'
                client_socket.send(result.encode('utf-8'))

        #如果是下载文件
        elif function_char=='X':
            fileinfo=json.loads(head)
            if checkcookie(fileinfo['cookie']):
                username=getusernamefromcookie(fileinfo['cookie'])
                filename='/home/ubuntu/'+username+'/'+fileinfo['filename']
                fileinfo=os.stat(filename)
                dic={'filesize':fileinfo.st_size}
                tosend='T'+json.dumps(dic)
                client_socket.send(tosend.encode('utf-8'))
                th_download=threading.Thread(target=downloadthread,args=(filename,))
                th_download.start()


                t=int(time.time())
                log='%d '%t+username+' download '+filename+'\n'
                lock.acquire()
                with open('/home/ubuntu/log','a') as f:
                    f.write(log)
                lock.release()

            else:
                pass




def checkcookie(cookie):
    if cookie in cookielist:
        t=int(cookie[0:10])
        now=int(time.time())
        #时间戳已过期
        if (now-t)>int(1800):
            cookielist.remove(cookie)
            print("the cookie has expired")
            return False
        else:
            return True
    else:
        return False



def getusernamefromcookie(cookie):
    l=int(cookie[20])
    username=cookie[21:21+l]
    return username


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('/home/ubuntu/server.crt', '/home/ubuntu/server_rsa_private.pem.unsecure')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.bind(('0.0.0.0', 9443))
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            lock=Lock()
            while True:
                cookielist=[]
                client_socket, addr = ssock.accept()
                #服务器要部署在linux服务器上，在windows系统上没有fork函数，socket函数需要序列化
                p=Process(target=talk,args=(client_socket,))
                p.start()