#! /usr/bin/env python3.4

from mypackage.handy import testQuit3, QuitException, mapFolder
import ftplib, os, getpass, os.path, re, json, time

class MyFTP():
    '''An FTP Manager Class'''
    def __init__(self, host = '', user = '', password = ''):
        '''MyFTP(host = '', user = '', password = '')'''
        self.set(host, user, password)
        self.local_dir = os.getcwd()
        self.remote_dir = '/'
        self.ftp = None
        self.localmap = {}
        self.remotemap = {}
    def set(self, host = '', user = '', password = ''):
        '''MyFTP.set(host = '', user = '', password = '')'''
        self.host = host
        self.user = user
        self.password = password
        self.message = None
    def action(self, instr=''):
        #initialize local and remote decorator function maps
        if not len(self.localmap):
            self.localmap = {'chdir':self.changeLocalDir, 'commands':self.showCmds, \
            'getcwd':self.getLocalDir, 'listdir':self.listLocalDir }
        if not len(self.remotemap):
            self.remotemap = {'mlsd':self.mlsd, 'cwd':self.changeRemoteDir, 'sendcmd':self.ftp.sendcmd, \
            'pwd':self.getRemoteDir, 'upfiles':self.upFiles, 'mkd':self.mkd, 'rmd':self.rmd, \
            'upfolder':self.upFolder }
        tokens = instr.split()
        if not len(tokens):
            return
        if tokens[0].lower() in self.localmap:
            if len(tokens) == 1:
                self.localmap[tokens[0]]()
            elif len(tokens) == 2:
                self.localmap[tokens[0]](tokens[1])
            elif len(tokens) > 2:
                self.localmap[tokens[0]](tokens[1:])
        elif tokens[0].lower() in self.remotemap:
            with ftplib.FTP(self.host, self.user, self.password) as self.ftp:
                self.ftp.cwd(self.remote_dir)
                if len(tokens) == 1:
                    self.remotemap[tokens[0]]()
                elif len(tokens) == 2:
                    self.remotemap[tokens[0]](tokens[1])
                elif len(tokens) > 2:
                    self.remotemap[tokens[0]](tokens[1:])
        else:
            print('Invalid command')
        print("Remote dir: {}".format(self.remote_dir))
        print("local dir: {}".format(os.getcwd()))
    def connect(self):
        with ftplib.FTP(self.host, self.user, self.password) as self.ftp:
            if not self.message:
                print('Connected to host: {} as user: {}'.format(self.host,self.user))
                self.message = self.ftp.getwelcome()
                print(self.message)
        print("Remote dir: {}".format(self.remote_dir))
        print("local dir: {}".format(os.getcwd()))
    def mlsd(self, instr=''):
        gen_resp = self.ftp.mlsd(instr, ["type", "size", "perm"])
        for name, f in gen_resp:
            #print("{} - {} {} {}".format(name, f['type'],f['sizd'],f['modify']))
            print("{} - {}".format(name, str(f)))
    def changeLocalDir(self, location):
        if not os.path.isdir(location):
            raise Exception('Invalid file folder location')
        else:
            os.chdir(location)
            self.local_dir = os.getcwd()
    def getLocalDir(self):
        print("local dir: {}".format(os.getcwd()))
    def changeRemoteDir(self, location):
        self.ftp.cwd(location)
        self.remote_dir = self.ftp.pwd()
    def getRemoteDir(self):
        self.remote_dir = self.ftp.pwd()
        print("Remote dir: {}".format(self.remote_dir))
    def showCmds(self):
        print("Local commands: "+', '.join([c for c in self.localmap.keys()]))
        print("Remote commands: "+', '.join([c for c in self.remotemap.keys()]))
    def listLocalDir(self):
        for f in os.listdir():
            print(f)
    def mkd(self, dirname):
        self.ftp.mkd(self.remote_dir+'/{}'.format(dirname))
    def rmd(self, dirpath):
        self.ftp.rmd(dirpath)
    def upDir(self, instr):
        p = self.ftp.pwd()
    def upFiles(self, file_list = [], local_dir = '.'):
        if isinstance(file_list, str):
            file_list = [file_list]
        if not len(file_list):
            return
        dir_files = os.listdir(local_dir)
        for item in file_list:
            try:
                if item in dir_files:
                    with open('.\\'+item,'rb') as f:
                        #self.ftp.storbinary('STOR '+item,f)
                        print("{} uploaded to server: {}".format(item, self.remote_dir))
            except Exception as e:
                print('{}: {}'.format(type(e), e))
    #this should be a generator so if it 
    def upFolder(self, path_list):
        '''Clones the contents of the local dir to a remote ftp dir\n
            upFolder([from_dir, to_dir, control_file])'''
        from_local = path_list[0]
        to_remote = path_list[1]
        if len(path_list) > 2:
            control_file = path_list[2]
        else:
            print("You didn't provide a Control file\r\nUsage: localdir, remotedir, controlfile")
            #print("")
            return
        if not os.path.isfile(control_file):
            drive = mapFolder(from_local)
            with open(control_file,'w') as f:
                json.dump([from_local,drive], f)
        loc_path_len = len(from_local)
        if not to_remote[-1] is '/':
            to_remote = to_remote+'/'
        after = []
        with open(control_file,'r') as f:
            drive = json.load(f)
            root = drive[0]
            driveList = drive[1]
        starttime = time.time()
        try:
            for i in driveList:
                for k, v in i.items():
                    if os.path.isdir(k):
                        if not v:
                            d = to_remote+'/'.join( k[len(root):].split('\\'))
                            i[k] = True
                            print('dir: {} created'.format(self.ftp.mkd(d)))
                            with open(control_file,'w') as f:
                                json.dump([root,driveList], f)
                        else:
                            d = to_remote+'/'.join( k[len(root):].split('\\'))
                            print("dir: {} previously created".format(d))
                    else:
                        if not v:
                            dtemp = os.path.split(k[len(root)+1:])[0]
                            d = to_remote+"/".join(dtemp.split("\\"))
                            if os.path.isfile(k):
                                with open(k,'rb') as upfile:
                                    self.ftp.cwd(d)
                                    self.ftp.storbinary('STOR '+os.path.split(k)[1], upfile)
                                    i[k] = True
                                    with open(control_file,'w') as f:
                                        json.dump([root,driveList], f)
                                    print("{} uploaded to {}".format(os.path.split(k)[1], d))
                        else:
                            print("{} previously uploaded".format(k))
            print("Upload successful")
            print("Total upload time: {} seconds".format(time.time()-starttime))
        except Exception as e:
            print(e)
        #finally:
        #    with open(control_file,'w') as f:
        #        json.dump([root,driveList], f)
        #^^^
        
    def delFiles(self, instr = []):
        gen = self.ftp.mlsd(self.remote_dir)
        

def main():
    while True:
        try:
            host = testQuit3('ftp host: ')
            user = testQuit3('username: ')
            password = getpass.getpass('Enter your password: ')
            myftp = MyFTP(host, user, password)
            myftp.connect()
            break
        except ftplib.error_perm as e:
            print('{}: {}'.format(type(e), e))
            continue
        except Exception as e:
            if isinstance(e, KeyboardInterrupt) or isinstance(e, QuitException):
                print('Quiting ftp_client4')
                exit()
            print('{}: {}'.format(type(e), e))
    #
    while True:
        try:
            cmd = testQuit3('>> ')
            myftp.action(cmd)
        
        except ftplib.error_perm as e:
            print('{}: {}'.format(type(e), e))
        except ftplib.error_perm as e:
            print('{}: {}'.format(type(e), e))
        except Exception as e:
            if isinstance(e, KeyboardInterrupt) or isinstance(e, QuitException):
                print('Quiting ftp_client4')
                exit()
            print('{}: {}'.format(type(e), e))

if __name__ == '__main__':
    main()
