import binascii
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, disconnect
from flask_cors import CORS
from queue import Queue
from threading import Thread,Event

from pubsub import pub as Publisher
from Controller import Controller, PrintLog

class Web:
    app = None
    socketio = None
    # key:client ID, value:{name:str, avatar:str, sid:str}
    clients:dict
 
    name = ""
    avatar = ""

    Msg = Queue()
    Exit = False

    ctrl:Controller = None
    ClientFullEvent = Event()
    ClientMaxNum = 4

    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)

        self.app.config['SECRET_KEY'] = 'SINBON'
        self.app.route('/')(self.index)
        self.app.route('/desktop', methods=['POST'])(self.desktop)

        self.socketio = SocketIO(self.app, async_mode='threading')
        self.socketio.on_event('connect', self.OnConnect, namespace='/update')
        self.socketio.on_event('disconnect', self.OnDisconnect, namespace='/update')
        self.socketio.on_event('message', self.OnMessage, namespace='/update')

        # internal communication
        # controller send message to web app and pass to client ui
        Publisher.subscribe(self.SendMessage, "webapp")

        self.clients = {}

        # start socketio background thread to update message to client
        self.socketio.start_background_task(target=self.WorkerTask)#, queue=self.Msg)

    def SetController(self, ctrl:Controller):
        self.ctrl = ctrl

    #
    # working thread function
    #

    def RunWebApp(self):
        # use_reloader=False, avoid app run twice
        self.socketio.run(self.app, port=80, debug=True, use_reloader=False)

    def WorkerTask(self):
        while not self.Exit:
            if self.ctrl == None or len(self.clients) == 0:
                continue

            # send message to client ui from controller
            if len(self.clients) > 0 and self.Msg.qsize() > 0:
                talk = self.Msg.get()
                self.socketio.emit('message', dict(data=talk), namespace='/update') # broadcast=True

            # client full and start game
            if self.ClientFullEvent.is_set():
                info = {}
                for key,val in self.clients.items():
                    info[key] = val['name']
                self.ctrl.StartGame(info)
                self.ClientFullEvent.clear()

    def Stop(self):
        self.Exit = True
        try:
            self.socketio.stop()
        except:
            PrintLog('End Web')

    #
    # message deliver function
    #

    # controller send message to web app and pass to client ui
    # controller -> web app -> client ui
    def SendMessage(self, msg):
        PrintLog('web app received message:')
        # print(msg)
        PrintLog(msg)
        self.Msg.put(msg)

    def ClientUpdate(self, data:dict, cid:int = 0):
        skip = []
        # notify connect client only
        if cid != 0:
            for key,val in self.clients.items():
                if key == cid:
                    continue
                skip.append(val['sid'])
        # else notify all
        self.socketio.emit('message', dict(data=data), namespace='/update', skip_sid=skip)

    #
    # tool function
    #

    def ClientId(self) -> int:
        val = self.name + ',' + self.avatar
        # convert name and avatar to client id
        cid = binascii.crc32(val.encode("UTF-8"))
        return cid

    #
    # route function
    #

    # @app.route('/')
    def index(self):
        # print('index')
        return render_template('index.html')

    # @app.route('/desktop', methods=['POST'])
    def desktop(self):
        if 'name' not in request.values or 'avatar' not in request.values:
            return render_template('index.html')

        self.name = request.values.get('name')
        self.avatar = request.values.get('avatar')
        # val = self.name + ',' + self.avatar
        # # convert name and avatar to client id
        # cid = binascii.crc32(val.encode("UTF-8"))

        cid = self.ClientId()
        if cid in self.clients:
            self.clients[cid]['sid'] = ''
        else:
            self.clients[cid] = {'name':self.name, 'avatar':self.avatar, 'sid':''}

        if len(self.clients) > self.ClientMaxNum:
            self.clients.pop(cid)
            # disconnect(request.sid, '/update')
            return render_template('index.html')

        PrintLog(f'received: {self.name}, {self.avatar}')

        return render_template('desktop.html')

    #
    # socketio event function
    #

    # received client message
    # client ui -> web server -> controller
    # @socketio.on('message', namespace='/update')
    def OnMessage(self, json):
        PrintLog(f'received {request.sid} message: ' + str(json))
        Publisher.sendMessage('controller', msg=json)

    # @socketio.on('connect', namespace='/update')
    def OnConnect(self):
        if len(self.clients) <= self.ClientMaxNum:
            PrintLog(f"Client {request.sid} on_connect.")

            # client new connect or reconnect
            if self.name != "" or self.avatar != "":
                cid = self.ClientId()
                seat = self.ctrl.Seat(self.name)
                data = {'info':{'name':self.name,'avatar':self.avatar, 'seat':seat, 'cid':cid}}
                # reconnect
                if cid in self.clients:
                    self.clients[cid]['sid'] = request.sid

                # 更新玩家資訊
                self.ClientUpdate(data, cid)
                # clear variable for next client
                self.name = ""
                self.avatar = ""

                # 更新等待人數
                num = self.ClientMaxNum - len(self.clients)
                state = "full" if num == 0 else "waiting"
                join = {"join_game":{"state":state,"wait_num":num}}
                self.ClientUpdate(join)

            # client reconnect in direct path
            else:
                # unknown state
                disconnect(request.sid, '/update')

        if len(self.clients) >= self.ClientMaxNum and not self.ctrl.IsStart:
            self.ClientFullEvent.set()

    # @socketio.on('disconnect', namespace='/update')
    def OnDisconnect(self):
        # sometime onconnect will be call before ondisconnect.
        PrintLog(f"Client {request.sid} on_disconnected.")

def StartWebApp():
    # run on the main thread only
    web = Web()
    ctrl = Controller()
    web.SetController(ctrl)

    webapp_thread = Thread(target=web.RunWebApp())
    webapp_thread.daemon = True
    webapp_thread.start()
    web.Stop()

if __name__ == '__main__':
    StartWebApp()
    PrintLog("finish")