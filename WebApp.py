from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from queue import Queue
from threading import Thread,Event

from pubsub import pub as Publisher
from Controller import Controller

class Web:
    app = None
    socketio = None
    clients:list

    Msg = Queue()
    Exit = False

    ctrl:Controller = None
    ClientFullEvent = Event()
    ClientMaxNum = 4
    ClientNum = 0

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

        self.clients = []
        # start socketio background thread to update message to client
        self.socketio.start_background_task(target=self.WorkerTask)#, queue=self.Msg)

    def SetController(self, ctrl:Controller):
        self.ctrl = ctrl

    def Stop(self):
        self.Exit = True
        try:
            self.socketio.stop()
        except:
            print('End Web')

    def RunWebApp(self):
        # use_reloader=False, avoid app run twice
        self.socketio.run(self.app, port=80, debug=True, use_reloader=False)

    # controller send message to web app and pass to client ui
    # controller -> web app -> client ui
    def SendMessage(self, msg):
        print('web app received message:')
        print(msg)
        self.Msg.put(msg)

    def WorkerTask(self):
        while not self.Exit:
            if self.ctrl == None:
                continue

            # send message to client ui
            # current waiting number.
            if len(self.clients) <= self.ClientMaxNum and not self.ctrl.IsStart:
                num = self.ClientMaxNum-len(self.clients)
                if num != self.ClientNum:
                    join = {"join_game":{"state":"waiting","wait_num":num}}
                    self.socketio.emit('message', dict(data=join), namespace='/update')
                    self.ClientNum = num

            if len(self.clients) > 0 and self.Msg.qsize() > 0:
                talk = self.Msg.get()
                self.socketio.emit('message', dict(data=talk), namespace='/update') # broadcast=True

            if self.ClientFullEvent.is_set():
                self.ctrl.StartGame()
                self.ClientFullEvent.clear()

    #
    # route function
    #

    # @app.route('/')
    def index(self):
        print('index')
        return render_template('index.html')

    # @app.route('/desktop', methods=['GET', 'POST'])
    def desktop(self):
        if len(self.clients) >= self.ClientMaxNum:
            return render_template('index.html')

        # name = request.form.get('name')  # Access a specific field by its name attribute
        # avatar = request.form.get('avatar')
        name = request.values.get('name')
        avatar = request.values.get('avatar')
        print(f'received {name}, {avatar}')
        print('desktop')
        return render_template('desktop.html')

    #
    # socketio event function
    #

    # received client message
    # client ui -> web server -> controller
    # @socketio.on('message', namespace='/update')
    def OnMessage(self, json):
        print(f'received {request.sid} message: ' + str(json))

        Publisher.sendMessage('controller', msg=json)

    # @socketio.on('connect', namespace='/update')
    def OnConnect(self):
        if len(self.clients) < self.ClientMaxNum:
            self.clients.append(request.sid)
            print(f"Client {request.sid} on_connect.")

        if len(self.clients) >= self.ClientMaxNum and not self.ctrl.IsStart:
            self.ClientFullEvent.set()
            return

    # @socketio.on('disconnect', namespace='/update')
    def OnDisconnect(self):
        self.clients.remove(request.sid)
        print(f"Client {request.sid} on_disconnected.")

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
    print("finish")