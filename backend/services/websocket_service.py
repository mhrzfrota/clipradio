from flask_socketio import emit, join_room, leave_room
from app import socketio

@socketio.on('subscribe')
def handle_subscribe(data):
    """Cliente se inscreve em um canal"""
    channel = data.get('channel')
    if channel:
        join_room(channel)
        emit('subscribed', {'channel': channel}, room=channel)

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Cliente se desinscreve de um canal"""
    channel = data.get('channel')
    if channel:
        leave_room(channel)
        emit('unsubscribed', {'channel': channel}, room=channel)

def broadcast_update(channel, event_type, data):
    """Broadcast update to all clients in channel"""
    socketio.emit('update', {
        'type': event_type,
        'data': data
    }, room=channel)

