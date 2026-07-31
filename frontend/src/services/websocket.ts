import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import type { Message } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  connect() {
    const token = useAuthStore.getState().token;
    if (!token) return;

    this.ws = new WebSocket(`${WS_URL}/ws/chat?token=${token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectDelay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleMessage(data: any) {
    const store = useChatStore.getState();

    switch (data.type) {
      case 'message':
        const message: Message = {
          role: data.role,
          agent_name: data.agent_name,
          content: data.content,
          metadata: data.metadata,
        };
        store.addMessage(message);
        store.setIsTyping(false);
        break;

      case 'typing':
        store.setIsTyping(true);
        break;

      case 'credits_update':
        useAuthStore.getState().updateUser({ credits: data.credits });
        break;

      case 'error':
        store.addMessage({
          role: 'system',
          content: data.content,
        });
        store.setIsTyping(false);
        break;
    }
  }

  send(content: string, agentType: string | null = null, conversationId?: number) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'message',
        content,
        agent_type: agentType,
        conversation_id: conversationId,
      }));

      // Add user message immediately
      useChatStore.getState().addMessage({
        role: 'user',
        content,
      });
    }
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}

export const chatWS = new ChatWebSocket();
