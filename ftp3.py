#! python3
from mypackage import handy
from netpack import ftpfuncs
import getpass, ftplib, os

sep = '/'
cmd_list = ('dir','srcdir','cwd','stor','update','srcdir','mkd','retr')
download_dir = 'C:\\Users\\Dynamo\\Downloads\\ftp\\'

loginCred = {}

def getLoginCred(loginCred):
    loginCred['proxy'] = input('Proxy server: ')
    if handy.testQuit(loginCred['proxy']):
        raise KeyboardInterrupt
    loginCred['host'] = input('ftp host: ')
    if handy.testQuit(loginCred['host']):
        raise KeyboardInterrupt
    loginCred['user'] = input('ftp user: ')
    if handy.testQuit(loginCred['user']):
        raise KeyboardInterrupt
    loginCred['pwd'] = getpass.getpass('Enter your password: ')
    if handy.testQuit(loginCred['pwd']):
        raise KeyboardInterrupt

def main():
    while True:
        try:
            global loginCred
            getLoginCred(loginCred)
            if loginCred['proxy']:
                loginCred['host'] = loginCred['proxy']
            print("Connecting...")
            with ftplib.FTP(loginCred['host'],loginCred['user'],loginCred['pwd']) as ftp:
                print('Connected to host: {}\r\nuser: {}'.format(loginCred['host'],loginCred['user']))
                break
        except ftplib.error_perm as e:
            print(e)
            continue
        except KeyboardInterrupt:
            print('Quiting script')
            return
        except Exception as e:
            print('{}: {}'.format(type(e), e))
    dir_stack = []
    srcdir = ''
    while True:
        try:
            global sep
            data = []
            typed = input('Enter command: ')
            if handy.testQuit(typed):
                return
            tokens = typed.split()
            if len(tokens) == 1:
                if cmd_list[0] in tokens[0].lower():# dir (Show contents of current dir)
                    with ftplib.FTP( loginCred['host'], loginCred['user'], loginCred['pwd']) as ftp:
                        ftp.cwd('{}'.format(sep.join(dir_stack)))
                        ftp.dir(data.append)
                    print('./{}'.format(sep.join(dir_stack)))
                    for line in data:
                        print(line)
            elif len(tokens) == 2:
                if cmd_list[2] in tokens[0].lower(): # cwd change working directory
                    with ftplib.FTP( loginCred['host'], loginCred['user'], loginCred['pwd']) as ftp:
                        if '..' in tokens[1]:
                            dir_stack.pop()
                            currdir = sep.join(dir_stack) 
                            ftp.cwd('{}/{}'.format(currdir,tokens[1]))
                        elif '.' in tokens[1]:
                            dir_stack.clear()
                            ftp.cwd('.')
                        else:
                            currdir = sep.join(dir_stack) 
                            ftp.cwd('{}/{}'.format(currdir,tokens[1]))
                            dir_stack.append(tokens[1])
        except KeyboardInterrupt:
            print('Quiting script')
            break
        except ftplib.error_perm as e:
            print('{}: {}'.format(type(e), e))
        except Exception as e:
            print('{}: {}'.format(type(e), e))

if __name__ == "__main__":
    main()
