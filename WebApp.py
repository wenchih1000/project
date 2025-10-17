from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from queue import Queue
from threading import Thread
import time

class Web:
    app = None
    socketio = None
    clients:list

    Msg = Queue()
    Exit = False

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'SINBON'
        self.app.route('/')(self.index)
        self.app.route('/desktop', methods=['GET', 'POST'])(self.desktop)

        self.socketio = SocketIO(self.app, async_mode='threading')
        self.socketio.on_event('connect', self.OnConnect, namespace='/update')
        self.socketio.on_event('disconnect', self.OnDisconnect, namespace='/update')
        self.socketio.on_event('message', self.OnMessage, namespace='/update')

        CORS(self.app)

        self.clients = []
        # start socketio background thread to update message to client
        self.socketio.start_background_task(target=self.WorkerTask)#, queue=self.Msg)

        self.MsgThread = Thread(target=self.PutMsg)
        self.MsgThread.start()

    def Stop(self):
        self.Exit = True
        try:
            self.socketio.stop()
        except:
            print('End Web')

    def RunWebApp(self):
        # use_reloader=False, avoid app run twice
        self.socketio.run(self.app, port=80, debug=True, use_reloader=False)

    def SendMsg(self, msg):
        self.Msg.put(msg)

    def PutMsg(self):

        while not self.Exit:
            cmd = {
                "join_game":{
                    "state":"waiting",
                    "wait_num":4 - len(self.clients)
                },
                "action_state":{
                    "player":"east",
                    "dice":True, "drawing":False, "discard":False,
                    "hu":False, "kong":False, "pong":False, "chow":False, "pass":False
                }
            }
            # print('PutMsg')
            self.Msg.put(cmd)
            time.sleep(2)
        print('End PutMsg')

    # send message to client
    def WorkerTask(self):    
        while not self.Exit:
            if len(self.clients) > 0 and self.Msg.qsize() > 0:

                talk = self.Msg.get()
                # talk = f"{str(self.clients)}:{data}"
                # broadcast=True
                self.socketio.emit('message', dict(data=talk), namespace='/update') 

    #
    # route function
    #

    # @app.route('/')
    def index(self):
        print('index')
        return render_template('index.html')

    # @app.route('/desktop', methods=['GET', 'POST'])
    def desktop(self):
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

    # @socketio.on('message', namespace='/update')
    def OnMessage(self, json):
        print(f'received {request.sid} message: ' + str(json))
        # emit('update message', str(json), broadcast=True)
        render_template('desktop.html')

    # @socketio.on('connect', namespace='/update')
    def OnConnect(self):
        self.clients.append(request.sid)
        print(f"Client {request.sid} on_connect.")

    # @socketio.on('disconnect', namespace='/update')
    def OnDisconnect(self):
        self.clients.remove(request.sid)
        print(f"Client {request.sid} on_disconnected.")

def StartWebApp():
    # run on the main thread only
    web = Web()
    webapp_thread = Thread(target=web.RunWebApp())
    webapp_thread.daemon = True
    webapp_thread.start()
    web.Stop()

if __name__ == '__main__':
    StartWebApp()
    print("finish")