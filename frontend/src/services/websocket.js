class CareCoordWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = {};
    this.reconnectDelay = 2000;
    this.reconnecting = false;
    this.shouldConnect = false;
  }

  connect(token) {
    this.shouldConnect = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    this._connect(wsUrl);
  }

  _connect(url) {
    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnecting = false;
        this._emit('connected', {});
      };
      this.ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          const eventType = msg.type || 'unknown';
          this._emit(eventType, msg.data || msg.payload || {});
          this._emit('*', msg);
        } catch {}
      };
      this.ws.onclose = () => {
        this._emit('disconnected', {});
        if (this.shouldConnect && !this.reconnecting) {
          this.reconnecting = true;
          setTimeout(() => this._connect(url), this.reconnectDelay);
        }
      };
      this.ws.onerror = () => {};
    } catch {}
  }

  disconnect() {
    this.shouldConnect = false;
    if (this.ws) { this.ws.close(); this.ws = null; }
  }

  on(eventType, cb) {
    if (!this.listeners[eventType]) this.listeners[eventType] = [];
    this.listeners[eventType].push(cb);
    return () => this.off(eventType, cb);
  }

  off(eventType, cb) {
    if (this.listeners[eventType])
      this.listeners[eventType] = this.listeners[eventType].filter(l => l !== cb);
  }

  _emit(eventType, data) {
    (this.listeners[eventType] || []).forEach(cb => { try { cb(data); } catch {} });
  }

  get isConnected() { return this.ws && this.ws.readyState === WebSocket.OPEN; }
}

export const wsClient = new CareCoordWebSocket();
